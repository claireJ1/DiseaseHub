FROM python:3.9
WORKDIR /app
COPY . .
RUN pip3 install -r /app/code/cdc_int_scrape/requirements.txt
WORKDIR /app/code/cdc_int_scrape
RUN ["python", "cdc_int_scraper.py"]
