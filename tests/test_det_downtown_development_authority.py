import json
from datetime import datetime
from os.path import dirname, join

import pytest
from city_scrapers_core.constants import BOARD, CANCELLED, COMMITTEE, PASSED, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time
from scrapy.settings import Settings

from city_scrapers.mixins.det_authority import JEFFERSON_LOCATION
from city_scrapers.spiders.det_downtown_development_authority import (
    DetDowntownDevelopmentAuthoritySpider,
)

with open(join(dirname(__file__), "files", "det_authority_events.json")) as f:
    test_events = json.load(f)["events"]
test_response = file_response(
    join(dirname(__file__), "files", "det_downtown_development_authority.html"),
    url="https://www.degc.org/dda",
)
spider = DetDowntownDevelopmentAuthoritySpider()
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
board_item = next(i for i in parsed_items if i["start"] == datetime(2026, 9, 23, 15))
committee_item = next(i for i in parsed_items if i["start"] == datetime(2026, 9, 28))


def test_count():
    assert len(parsed_items) == 46


def test_title():
    assert board_item["title"] == "Board of Directors"
    assert committee_item["title"] == "Finance Committee"
    assert "Tigers Ticket Donation Program Committee" in [
        i["title"] for i in parsed_items
    ]


def test_description():
    assert board_item["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2025, 10, 8, 15)


def test_end():
    assert board_item["end"] is None


def test_id():
    assert (
        board_item["id"]
        == "det_downtown_development_authority/202609231500/x/board_of_directors"
    )


def test_no_duplicate_events():
    """Edited recurring events are listed twice, once marked as canceled"""
    ids = [i["id"] for i in parsed_items]
    assert len(ids) == len(set(ids))
    # The copy of this event that isn't canceled on the site is used
    item = next(i for i in parsed_items if i["start"] == datetime(2026, 4, 22, 15))
    assert item["status"] == PASSED


def test_status():
    assert board_item["status"] == PASSED
    assert committee_item["status"] == TENTATIVE
    cancelled_item = next(
        i for i in parsed_items if i["start"] == datetime(2026, 9, 9, 15)
    )
    assert cancelled_item["status"] == CANCELLED


def test_location():
    assert board_item["location"] == JEFFERSON_LOCATION
    assert committee_item["location"] == JEFFERSON_LOCATION


def test_source():
    assert (
        board_item["source"]
        == "https://www.degc.org/event-details/regular-dda-board-meeting-2026-09-23-15-00"  # noqa
    )
    assert committee_item["source"] == "https://www.degc.org/dda"


def test_links():
    assert board_item["links"] == [
        {
            "href": "https://www.degc.org/_files/ugd/69e7f0_4cab8fce96484d82bb928ae9198b6e3a.pdf",  # noqa
            "title": "REGULAR DDA BOARD MEETING AGENDA",
        },
        {
            "href": "https://www.degc.org/_files/ugd/69e7f0_bac5faf0ecee4ebc8b996ae903a646b9.pdf",  # noqa
            "title": "REGULAR DDA BOARD MEETING NOTICE",
        },
        {
            "href": "https://us06web.zoom.us/j/88105431213?pwd=mvbyabjG9UoD9wfSiGag4vIWWOKCXd.1",  # noqa
            "title": "Zoom",
        },
        VIDEO_LINK,
    ]


def test_classification():
    assert board_item["classification"] == BOARD
    assert committee_item["classification"] == COMMITTEE


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False


@pytest.mark.parametrize("item", parsed_items)
def test_video_link(item):
    assert item["links"][-1] == VIDEO_LINK
