"""Tests for the dataset loader.

``data/spots.json`` is the source of truth and the ``spots`` table is a
rebuildable projection of it, so what matters here is that the projection ends
up exactly matching the snapshot, including for records the snapshot drops.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from spots.models import StudySpot

from .test_spots_api import RECORDS

pytestmark = pytest.mark.django_db


def write_snapshot(tmp_path: Path, records: list[dict[str, Any]]) -> Path:
    path = tmp_path / "spots.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def load(path: Path) -> None:
    call_command("load_spots", dataset=path)


class TestLoading:
    def test_writes_every_record(self, tmp_path: Path) -> None:
        load(write_snapshot(tmp_path, RECORDS))
        assert StudySpot.objects.count() == len(RECORDS)

    def test_is_repeatable(self, tmp_path: Path) -> None:
        path = write_snapshot(tmp_path, RECORDS)
        load(path)
        load(path)
        assert StudySpot.objects.count() == len(RECORDS)

    def test_drops_records_removed_upstream(self, tmp_path: Path) -> None:
        # The table is a projection, so an upsert would wrongly keep rows the
        # importer no longer produces.
        load(write_snapshot(tmp_path, RECORDS))
        load(write_snapshot(tmp_path, RECORDS[:2]))
        assert StudySpot.objects.count() == 2
        assert not StudySpot.objects.filter(pk="dining:grumpy").exists()

    def test_an_empty_snapshot_empties_the_table(self, tmp_path: Path) -> None:
        load(write_snapshot(tmp_path, RECORDS))
        load(write_snapshot(tmp_path, []))
        assert StudySpot.objects.count() == 0

    def test_a_record_without_a_university_loads(self, tmp_path: Path) -> None:
        # Snapshots produced before the field existed omit it entirely.
        record = {key: value for key, value in RECORDS[0].items() if key != "university"}
        load(write_snapshot(tmp_path, [record]))
        assert StudySpot.objects.get(pk=record["id"]).university is None

    @pytest.mark.parametrize("borough", ["brooklyn", "BROOKLYN", "  Staten   Island "])
    def test_borough_casing_and_spacing_are_normalized(self, tmp_path: Path, borough: str) -> None:
        load(write_snapshot(tmp_path, [{**RECORDS[0], "borough": borough}]))
        assert StudySpot.objects.get(pk=RECORDS[0]["id"]).borough in {
            "Brooklyn",
            "Staten Island",
        }


class TestRejection:
    def test_a_missing_file_is_an_error(self, tmp_path: Path) -> None:
        with pytest.raises(CommandError, match="No dataset at"):
            load(tmp_path / "absent.json")

    def test_a_json_object_is_an_error(self, tmp_path: Path) -> None:
        path = tmp_path / "spots.json"
        path.write_text('{"id": "facdb:bobst"}', encoding="utf-8")
        with pytest.raises(CommandError, match="JSON array"):
            load(path)

    def test_a_field_outside_the_contract_is_an_error(self, tmp_path: Path) -> None:
        # A field the model does not know about means the importer and the API
        # have drifted; dropping it silently would hide that.
        record = {**RECORDS[0], "wifi": True}
        with pytest.raises(CommandError, match="outside the shared contract"):
            load(write_snapshot(tmp_path, [record]))

    def test_a_borough_outside_the_five_is_an_error(self, tmp_path: Path) -> None:
        with pytest.raises(CommandError, match="is invalid"):
            load(write_snapshot(tmp_path, [{**RECORDS[0], "borough": "Yonkers"}]))

    def test_an_out_of_range_latitude_is_an_error(self, tmp_path: Path) -> None:
        with pytest.raises(CommandError, match="is invalid"):
            load(write_snapshot(tmp_path, [{**RECORDS[0], "latitude": 91.0}]))

    def test_a_rejected_snapshot_leaves_the_table_untouched(self, tmp_path: Path) -> None:
        load(write_snapshot(tmp_path, RECORDS))
        with pytest.raises(CommandError):
            load(write_snapshot(tmp_path, [{**RECORDS[0], "borough": "Yonkers"}]))
        assert StudySpot.objects.count() == len(RECORDS)
