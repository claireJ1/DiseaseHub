import pytest
import json
import os
import sys

sys.path.append('./code/cdc_us_scrape/cdc_us_outbreaks_data.json')
file_path = './code/cdc_us_scrape/cdc_us_outbreaks_data.json'

def test_attributes():
    attributes = ['location', 'source_of_outbreak', 
        'date_of_publication', 'cases', 'deaths', 'control_measures']

    with open(file_path) as f:
        data = json.load(f)

    # Check all attributes are contained in the event data
    for event in data['events']:
        for attribute in attributes:
            assert attribute in event['attribute']
    
def test_attributes_not_none():
    attributes = ['location', 'source_of_outbreak', 
        'date_of_publication', 'cases', 'deaths', 'control_measures']

    with open(file_path) as f:
        data = json.load(f)

    # Check all attributes are contained in the event data
    for event in data['events']:
        for attribute in attributes:
            assert event['attribute'][attribute] != None