import json
from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import BOARD, PASSED, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time
from scrapy.settings import Settings

from city_scrapers.mixins.det_authority import GUARDIAN_LOCATION, JEFFERSON_LOCATION
from city_scrapers.spiders.det_next_michigan_development_corporation import (
    DetNextMichiganDevelopmentCorporationSpider,
)

with open(join(dirname(__file__), "files", "det_authority_events.json")) as f:
    test_events = json.load(f)["events"]
test_response = file_response(
    join(dirname(__file__), "files", "det_next_michigan_development_corporation.html"),
    url="https://www.degc.org/d-nmdc",
)
spider = DetNextMichiganDevelopmentCorporationSpider()
spider.settings = Settings(values={"CITY_SCRAPERS_ARCHIVE": False})

with freeze_time("2026-09-27"):
    parsed_items = sorted(
        spider._parse_documents(
            test_response,
            events=[e for e in test_events if spider._is_agency_event(e)],
        ),
        key=lambda i: (i["start"], i["title"]),
    )

# Meeting only listed in documents
doc_item = next(i for i in parsed_items if i["start"] == datetime(2026, 5, 12))
# Upcoming meeting from the events API
event_item = next(i for i in parsed_items if i["start"] == datetime(2026, 12, 8, 9, 25))


def test_count():
    assert len(parsed_items) == 9


def test_title():
    assert doc_item["title"] == "Special Board Meeting"
    assert event_item["title"] == "Board of Directors"


def test_description():
    assert event_item["description"] == ""


def test_end():
    assert event_item["end"] is None


def test_id():
    assert (
        event_item["id"]
        == "det_next_michigan_development_corporation/202612080925/x/board_of_directors"
    )


def test_status():
    assert doc_item["status"] == PASSED
    assert event_item["status"] == TENTATIVE


def test_location():
    assert doc_item["location"] == GUARDIAN_LOCATION
    assert event_item["location"] == JEFFERSON_LOCATION


def test_source():
    assert doc_item["source"] == "https://www.degc.org/d-nmdc"
    assert (
        event_item["source"]
        == "https://www.degc.org/event-details/dnmdc-board-meeting-2026-12-08-09-25"
    )


def test_links():
    assert doc_item["links"][0]["href"].startswith("https://www.degc.org/_files/")


def test_classification():
    assert doc_item["classification"] == BOARD
    assert event_item["classification"] == BOARD


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
