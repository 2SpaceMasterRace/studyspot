"""Copy the normalized dataset into the serving database.

``data/spots.json`` is the source of truth; the ``spots`` table is a rebuildable
projection of it:

.. code-block:: shell

    just load-data

Every record is validated against the model before anything is written, so the
serving table can only ever hold records the API can serve. The whole load is
one transaction: a snapshot that fails validation halfway leaves the previous
contents in place rather than a half-replaced table.

On AWS this runs inside a Lambda function, because the database sits in a
private subnet and nothing outside the VPC can reach it. See
``handler.manage``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from spots.models import Borough, StudySpot

#: Written into the deployment package by infra/scripts/build-lambda.sh.
BUNDLED_DATASET = Path(settings.BASE_DIR) / "data" / "spots.json"

#: ``src/backend/spots/management/commands/load_spots.py`` -> repository root.
REPOSITORY_DATASET = Path(__file__).resolve().parents[5] / "data" / "spots.json"

CONTRACT_FIELDS = {
    "id",
    "name",
    "category",
    "address",
    "neighborhood",
    "borough",
    "latitude",
    "longitude",
    "university",
}

#: Written in batches so that a 2,000-row snapshot is a handful of statements
#: rather than one statement with 2,000 parameter groups.
BATCH_SIZE = 500


def default_dataset() -> Path:
    """The snapshot to load when none is named.

    Prefers the copy inside the deployment package, because on Lambda the
    repository layout above it does not exist.
    """
    return BUNDLED_DATASET if BUNDLED_DATASET.exists() else REPOSITORY_DATASET


def normalize_borough(value: Any) -> Any:
    """Accept any casing or internal spacing of a borough name.

    The importer writes canonical names, but the previous contract accepted
    ``brooklyn`` and ``  Staten   Island ``, and a snapshot produced by an older
    importer should still load.
    """
    if not isinstance(value, str):
        return value
    wanted = " ".join(value.split()).casefold()
    for borough in Borough.values:
        if borough.casefold() == wanted:
            return borough
    return value


def to_spot(record: Any, index: int) -> StudySpot:
    """Build a validated model instance from one snapshot record."""
    if not isinstance(record, dict):
        raise CommandError(f"Record {index} is not a JSON object.")

    unknown = sorted(set(record) - CONTRACT_FIELDS)
    if unknown:
        # The shared contract is what three consumers agree on. A field the
        # model does not know about means the importer and the API have drifted,
        # and silently dropping it would hide that.
        raise CommandError(
            f"Record {index} has fields outside the shared contract: {', '.join(unknown)}."
        )

    spot = StudySpot(
        id=record.get("id"),
        name=record.get("name"),
        category=record.get("category"),
        address=record.get("address"),
        neighborhood=record.get("neighborhood"),
        borough=normalize_borough(record.get("borough")),
        latitude=record.get("latitude"),
        longitude=record.get("longitude"),
        # Absent for every snapshot produced before the field existed.
        university=record.get("university"),
    )

    try:
        # validate_constraints is excluded: the CheckConstraints are enforced by
        # the database on write, and checking them here would issue a query per
        # row.
        spot.full_clean(validate_unique=False, validate_constraints=False)
    except ValidationError as error:
        raise CommandError(
            f"Record {index} ({record.get('id')!r}) is invalid: {error.messages}"
        ) from error

    return spot


class Command(BaseCommand):
    help = "Replace the spots table with the contents of a normalized snapshot."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dataset",
            type=Path,
            default=None,
            help="Normalized dataset to load. Defaults to the bundled snapshot.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dataset: Path = options["dataset"] or default_dataset()

        if not dataset.exists():
            raise CommandError(f"No dataset at {dataset}.")

        records = json.loads(dataset.read_text("utf-8"))
        if not isinstance(records, list):
            raise CommandError(f"{dataset} must contain a JSON array of study spots.")

        spots = [to_spot(record, index) for index, record in enumerate(records)]

        with transaction.atomic():
            # The table is a rebuildable projection, so a record dropped
            # upstream must disappear here too. That is why this replaces rather
            # than upserts.
            StudySpot.objects.all().delete()
            StudySpot.objects.bulk_create(spots, batch_size=BATCH_SIZE)

        written = StudySpot.objects.count()
        self.stdout.write(self.style.SUCCESS(f"loaded {written} spots from {dataset}"))
