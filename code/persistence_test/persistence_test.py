import sys
sys.path.insert(0, "package/")

import json

file_template = { 
    "data_source": "str", 
    "dataset_type": "str", 
    "dataset_id": "str", 
    "time_object": { 
        "timestamp": "str", 
        "timezone": "str" 
    }, 
    "events": []
}

time_template = { 
                    "timestamp": "2019-07-21 13:04:40.3401012", 
                    "duration": 1, 
                    "duration_unit": "second", 
                    "timezone": "GMT+11" 
                }

attribute_template_2 = {"att1": 2, "att2": "efq", "att3": "ee"}

file_content_1 =  { 
    "data_source": "datasource_X", 
    "dataset_type": "sensor_X", 
    "dataset_id": "http://bucket-name.s3-website-Region.amazonaws.com", 
    "time_object": { 
        "timestamp": "2023-02-12 07:52:02.921420",
        "timezone": "GMT+11"
    }, 
    "events": [
            {
                "time_object": { 
                    "timestamp": "2019-07-21 13:04:40.3401012", 
                    "duration": 1, 
                    "duration_unit": "second", 
                    "timezone": "GMT+11"
                },
                "event_type": "efe",
                "attribute": {"att1": 2, "att2": "efq", "att3": "ee"}
            },
            {
                "time_object": { 
                    "timestamp": "2019-07-21 13:04:40.3401012", 
                    "duration": 1, 
                    "duration_unit": "second", 
                    "timezone": "GMT+11"
                },
                "event_type": "sdfee",
                "attribute": {"att1": "3", "att2": "efq", "att3": "ee"}
            }
            ]
}


def check_file_content(file_content, attribute_template):

    return_json = {}
    return_json['test_dataset_attributes'] = 'Passed'
    return_json['test_overall_event_attributes'] = 'Passed'

    # check dataset attribute
    if (check_dictionary(file_content, file_template) != 0):
        return_json['test_dataset_attributes'] = 'Failed'

    # check events 
    event_failed = 0
    for event in file_content['events']:
        test_json = check_event_content(event, attribute_template)
        if 'Failed' in test_json.values():
            return_json['test_overall_event_attributes'] = 'Failed'
            return_json.update(test_json)
            event_failed = 1
            break
    
    if event_failed == 0:
        return_json['test_event_time_object'] = 'Passed'
        return_json['test_event_type'] = 'Passed'
        return_json['test_event_attribute'] = 'Passed'
    
    return return_json

def check_dictionary(output, template):

    for k1 in template.keys():
        if k1 in output.keys():
            if (isinstance(output[k1], dict)):
                if (check_dictionary(output[k1], template[k1]) != 0):
                    return -1
            elif (isinstance(output[k1], str) and len(output[k1]) == 0):
                return -1
        
        else:
            return -1
    
    return 0


def check_event_content(output, event_attribute):

    # check time object
    return_json = {}
    return_json['test_event_time_object'] = 'Passed'
    return_json['test_event_type'] = 'Passed'
    return_json['test_event_attribute'] = 'Passed'

    if not ('time_object' in output.keys() and check_dictionary(output['time_object'], time_template) == 0):
        return_json['test_event_time_object'] = 'Failed'

    # check event_type
    if not ('event_type' in output.keys() and len(output['event_type']) != 0):
        return_json['test_event_type'] = 'Failed'
    
    # check attribute
    if not ('attribute' in output.keys() and check_dictionary(output['attribute'], event_attribute) == 0):
        return_json['test_event_attribute'] = 'Failed'

    return return_json
