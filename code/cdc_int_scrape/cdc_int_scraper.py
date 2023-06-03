#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, 'package/')

from bs4 import BeautifulSoup
import boto3
from datetime import datetime, timezone
from flagbase import FlagbaseClient, Config, Identity #feature flagging
import json
import pytz
import random
import re
import requests
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from os import path

def scrape():

    flagbase = FlagbaseClient(
        config=Config(
            server_key = "sdk-server_cd7d8e93-6b30-4d0a-9205-ee288d8a0b1e"
        )
    )

    user = Identity("user_id", {"some-trait-key": "blue"})
    feature_variation = flagbase.variation("premium-users-data", user, "control")

    html = 'https://www.cdc.gov/outbreaks/'

    html_doc = requests.get(html)
    soup = BeautifulSoup(html_doc.content, 'html.parser')

    int_outbreaks_list = []
    event_dataset = {}

    # The general data
    event_dataset["data_source"] = "Centers for Disease Control and Prevention"
    event_dataset["dataset_type"] = "Disease Outbreaks"
    event_dataset["dataset_id"] = "http://unsw-seng3011-23t1-shared-dev.s3.ap-southeast-2.amazonaws.com" 
    event_dataset["time_object"] = {"timestamp": str(datetime.now()), "timezone": "GMT+11"}    #AEDT is +11 from greenwich
    event_dataset["events"] = []

    # SCRAPE THE LINKS UNDER 'INTERNATIONAL OUTBREAKS' FROM HOMEPAGE
    
    tag = soup.find('ul', attrs={'class':'bullet-list'})

    for article in tag.find_all('a', href=True):

        event_object = {}
        attributes = {}

        int_outbreaks_list.append(article)
        base = "https://www.cdc.gov"
        link_second_half = re.findall(r'\"(.*)\"', str(article))[0]

        # Ebola outbreak considered to have "ended" by the cdc.
        if ("ebola" in link_second_half):
            continue
        
        title = re.findall('<a.*>(.*)</a>', str(article))

        if ("Mpox" in title[0]):
            mpox_html = requests.get(link_second_half)
            mpox_soup = BeautifulSoup(mpox_html.content, 'html.parser')

            int_outbreaks_link = base + (re.findall('<a href\s*=\s*"([^"]*world-map[^"]*)', str(mpox_soup))[0])

            mpox_int_html = requests.get(int_outbreaks_link)
            mpox_int_soup = BeautifulSoup(mpox_int_html.content, 'html.parser')

            file = base + (re.findall('data-config-url\s*=\s*\"([^\"]*confirmed_cases_data[^\"]*)', str(mpox_int_soup))[0])
            mpox_data = requests.get(file)
            mpox_data = json.loads(BeautifulSoup(mpox_data.content, 'html.parser').text)

            for element in mpox_data["datasets"]["https://www.cdc.gov/wcms/vizdata/poxvirus/mpox/data/MPX-Cases-Deaths-by-Country.csv"]["data"]:
                attributes = {}
                time_object = {}
                mini_event = {}

                full_time_object = element["Asof"]

                # All dates have the respect the following format: “yyyy-MM-ddTHH:mm:ss”. 
                v_time = str(re.findall('\d.*\d{4}', full_time_object)[0] + " " + re.findall('\d{4}\s(\d.*:\d.*[?AM|PM])', full_time_object)[0])

                time_object["timestamp"] = str(datetime.strptime(v_time,'%d %b %Y %I:%M %p'))

                time_object["duration"] = 0
                time_object["duration_unit"] = "second"
                time_object["timezone"] = "EDT"

                attributes["location"] = element["Country"]
                attributes["cases"] = element["Cases"]
                attributes["deaths"] = element["Deaths"]
                attributes["source"] = "Unknown"
                attributes["date_of_report"] = str(datetime.strptime(v_time,'%d %b %Y %I:%M %p'))

                mini_event["time_object"] = time_object

                with open("disease_list.json") as f:
                    data = json.load(f)

                for disease in data:
                    if re.search(disease['name'], title[0], re.IGNORECASE):
                        mini_event["event_type"] = disease['name']

                protect_yourself_link = base + (re.findall('<a href\s*=\s*"([^"]*prevention[^"]*)', str(mpox_soup))[0])
                protect_yourself_html = requests.get(protect_yourself_link)
                protect_yourself_soup = BeautifulSoup(protect_yourself_html.content, 'html.parser')

                attributes["control_measures"] = [measure.text for measure in protect_yourself_soup.find_all('div', class_="card-title h5 mb-2")]

                mini_event["attribute"] = attributes

                event_dataset["events"].append(mini_event)
            
        else:
            
            link = base + link_second_half
            covid_main_page = requests.get(link)
            covid_main_page_soup = BeautifulSoup(covid_main_page.content, 'html.parser')

            int_outbreaks_link = base + (re.findall('<a href\s*=\s*"([^"]*us-cases-deaths[^"]*)', str(covid_main_page_soup))[0])

            c_page = requests.get("https://www.cdc.gov/coronavirus/2019-ncov/covid-data/covidview/index.html")
            covid_soup = BeautifulSoup(c_page.text, "html.parser")

            attributes = {}
            time_object = {}
            mini_event = {}

            time_object["timestamp"] = str(datetime.strptime(str((datetime.now(pytz.timezone("America/New_York") )).strftime('%d %b %Y') + " 8:00 PM"),'%d %b %Y %I:%M %p'))
            time_object["duration"] = 0
            time_object["duration_unit"] = "second"
            time_object["timezone"] = "EDT"

            # for premium users, include historical data for all states in the US
            if feature_variation == "treatment":

                protect_yourself_link = base + (re.findall('<a href\s*=\s*"([^"]*prevent-getting-sick/prevention[^"]*)', str(covid_main_page_soup))[0])
                protect_yourself_html = requests.get(protect_yourself_link)
                protect_yourself_soup = BeautifulSoup(protect_yourself_html.content, 'html.parser')

                c_measures = [measure.text for measure in protect_yourself_soup.find_all('h3', class_="card-title mb-1 h4 mb-3 text-left")]
                event_dataset = premium_user_data(title, event_dataset, c_measures)
                data_json = json.dumps(event_dataset, indent=4)
                
                return data_json
            else:
                with open('countries.json') as f:
                    data = json.load(f)

                attributes["location"] = "United States of America"

                cases = (re.search('A total of (.*) COVID-19 cases', str(covid_soup))[0])
                attributes["cases"] = re.findall('\d+,\d+,\d+', cases)[0]
                deaths = (re.search('a total of (.*) COVID-19 deaths', str(covid_soup))[0])
                attributes["deaths"] = re.findall('\d+,\d+,\d+', deaths)[0]
                attributes["source"] = "Wuhan, China"
                attributes["date_of_report"] = str(datetime.strptime(str((datetime.now(pytz.timezone("America/New_York") )).strftime('%d %b %Y') + " 8:00 PM"),'%d %b %Y %I:%M %p'))

                mini_event["time_object"] = time_object

                with open('disease_list.json') as f:
                    data = json.load(f)

                for disease in data:
                    if re.search(disease['name'], title[0], re.IGNORECASE):
                        mini_event["event_type"] = disease['name']

                # control measures
                protect_yourself_link = base + (re.findall('<a href\s*=\s*"([^"]*prevent-getting-sick/prevention[^"]*)', str(covid_main_page_soup))[0])
                protect_yourself_html = requests.get(protect_yourself_link)
                protect_yourself_soup = BeautifulSoup(protect_yourself_html.content, 'html.parser')

                attributes["control_measures"] = [measure.text for measure in protect_yourself_soup.find_all('h3', class_="card-title mb-1 h4 mb-3 text-left")]

                mini_event["attribute"] = attributes

                event_dataset["events"].append(mini_event)
            
    data_json = json.dumps(event_dataset, indent=4)

    return data_json

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

