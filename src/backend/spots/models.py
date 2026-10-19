"""The shared study-spot contract, as a Django model.

One model serves the HTTP API, the dataset loader, and any future search
projection, so those cannot drift apart.

Nullability follows what NYC Open Data actually supplies rather than what would
be convenient. In the committed snapshots, ``address`` and ``neighborhood`` are
both genuinely absent for some records, so requiring them would reject real
rows. ``university`` is absent for every record the importer does not take from
a curated campus list, which is most of them.
"""

from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Upper

#: Page size defaults for ``GET /spots``, part of the published contract.
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

#: Filter values are trimmed, must not be blank, and are bounded.
MAX_FILTER_LENGTH = 120


class Borough(models.TextChoices):
    """The five New York City boroughs."""

    MANHATTAN = "Manhattan", "Manhattan"
    BROOKLYN = "Brooklyn", "Brooklyn"
    QUEENS = "Queens", "Queens"
    BRONX = "Bronx", "Bronx"
    STATEN_ISLAND = "Staten Island", "Staten Island"


class StudySpot(models.Model):
    """One study spot.

    ``category`` is a free string rather than an enumeration: the vocabulary
    belongs to the data importer, and pinning it here would force every category
    change through the shared contract and a migration.

    Case-insensitive filters go through Django's ``icontains`` and ``iexact``,
    which is why this table has no case-folded companion columns. The previous
    SQLite-backed version needed them because SQLite only folds ASCII; Postgres
    folds the whole of Unicode, provided every column involved uses the database
    collation. See the note on ``name`` below for what happens when one does not.

    One behavioural difference survives the change from the folded columns:
    Python's ``str.casefold()`` maps ``ß`` to ``ss`` and Postgres ``UPPER()``
    does not, so a search for "strasse" no longer matches "Straße". No record in
    the NYC snapshots is affected.
    """

    #: Identifiers are prefixed with their source dataset, as in
    #: ``facdb:eec118768e15a5e03d3354abda7b00da``.
    id = models.TextField(
        primary_key=True,
        help_text="Stable identifier, prefixed with its source dataset.",
    )

    # Neither of these columns declares a collation, and that is deliberate.
    #
    # An earlier version pinned both to "C" to make Meta.ordering byte-wise, on
    # the theory that the database's own locale could let two different names tie
    # in the sort key and so serve one row on two pages. That theory was wrong:
    # the ordering is (name, id) and `id` is a unique primary key, so the
    # tiebreaker already makes the sort total and deterministic under any
    # deterministic collation. Which collation is used only changes what order
    # the names come out in, not whether paging is stable.
    #
    # It was also actively harmful. Django compiles `icontains` and `iexact` to
    # UPPER(column) LIKE UPPER(%s), and UPPER() folds according to the collation
    # of its argument. A "C"-collated column folds ASCII only, while the bound
    # parameter folds under the database collation, so the two sides disagree on
    # every non-ASCII letter: UPPER('café') is 'CAFÉ' for the parameter but
    # 'CAFé' for the column, and `name__iexact='Café Grumpy'` could not match the
    # row it was copied from. NYC Open Data is full of accented names.
    #
    # Leaving both columns on the database collation makes the two sides fold
    # identically, which is what matters -- it is correct whether the cluster was
    # initialised with en_US.UTF-8 or with C.
    name = models.TextField()

    category = models.TextField()
    address = models.TextField(blank=True, null=True)
    neighborhood = models.TextField(
        blank=True,
        null=True,
        help_text="Neighborhood name, when the source supplies one.",
    )
    borough = models.TextField(choices=Borough.choices)

    latitude = models.FloatField(
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
    )
    longitude = models.FloatField(
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
    )

    university = models.TextField(
        blank=True,
        null=True,
        help_text=(
            "The institution this spot belongs to, for records the importer takes "
            "from a curated campus list. Never inferred: a spot with no curated "
            "affiliation leaves this absent."
        ),
    )

    class Meta:
        db_table = "spots"
        verbose_name = "study spot"
        verbose_name_plural = "study spots"

        #: Deterministic and total, so a row can never be repeated or skipped
        #: across pages.
        ordering = ["name", "id"]

        constraints = [
            # The field's `choices` are only enforced by full_clean(), which the
            # loader does not call on every row. The database should refuse a
            # sixth borough whatever wrote it.
            models.CheckConstraint(
                condition=models.Q(borough__in=Borough.values),
                name="spots_borough_known",
            ),
            models.CheckConstraint(
                condition=models.Q(latitude__gte=-90, latitude__lte=90),
                name="spots_latitude_range",
            ),
            models.CheckConstraint(
                condition=models.Q(longitude__gte=-180, longitude__lte=180),
                name="spots_longitude_range",
            ),
        ]

        indexes = [
            # Matches Meta.ordering, so paging is an index scan rather than a
            # sort of the whole table.
            models.Index(fields=["name", "id"], name="spots_order_idx"),
            # `iexact` compiles to UPPER(column) = UPPER(%s), so the index has to
            # be on the same expression to be usable.
            models.Index(Upper("neighborhood"), name="spots_neighborhood_idx"),
            models.Index(Upper("borough"), name="spots_borough_idx"),
            models.Index(Upper("university"), name="spots_university_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.borough})"
