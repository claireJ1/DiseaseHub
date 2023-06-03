#!/usr/bin/env python3
import sys
sys.path.insert(0, 'package/')

from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import pytz
import re
import requests
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from os import path

def scrape():
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

                attributes["country"] = element["Country"]
                attributes["cases"] = element["Cases"]
                attributes["deaths"] = element["Deaths"]
                attributes["source"] = "Unknown"
                attributes["date_of_report"] = str(datetime.strptime(v_time,'%d %b %Y %I:%M %p'))

                mini_event["time_object"] = time_object

                with open('/tmp/disease_list.json') as f:
                    data = json.load(f)

                for disease in data:
                    if re.search(disease['name'], title[0], re.IGNORECASE):
                        mini_event["event_type"] = disease['name']

                mini_event["attribute"] = attributes

                event_dataset["events"].append(mini_event)
        else:
            
            link = base + link_second_half
            covid_main_page = requests.get(link)
            covid_main_page_soup = BeautifulSoup(covid_main_page.content, 'html.parser')

            int_outbreaks_link = base + (re.findall('<a href\s*=\s*"([^"]*us-cases-deaths[^"]*)', str(covid_main_page_soup))[0])

            # open through selenium to get required html
            driver = webdriver.Chrome(ChromeDriverManager().install())
            driver.get(int_outbreaks_link) 
            time.sleep(6) 
            html = driver.page_source

            covid_soup = BeautifulSoup(html, "html.parser")

            attributes = {}
            time_object = {}
            mini_event = {}

            time_object["timestamp"] = str(datetime.strptime(str((datetime.now(pytz.timezone("America/New_York") )).strftime('%d %b %Y') + " 8:00 PM"),'%d %b %Y %I:%M %p'))
            time_object["duration"] = 0
            time_object["duration_unit"] = "second"
            time_object["timezone"] = "EDT"

            with open('/tmp/countries.json') as f:
                data = json.load(f)

            for countries in data:
                if re.search(countries['name'], str(covid_soup), re.IGNORECASE):
                    attributes["country"] = countries['name']

            attributes["cases"] = covid_soup.find("span", {'id' : 'status-cases-total'}).text
            attributes["deaths"] = covid_soup.find("span", {'id' : 'status-deaths-total'}).text
            attributes["source"] = "Wuhan, China"
            attributes["date_of_report"] = str(datetime.strptime(str((datetime.now(pytz.timezone("America/New_York") )).strftime('%d %b %Y') + " 8:00 PM"),'%d %b %Y %I:%M %p'))

            mini_event["time_object"] = time_object

            with open('/tmp/disease_list.json') as f:
                data = json.load(f)

            for disease in data:
                if re.search(disease['name'], title[0], re.IGNORECASE):
                    mini_event["event_type"] = disease['name']

            mini_event["attribute"] = attributes

            event_dataset["events"].append(mini_event)

            driver.close()

    data_json = json.dumps(event_dataset, indent=4)

    return data_json
