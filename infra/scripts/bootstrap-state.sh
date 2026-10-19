#!/usr/bin/env bash
#
# Create the S3 bucket that holds Terraform state.
#
# Run this once per AWS account, before a second person or CI applies this
# stack. It is deliberately not Terraform: the bucket that stores state cannot
# itself be tracked in the state it stores.
#
#     infra/scripts/bootstrap-state.sh [region]
#
# Afterwards, uncomment the backend block in infra/terraform/backend.tf with the
# printed bucket name and run `terraform init -migrate-state`.

set -euo pipefail

REGION="${1:-us-east-1}"

if ! command -v aws >/dev/null 2>&1; then
	echo "error: the AWS CLI is required but not installed." >&2
	exit 1
fi

if ! ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text 2>/dev/null)"; then
	echo "error: no working AWS credentials. Configure a profile first, for example:" >&2
	echo "         aws configure sso        # or" >&2
	echo "         aws configure" >&2
	exit 1
fi

BUCKET="studyspot-terraform-state-${ACCOUNT_ID}"

echo "==> Account ${ACCOUNT_ID}, region ${REGION}"

if aws s3api head-bucket --bucket "${BUCKET}" >/dev/null 2>&1; then
	echo "==> Bucket ${BUCKET} already exists; leaving it alone."
else
	echo "==> Creating ${BUCKET}"
	# us-east-1 is the one region that rejects a LocationConstraint.
	if [ "${REGION}" = "us-east-1" ]; then
		aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}"
	else
		aws s3api create-bucket \
			--bucket "${BUCKET}" \
			--region "${REGION}" \
			--create-bucket-configuration "LocationConstraint=${REGION}"
	fi
fi

# Versioning is what makes a corrupted or truncated state recoverable, and it is
# the one setting you cannot add usefully after the fact.
echo "==> Enabling versioning"
aws s3api put-bucket-versioning \
	--bucket "${BUCKET}" \
	--versioning-configuration Status=Enabled

echo "==> Enabling default encryption"
aws s3api put-bucket-encryption \
	--bucket "${BUCKET}" \
	--server-side-encryption-configuration \
	'{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":true}]}'

# State contains the generated database password in cleartext.
echo "==> Blocking all public access"
aws s3api put-public-access-block \
	--bucket "${BUCKET}" \
	--public-access-block-configuration \
	"BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "==> Requiring TLS for every request"
aws s3api put-bucket-policy \
	--bucket "${BUCKET}" \
	--policy "$(
		cat <<-POLICY
			{
			  "Version": "2012-10-17",
			  "Statement": [
			    {
			      "Sid": "DenyInsecureTransport",
			      "Effect": "Deny",
			      "Principal": "*",
			      "Action": "s3:*",
			      "Resource": [
			        "arn:aws:s3:::${BUCKET}",
			        "arn:aws:s3:::${BUCKET}/*"
			      ],
			      "Condition": { "Bool": { "aws:SecureTransport": "false" } }
			    }
			  ]
			}
		POLICY
	)"

cat <<EOF

==> Done.

Add this to infra/terraform/backend.tf, then run:

    terraform init -migrate-state

terraform {
  backend "s3" {
    bucket       = "${BUCKET}"
    key          = "staging/terraform.tfstate"
    region       = "${REGION}"
    encrypt      = true
    use_lockfile = true
  }
}
EOF
