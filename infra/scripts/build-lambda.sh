#!/usr/bin/env bash
#
# Build the Lambda deployment package for the StudySpot Django API.
#
# The package has to be built for the Lambda runtime rather than for this
# machine: psycopg ships compiled wheels, and the one that works on an Apple
# Silicon laptop is not the one that works on arm64 Linux. uv cross-resolves for
# the target platform instead of installing whatever matches the local
# interpreter, which is why this does not need Docker.
#
#     infra/scripts/build-lambda.sh
#
# Output: infra/build/studyspot-api.zip, which is what the Terraform variable
# lambda_package_path points at.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

BACKEND_DIR="${REPO_ROOT}/src/backend"
BUILD_DIR="${REPO_ROOT}/infra/build"
STAGE_DIR="${BUILD_DIR}/package"
ARCHIVE="${BUILD_DIR}/studyspot-api.zip"

# Must match the runtime and architectures in infra/terraform/api.tf.
PYTHON_VERSION="3.12"

# glibc 2.34 is what Amazon Linux 2023 ships, and the python3.12 Lambda runtime
# is built on it. Naming the real floor rather than the conventional
# `manylinux2014` matters: that alias means glibc 2.17, and psycopg-binary
# publishes no aarch64 wheel that old, so resolution fails outright. A higher
# floor is also strictly more permissive, since it still accepts wheels built
# against older glibc.
TARGET_PLATFORM="aarch64-manylinux_2_34"

for tool in uv zip; do
	if ! command -v "${tool}" >/dev/null 2>&1; then
		echo "error: ${tool} is required but not installed." >&2
		exit 1
	fi
done

echo "==> Cleaning ${BUILD_DIR}"
rm -rf "${BUILD_DIR}"
mkdir -p "${STAGE_DIR}"

# The lockfile stays the source of truth for versions, exactly as it does for
# Compose and CI. --frozen fails loudly if uv.lock and pyproject.toml disagree,
# which is better than shipping a package built from a different resolution than
# the one the tests ran against.
echo "==> Exporting locked runtime dependencies"
uv export \
	--project "${BACKEND_DIR}" \
	--frozen \
	--no-dev \
	--no-emit-project \
	--no-hashes \
	--format requirements-txt \
	--output-file "${BUILD_DIR}/requirements.txt"

echo "==> Installing dependencies for ${TARGET_PLATFORM}, Python ${PYTHON_VERSION}"
uv pip install \
	--target "${STAGE_DIR}" \
	--python-version "${PYTHON_VERSION}" \
	--python-platform "${TARGET_PLATFORM}" \
	--requirement "${BUILD_DIR}/requirements.txt" \
	--quiet

echo "==> Adding application code"
cp -R "${BACKEND_DIR}/studyspot" "${STAGE_DIR}/"
cp -R "${BACKEND_DIR}/spots" "${STAGE_DIR}/"
cp "${BACKEND_DIR}/handler.py" "${STAGE_DIR}/"
# Shipped so that `showmigrations` and anything else run through the management
# function behaves the same as it does locally.
cp "${BACKEND_DIR}/manage.py" "${STAGE_DIR}/"

# The management function reads the snapshot from inside the package. The Vercel
# build could never see data/spots.json because its service root is
# src/backend/, which is the gap docs/source/deployment.md warns about; bundling
# it here is what lets the AWS deployment actually populate its database.
echo "==> Adding the normalized dataset"
mkdir -p "${STAGE_DIR}/data"
cp "${REPO_ROOT}/data/spots.json" "${STAGE_DIR}/data/spots.json"

# Collected at build time because the function's filesystem is read-only. These
# are only served when DJANGO_ENABLE_ADMIN is on, but collecting them always
# means flipping that flag does not also require remembering this step.
#
# Uses the local environment rather than the cross-installed one: the staged
# wheels are arm64 Linux and will not run here.
echo "==> Collecting static files"
if ! DJANGO_DEBUG=true uv run --project "${BACKEND_DIR}" --directory "${BACKEND_DIR}" \
	python manage.py collectstatic --noinput --clear >/dev/null; then
	echo "error: collectstatic failed. Run 'uv sync --frozen' in src/backend/ first." >&2
	exit 1
fi
cp -R "${BACKEND_DIR}/staticfiles" "${STAGE_DIR}/staticfiles"

# Nothing in the package should be a compiled artifact of the build machine.
find "${STAGE_DIR}" -name '__pycache__' -type d -prune -exec rm -rf {} +
find "${STAGE_DIR}" -name '*.pyc' -delete

# Terraform redeploys the function whenever the archive's hash changes, so the
# archive must be byte-identical for identical inputs. Without a fixed mtime
# every build would produce a new hash and a pointless function update.
echo "==> Normalizing timestamps"
find "${STAGE_DIR}" -exec touch -t 200001010000.00 {} +

echo "==> Writing ${ARCHIVE}"
(cd "${STAGE_DIR}" && zip --quiet --recurse-paths -X "${ARCHIVE}" .)

SIZE="$(du -h "${ARCHIVE}" | cut -f1)"
echo "==> Built ${ARCHIVE} (${SIZE})"

# Lambda rejects a direct upload over 50 MB; past that the package has to go via
# S3. Warn before Terraform fails with a less obvious message.
BYTES="$(wc -c <"${ARCHIVE}" | tr -d ' ')"
if [ "${BYTES}" -gt 52428800 ]; then
	echo "warning: the package exceeds Lambda's 50 MB direct upload limit." >&2
	echo "         Publish it through S3, or trim the dependency set." >&2
fi
