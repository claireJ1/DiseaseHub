import os
import sys
sys.path.insert(0, "package/")

import requests
import boto3
from bs4 import BeautifulSoup
import re
import json
from os import path
from datetime import datetime

import newrelic.agent
newrelic.agent.initialize()

def new_event():
    # template dictionary for event data
    event_data = {
        "time_object": { 
            "timestamp": "", 
            "duration": 0,
            "duration_unit": "second", 
            "timezone": "GMT+11" 
        }, 
        "event_type": "",
        "attribute": { 
            "location": "", 
            "source_of_outbreak": "",
            "date_of_publication": "",
            "cases": 0,
            "deaths": 0,
            "control_measures": ""
        } 
    }
    
    return event_data

def create_json(events):
    # dump into json file

    # filename = '/tmp/cdc_us_outbreaks_data.json'

    content = {
        "data_source": "cdc",
        "dataset_type": "disease outbreaks",
        "dataset_id": "http://unsw-seng3011-23t1-shared-dev.s3.ap-southeast-2.amazonaws.com",
        "time_object": {
            "timestamp": str(datetime.now()),
            "timezone": "GMT+11"
        },
        "events": []
    }

    content["events"] = events
    data = json.dumps(content, indent=4)

    # with open(filename, 'w') as f:
    #     f.write(data)

    return data

def extract_location(page_content):

    with open('us_state_codes.json') as f:
        data = json.load(f)

    states = []

    for state in data:
        if re.search(data[state], page_content, re.IGNORECASE) and data[state] not in states:
            states.append(data[state])

    return ', '.join(states)

def extract_event_type(page_content):

    with open('disease_list.json') as f:
        data = json.load(f)

    for disease in data:
        if re.search(disease['name'], page_content, re.IGNORECASE):
            return disease['name']
    return None


def page_scrape(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    text_location = "States affected"
    text_source = "source"
    text_cases = "Illnesses: "
    text_deaths = "Deaths: "
    text_control = "prevent"

    try:
        event_type = soup.find("h1").getText()
        event_type = extract_event_type(event_type)
        if event_type is None:
            event_type = soup.find("html").getText()
            event_type = extract_event_type(event_type)
            if event_type is None:
                event_type = soup.find("h1").getText()
    except:
        event_type = ""

    try:
        publication_date = soup.find('span', id="last-reviewed-date").getText()
    except:
        publication_date = ""

    location_page = soup.find("html").getText()
    
    try:
        location = extract_location(location_page)
    except:
        location = ""


    timestamp = datetime.now()

    try:
        source = soup.find(lambda tag: tag.name == "p" and text_source in tag.text).getText()
        if "cookies" in source:
            source = ""
    except:
        source = ""
    try:
        cases = soup.find(lambda tag: tag.name == "li" and text_cases in tag.text).getText()
        cases = int(re.sub("[^0-9]", "", cases))
    except:
        try:
            text_cases = "Cases: "
            cases = soup.find(lambda tag: tag.name == "li" and text_cases in tag.text).getText()
            cases = int(re.sub("[^0-9]", "", cases))
        except:
            cases = ""
    try:
        deaths = soup.find(lambda tag: tag.name == "li" and text_deaths in tag.text).getText()
        deaths = int(re.sub("[^0-9]", "", deaths))
    except:
        deaths = ""
    try:
        control = soup.find(lambda tag: tag.name == "li" and text_control in tag.text).getText().strip()
    except:
        control = ""
        print(control)

    json = new_event()

    json['time_object']['timestamp'] = str(timestamp)
    json['event_type'] = event_type
    json['attribute']['location'] = location
    json['attribute']['source_of_outbreak'] = source.strip()
    json['attribute']['date_of_publication'] = publication_date
    json['attribute']['cases'] = cases
    json['attribute']['deaths'] = deaths
    json['attribute']['control_measures'] = str(control)

    return json



def scrape():
    # Start from homepage
    HOME_URL = 'https://www.cdc.gov/outbreaks/'
    homepage = requests.get(HOME_URL)

    soup = BeautifulSoup(homepage.content, "html.parser")
    events = []

    us_outbreaks = soup.find("p", string="Recent investigations reported on CDC.gov").find_next("div")
    reports = us_outbreaks.find_all("li")
    for report in reports:
        report_page = report.find("a", href=True)
        if report_page['href'].startswith('https://www.cdc.gov/'):
            event = page_scrape(report_page['href'])
        else:
            event = page_scrape('https://www.cdc.gov' + report_page['href'])
        events.append(event)
    json = create_json(events)
    return json

def dump_s3():
    s3 = boto3.client("s3")

    try:
        data_dic = json.loads(scrape())
    except Exception as e:
        return {
            "statusCode": 500,
            "body": '{"status":"Server error"}',
            "headers": {
                "Content-Type": "application/json",
            },
        }
    
    file_id = int(datetime.now().timestamp())
    key = "H14B_BRAVO_" + str(file_id) + ".json"
    data_dic["dataset_id"] = "https://unsw-seng3011-23t1-shared-dev.s3.ap-southeast-2.amazonaws.com/" + key
    body = json.dumps(data_dic).encode('utf-8')

    try:
        obj = s3.put_object(Body=body, Bucket=os.environ["GLOBAL_S3_NAME"], Key=key)
        return {
            "statusCode": 200,
            "body": json.dumps(f"Successfully uploaded file into the S3 bucket.")
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Failed to uploaded file into the S3 bucket.")
        }

if __name__ == '__main__':
    data = scrape()
    with open('data.json', 'w') as f:
        json.dump(data, f)
        
    dump_s3()
