import json
from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import BOARD, CANCELLED, COMMITTEE, PASSED, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time
from scrapy.settings import Settings

from city_scrapers.mixins.det_authority import GUARDIAN_LOCATION, JEFFERSON_LOCATION
from city_scrapers.spiders.det_economic_development_corporation import (
    DetEconomicDevelopmentCorporationSpider,
)

with open(join(dirname(__file__), "files", "det_authority_events.json")) as f:
    test_events = json.load(f)["events"]
test_response = file_response(
    join(dirname(__file__), "files", "det_economic_development_corporation.html"),
    url="https://www.degc.org/edc",
)
spider = DetEconomicDevelopmentCorporationSpider()
spider.settings = Settings(values={"CITY_SCRAPERS_ARCHIVE": False})

with freeze_time("2026-09-27"):
    parsed_items = sorted(
        spider._parse_documents(
            test_response,
            events=[e for e in test_events if spider._is_agency_event(e)],
        ),
        key=lambda i: (i["start"], i["title"]),
    )

VIDEO_LINK = {
    "href": "https://www.youtube.com/channel/UCYOkOt8yzAfrbgxFSH7_WNA/videos",
    "title": "Video",
}
# Board meeting from the events API with matching documents
board_item = next(i for i in parsed_items if i["start"] == datetime(2026, 6, 23, 9))
# Committee meeting only listed in documents
committee_item = next(i for i in parsed_items if i["start"] == datetime(2026, 6, 23))
upcoming_item = next(i for i in parsed_items if i["start"] == datetime(2026, 10, 13, 9))


def test_count():
    assert len(parsed_items) == 55


def test_filters_other_agencies():
    assert all("DDA" not in link["title"] for i in parsed_items for link in i["links"])


def test_title():
    assert board_item["title"] == "Board of Directors"
    assert committee_item["title"] == "Finance Committee"
    assert {i["title"] for i in parsed_items} == {
        "Board of Directors",
        "Finance Committee",
        "City Council Public Hearing",
    }


def test_description():
    assert board_item["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2025, 10, 14, 9)
    assert parsed_items[-1]["start"] == datetime(2027, 6, 22, 9)


def test_end():
    assert board_item["end"] is None


def test_time_notes():
    assert board_item["time_notes"] == ""
    assert committee_item["time_notes"] == "See source to confirm meeting time"


def test_id():
    assert (
        board_item["id"]
        == "det_economic_development_corporation/202606230900/x/board_of_directors"
    )


def test_status():
    assert board_item["status"] == PASSED
    assert upcoming_item["status"] == TENTATIVE
    # Cancellation only noted in the document title, not the event
    cancelled_item = next(
        i for i in parsed_items if i["start"] == datetime(2026, 9, 22, 9)
    )
    assert cancelled_item["status"] == CANCELLED


def test_location():
    assert board_item["location"] == GUARDIAN_LOCATION
    assert committee_item["location"] == GUARDIAN_LOCATION
    assert upcoming_item["location"] == JEFFERSON_LOCATION


def test_source():
    assert (
        board_item["source"]
        == "https://www.degc.org/event-details/regular-edc-board-meeting-2026-06-23-09-00"  # noqa
    )
    assert committee_item["source"] == "https://www.degc.org/edc"


def test_links():
    assert board_item["links"] == [
        {
            "href": "https://www.degc.org/_files/ugd/69e7f0_ad7db032182a42a6939fb78128809061.pdf",  # noqa
            "title": "EDC BOARD MEETING MINUTES",
        },
        {
            "href": "https://www.degc.org/_files/ugd/69e7f0_84b8b74cccc146bfb59078805f483252.pdf",  # noqa
            "title": "EDC BOARD MEETING AGENDA",
        },
        {
            "href": "https://www.degc.org/_files/ugd/69e7f0_33bbd1eccb2c4720b0ad64bb5ea5a67b.pdf",  # noqa
            "title": "EDC BOARD MEETING NOTICE",
        },
        VIDEO_LINK,
    ]
    assert upcoming_item["links"] == [VIDEO_LINK]


def test_classification():
    assert board_item["classification"] == BOARD
    assert committee_item["classification"] == COMMITTEE


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False


@pytest.mark.parametrize("item", parsed_items)
def test_video_link(item):
    assert item["links"][-1] == VIDEO_LINK
