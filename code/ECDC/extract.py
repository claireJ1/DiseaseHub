import csv, json, datetime, os, re, requests

def read():
    files = os.listdir('.')
    for file in files:
        if re.match(r'ECDC_surveillance.*', file) != None:
            print(file)
            extract_file_to_json(file)

def extract_file_to_json(file):
    result = re.compile(r".*_data_(.*)\.csv").search(file)
    json_file_name = result.group(1) + ".json"
    data_dict = {
        "data_source": "ECDC",
        "dataset_type": "disease outbreaks",
        "dataset_id": "xxx",    
        "time_object": {
            "timestamp": str(datetime.datetime.now()),
            "timezone": "GMT+11" 
        },
        "events": [],
    }
    with open(file, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            data_dict["events"].append(extract_attributes(row))
    # dumping data into s3
    dump_s3(data_dict)

def extract_attributes(data_dict): 
    new_dict = { 
        "time_object": { 
            "timestamp": data_dict['Time'], 
            "duration": datetime.datetime.now().year - int(data_dict['Time']), 
            "duration_unit": "year", 
            "timezone": "GMT+11" 
        }, 
        "event_type": data_dict['HealthTopic'], 
        "attribute": { 
            "indicator": data_dict['Indicator'],
            "region_name": data_dict['RegionName'],
            "region_code": data_dict['RegionCode'],
            "unit": data_dict['Unit'], 
            "unit_value": data_dict['NumValue'], 
            "year": data_dict['Time']
        } 
    }
    return new_dict

def dump_s3(json_data):
    # recieve token
    token = get_token()
    # dump data into S3 using the API provided by F14A_SIERRA
    s3_api = "https://afzpve4n13.execute-api.ap-southeast-2.amazonaws.com/F14A_SIERRA/upload"
    header = {
        "Authorization": token
    }
    x = requests.post(url=s3_api, json=json_data, headers=header)
    print(x.text)

def get_token():
    # recieve token
    token_recieving_url = "https://afzpve4n13.execute-api.ap-southeast-2.amazonaws.com/login"
    header = {
        "username": secret,
        "password": secret,
        "group": "H14B_Bravo"
    }
    x = requests.post(token_recieving_url, json = header)
    return (json.loads(x.text))["token"]


read()