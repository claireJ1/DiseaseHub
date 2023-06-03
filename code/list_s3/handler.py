import json, os
import boto3

def handler(event, context):
    print("This is a log")
    if os.getenv("ENV"):
        print("ENV =", os.getenv)
    s3 = boto3.client('s3')
    try:
        contents = s3.list_objects(Bucket=os.getenv("GLOBAL_S3_NAME"))
        keys = [item['Key'] for item in contents['Contents']]
        return {
            "statusCode": 200,
            "body": json.dumps({'keys': keys}),
            "headers": {
                "Content-Type": "application/json",
            },
        }
    except Exception as e:
        print(str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({'message': "Something went wrong :("}),
            "headers": {
                "Content-Type": "application/json",
            },
        }