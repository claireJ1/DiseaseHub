import json, os
from datetime import datetime
import boto3

import newrelic.agent
newrelic.agent.initialize()

@newrelic.agent.lambda_handler()
def handler(event, context):
    print("Scheduled function is called")
    print("Time now is", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("event", event)
    print("context", context)