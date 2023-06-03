import requests
from scrapingant_client import ScrapingAntClient
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import sys
sys.path.insert(0, "package/")


# a scraper that extracts Global Incident Map data

def scraper():
    # Define URL with a dynamic web content
    curr_day = datetime.today().strftime("%d")
    curr_month = datetime.today().strftime("%b")
    curr_year = datetime.today().strftime("%Y")

    last_week_date = datetime.today() - timedelta(days=6)
    last_week_day = last_week_date.strftime("%d")
    last_week_month = last_week_date.strftime("%b")
    last_week_year = last_week_date.strftime("%Y")

    url = "https://outbreaks.globalincidentmap.com/map?start_date=" \
        + last_week_day + "%20" + last_week_month + "%20" \
        + last_week_year + "&end_date=" + curr_day + "%20" \
        + curr_month + "%20" + curr_year

    # send request to the url website
    result = web_request(url)
    if result == -1:
        return -1

    try_count = 3
    outbreaks = result.find_all("td")
    while outbreaks == [] and try_count > 0:
        result = web_request(url)
        if result == -1:
            return -1
        outbreaks = result.find_all("td")
        try_count -= 1

    data = {}
    data["data_source"] = "global incident map"
    data["dataset_type"] = "disease outbreaks"
    # update dateset id when upload to S3
    data["dataset_id"] = ""
    data["time_object"] = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           "timezone": "GMT+11"}
    data["events"] = []

    for i, event in enumerate(outbreaks):

        if i % 5 == 1:
            event_object = {}
            attribute = {}
            time = {}
            event_type = ""

            # Scraping the details of the outbreak
            href = event.find("a").get("href")
            detail_url = "https://outbreaks.globalincidentmap.com" + href
            detail_page = requests.get(detail_url)
            soup = BeautifulSoup(detail_page.text, 'html.parser')

            # Extract the title of the ourbtreak
            title = soup.find("div", {"class": "col-span-3 mt-2"}).get_text()
            attribute["title"] = title

            # Scarping the attributes for the outrbeak
            web_attr = soup.find_all(
                "div", {"class": "mt-2 col-span-3 md:col-span-1"})
            for j, attributes in enumerate(web_attr):

                # Get the event type
                if j % 8 == 0:
                    event_type = attributes.get_text().rstrip()
                elif j % 8 == 1:
                    time["timestamp"] = attributes.get_text().rstrip()
                    time["duration"] = 0
                    time["duration_unit"] = "second"
                    time["timezone"] = "GMT+11"
                elif j % 8 == 2:
                    country = attributes.get_text().rstrip()
                    attribute["country"] = country[country.find(
                        "(")+1:country.find(")")]
                elif j % 8 == 3:
                    attribute["city"] = attributes.get_text().rstrip()
                elif j % 8 == 5:
                    attribute["severity"] = attributes.get_text().rstrip()

            # Extract event description
            descr = soup.find("div", {"class": "col-span-4 mt-1"}).get_text()
            attribute["description"] = descr

            # Extract related links
            link = soup.find(
                "a", {"class": "text-black hover:text-orange-500"}).get("href")
            attribute["links"] = link

            event_object["time_object"] = time
            event_object["event_type"] = event_type
            event_object["attribute"] = attribute
            data["events"].append(event_object)

    return json.dumps(data)


def web_request(url):
    # Create a ScrapingAntClient instance
    client = ScrapingAntClient(token='8536ba91784e407e8ca76016f8b9f3b7')

    # Get the HTML page rendered content
    try:
        page_content = client.general_request(url).content
    except Exception as e:
        return -1

    # Parse content with BeautifulSoup
    page = BeautifulSoup(page_content, features="html.parser")

    return page
