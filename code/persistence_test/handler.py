import sys
sys.path.insert(0, "package/")

import json
import boto3
import os
import base64
import requests

from persistence_test import check_file_content

VALIDATION_URL = 'https://afzpve4n13.execute-api.ap-southeast-2.amazonaws.com/verify_token'

def handler(event, context):

    # Check token
    try:
        token = event['headers']['authorization']
        res = requests.post(VALIDATION_URL, headers={'Authorization': token})
    except Exception as e:
        return {
            'statusCode': res.status_code,
            'body': json.dumps(str(e))
        }
    
    body = json.loads(event['body'])

    # Check params
    params = ['prefix', 'schedule', 'attribute']
    if not (sorted(body.keys()) == sorted(params)):
        return {
            'statusCode': 400,
            'body': json.dumps('Please provide all three attributes in body (prefix, schedule, attribute)')
        }
    
    # Check 
    prefix = body['prefix']
    schedule = body['schedule']
    attribute = body['attribute']
    
     # Get all the objects uploaded by the given group
    s3 = boto3.client('s3')

    try:
        objs = s3.list_objects_v2(Bucket=os.environ['GLOBAL_S3_NAME'],
                                   Prefix=prefix)['Contents']
        
        if (len(objs) == 0):
            return {
                'statusCode': 400,
                'body': json.dumps('No file matches the given prefix')
            }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps('No file matches the given prefix')
        }
    
    get_last_modified = lambda obj: int(obj['LastModified'].strftime('%s'))
    sort_objs = sorted(objs, key=get_last_modified, reverse=True)

    return_json = {}
    return_json['test_upload_schedule'] = 'Passed'

    # Check if schedule worked  
    first_five = sort_objs if len(sort_objs) < 5 else sort_objs[:5]
    if (schedule != 0):
        for i, obj in enumerate(first_five):
            if (i != len(first_five) - 1):
                duration = obj['LastModified'] - sort_objs[i]['LastModified']
                
                # Raise Error in testing services
                if (duration.days > schedule):
                    return_json['test_upload_schedule'] = 'Failed'
                    break

    # check file content in the correct format
    test_files = 0
    for x in range(0, len(first_five)):
        key = first_five[x]['Key']
        
        try:
            file_obj = s3.get_object(Bucket=os.environ['GLOBAL_S3_NAME'], Key=key)
            file_content = json.loads(file_obj['Body'].read().decode('utf-8'))
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps(str(e))
            }

        file_test = check_file_content(file_content, attribute)
        if 'Failed' in file_test.values():
            test_name = 'test_' + key + '_components'
            return_json[test_name] = 'Failed'
            return_json.update(file_test)
            test_files = 1
            break
    
    if (test_files == 0):
        return_json['test_dataset_attributes'] = 'Passed'
        return_json['test_overall_event_attributes'] = 'Passed'
        return_json['test_event_time_object'] = 'Passed'
        return_json['test_event_type'] = 'Passed'
        return_json['test_event_attribute'] = 'Passed'

    
    return {
        'statusCode': '200',
        'body': json.dumps(return_json)
    }