def premium_user_data(title, event_dataset, c_measures):
    base = 'https://www.cdc.gov/outbreaks/'

    covid_data = (requests.get("https://data.cdc.gov/resource/pwn4-m3yp.json")).json()
    
    for c_data in covid_data:
        attributes = {}
        time_object = {}
        mini_event = {}

        time_object["timestamp"] = c_data["date_updated"].replace("T", " ")
        time_object["duration"] = 0
        time_object["duration_unit"] = "second"
        time_object["timezone"] = "EDT"

        with open('us_state_codes.json') as f:
            data = json.load(f)
            if c_data["state"] in data:
                attributes["location"] = data.get(c_data["state"])
            else:
                attributes["location"] = ""

        attributes["cases"] = c_data["new_cases"]
        attributes["deaths"] = c_data["tot_deaths"]
        attributes["source"] = "Wuhan, China"
        attributes["date_of_report"] = c_data["date_updated"].replace("T", " ")

        mini_event["time_object"] = time_object

        with open('disease_list.json') as f:
            data = json.load(f)

        for disease in data:
            if re.search(disease['name'], title[0], re.IGNORECASE):
                mini_event["event_type"] = disease['name']
        
        attributes["control_measures"] = c_measures
        mini_event["attribute"] = attributes
        event_dataset["events"].append(mini_event)

    return event_dataset

if __name__ == '__main__':
    data = scrape()
    dump_s3()