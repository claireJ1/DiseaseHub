import json 
import pytest
import sys
import os

sys.path.append('./code/cdc_int_scrape/tmp/sample.json')
fpath = './code/cdc_int_scrape/tmp/sample.json'
#from cdc_int_scraper import scrape

def test_length_of_return_data():

    with open(fpath) as f:
        data = json.load(f)

    assert len(data) > 0

def test_attributes():

    data_attributes = ["cases", "country", "deaths", "source", "date_of_report", "control_measures"]

    with open(fpath) as f:
        data = json.load(f)

    for event in data["events"]:
        assert len(event["attribute"]) == 6
        for attribute in event["attribute"]:
            assert attribute in data_attributes

def test_check_both_outbreaks():
    with open(fpath) as f:
        data = json.load(f)

    for event in data["events"]:
        if (str(event["event_type"]) != "COVID-19"):
            if (str(event["event_type"]) != "Mpox"):
                assert False 
    
    assert True