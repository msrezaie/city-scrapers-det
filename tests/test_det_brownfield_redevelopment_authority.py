import json
from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import (
    ADVISORY_COMMITTEE,
    BOARD,
    COMMITTEE,
    FORUM,
    PASSED,
    TENTATIVE,
)
from city_scrapers_core.utils import file_response
from freezegun import freeze_time
from scrapy.settings import Settings

from city_scrapers.mixins.det_authority import JEFFERSON_LOCATION, TBD_LOCATION
from city_scrapers.spiders.det_brownfield_redevelopment_authority import (
    DetBrownfieldRedevelopmentAuthoritySpider,
)

with open(join(dirname(__file__), "files", "det_authority_events.json")) as f:
    test_events = json.load(f)["events"]
test_response = file_response(
    join(dirname(__file__), "files", "det_brownfield_redevelopment_authority.html"),
    url="https://www.degc.org/dbra",
)
spider = DetBrownfieldRedevelopmentAuthoritySpider()
spider.settings = Settings(values={"CITY_SCRAPERS_ARCHIVE": False})

with freeze_time("2026-09-27"):
    parsed_items = sorted(
        spider._parse_documents(
            test_response,
            events=[e for e in test_events if spider._is_agency_event(e)],
        ),
        key=lambda i: (i["start"], i["title"]),
    )

board_item = next(i for i in parsed_items if i["start"] == datetime(2026, 9, 23, 16))
cac_item = next(i for i in parsed_items if i["start"] == datetime(2026, 9, 23, 17))
hearing_item = next(i for i in parsed_items if i["start"] == datetime(2026, 9, 29, 17))
lbrf_item = next(i for i in parsed_items if i["start"] == datetime(2026, 6, 10, 15, 45))
council_hearing_item = next(
    i for i in parsed_items if i["start"] == datetime(2026, 7, 2)
)


def test_count():
    assert len(parsed_items) == 114


def test_title():
    assert board_item["title"] == "Board of Directors"
    assert cac_item["title"] == "Community Advisory Committee"
    assert lbrf_item["title"] == "Local Brownfield Revolving Fund Committee"
    assert (
        hearing_item["title"]
        == "Renaissance Center And Rivereast District Local Public Hearing"
    )
    assert (
        council_hearing_item["title"]
        == "Stockbridge Renaissance City Council Public Hearing"
    )


def test_description():
    assert board_item["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2025, 10, 2, 17)


def test_end():
    assert board_item["end"] is None


def test_id():
    assert (
        board_item["id"]
        == "det_brownfield_redevelopment_authority/202609231600/x/board_of_directors"
    )


def test_status():
    assert board_item["status"] == PASSED
    assert hearing_item["status"] == TENTATIVE


def test_location():
    assert board_item["location"] == JEFFERSON_LOCATION
    assert hearing_item["location"] == {
        "name": "Coleman A. Young Municipal Center",
        "address": "2 Woodward Ave, Detroit, MI 48226",
    }
    assert parsed_items[0]["location"] == {
        "name": "",
        "address": "2826 Bagley St, Detroit, MI 48216",
    }
    assert council_hearing_item["location"] == TBD_LOCATION


def test_source():
    assert (
        board_item["source"]
        == "https://www.degc.org/event-details/regular-dbra-board-meeting-2026-09-23-16-00"  # noqa
    )
    assert council_hearing_item["source"] == "https://www.degc.org/dbra"


def test_links():
    assert board_item["links"] == [
        {
            "href": "https://www.degc.org/_files/ugd/69e7f0_19b21bcae72c4df692ee6be5d46b01f8.pdf",  # noqa
            "title": "DBRA REGULAR BOARD MEETING NOTICE",
        },
        {
            "href": "https://www.degc.org/_files/ugd/69e7f0_58a6738bc8dd4411861642984e420191.pdf",  # noqa
            "title": "DBRA REGULAR BOARD MEETING AGENDA",
        },
    ]
    assert cac_item["links"] == [
        {
            "href": "https://www.degc.org/_files/ugd/69e7f0_f3925068cc7d4419a2887025c3a77790.pdf",  # noqa
            "title": "DBRA-CAC REGULAR MEETING NOTICE",
        },
        {
            "href": "https://www.degc.org/_files/ugd/69e7f0_cccf7234270c4398bc1dfa5b51c28b3a.pdf",  # noqa
            "title": "DBRA-CAC REGULAR MEETING AGENDA",
        },
        {
            "href": "https://us06web.zoom.us/j/85246162227?pwd=IMFbNa5dGgBHmFZtT03zmIMpOxXfRr.1",  # noqa
            "title": "Zoom",
        },
    ]
    # Documents matched to an event with a different title on the same day
    assert hearing_item["links"] == [
        {
            "href": "https://www.degc.org/_files/ugd/5bbdb1_4ad24a27cde84f5fbf0b9e78681304ea.pdf",  # noqa
            "title": "RENAISSANCE CENTER AND RIVEREAST DISTRICT LOCAL PUBLIC HEARING NOTICE",  # noqa
        }
    ]


def test_classification():
    assert board_item["classification"] == BOARD
    assert cac_item["classification"] == ADVISORY_COMMITTEE
    assert lbrf_item["classification"] == COMMITTEE
    assert hearing_item["classification"] == FORUM


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
