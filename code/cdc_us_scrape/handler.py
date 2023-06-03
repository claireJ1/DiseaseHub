
import sys
sys.path.insert(0, "package/")

import json
import os
import boto3
from datetime import datetime

from cdc_us_scraper import scrape

import newrelic.agent
newrelic.agent.initialize()

@newrelic.agent.lambda_handler()
def handler(event, context):
    s3 = boto3.client("s3")

    try:
        data_dic = json.loads(scrape())
    except Exception as e:
        print(e)
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
        print(e)
        return {
            "statusCode": 500,
            "body": json.dumps(f"Failed to uploaded file into the S3 bucket.")
        }
