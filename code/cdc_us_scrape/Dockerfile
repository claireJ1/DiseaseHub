FROM python:3.9-slim-buster
WORKDIR /app
ADD . /app
WORKDIR /app/code/cdc_us_scrape
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python", "cdc_us_scraper.py"]
