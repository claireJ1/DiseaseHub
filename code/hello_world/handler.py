
import logging
import json

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

def handler(event, context):
    print("Hello World")
    try:
        LOGGER.info(f"Received event: {event}")
        return {
            "statusCode": 200,
            "body": json.dumps(event),
            "headers": {
                "Content-Type": "application/json",
            },
        }
    except Exception as e:
        LOGGER.error(f"Error hello world: {e}")
        return {
            "statusCode": 500,
            "body": '{"status":"Server error"}',
            "headers": {
                "Content-Type": "application/json",
            },
        }