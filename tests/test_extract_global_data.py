import pytest
import json
import sys
import datetime

sys.path.append('./code/upload_global_incident')
from scraper import scraper

data = json.loads(scraper())

def test_data_attributes():
    data_attributes = ["data_source", "dataset_type", "dataset_id", "time_object", "events"]
    assert len(data) == 5

    for key in data:
        assert data_attributes.count(key) == 1
        if key != "dataset_id":
            assert len(data[key]) != 0
    
def test_event_attributes():
    events = data["events"]
    event_attributes = ["time_object", "event_type", "attribute"]
    assert len(events) != 0

    if (len(events) > 0):
        for key in events[0]:
            assert event_attributes.count(key) == 1
            assert len(events[0][key]) != 0

        # check individual attributes
        selected_attr = ["title", "country", "city", "severity", "description", "links"]
        for event in events:
            assert len(event["attribute"]) == 6

            for attr in event["attribute"]:
                assert selected_attr.count(attr) == 1
                assert len(event["attribute"][attr]) != 0
            
def test_event_time():
    # since lambda is invoked weekly, event time should be within 7 days
    events = data["events"]
    end_date = datetime.datetime.now()
    start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    for event in events:
        date = event["time_object"]["timestamp"]
        date_object = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        assert date_object >= start_date and date_object <= end_date


            