from concurrent import futures

import logging, datetime, json, re, requests

import grpc
import sending_pb2_grpc
import sending_pb2


def extract_data(data):
    curr_time = str(datetime.datetime.now())
    data_dict = {
        "data_source": "ECDC",
        "dataset_type": "disease outbreaks",
        "dataset_id": "H14B_Bravo_ECDC_" + curr_time,    
        "time_object": {
            "timestamp": curr_time,
            "timezone": "GMT+11" 
        },
        "events": [],
    }
    formatted_data = data.splitlines()
    for record in formatted_data:
        record = record.split(',')
        record[1] = int(re.findall(r'\d+', record[1])[0])
        record[3] = float(record[3]) if record[3] != '-' else 0.0
        data_dict["events"].append(extract_attributes(record))
    return data_dict

def extract_attributes(record): 
    new_dict = { 
        "time_object": { 
            "timestamp": record[1], 
            "duration": datetime.datetime.now().year - (record[1]), 
            "duration_unit": "year", 
            "timezone": "GMT+11" 
        }, 
        "event_type": "Case Numbers", 
        "attribute": { 
            # No symptoms
            "disease": record[0],
            "location": record[2],
            "event_date": record[1],
            "number_cases": record[3],
        }
    }
    return new_dict

def dump_s3(json_data, token):
    s3_api = "https://afzpve4n13.execute-api.ap-southeast-2.amazonaws.com/F14A_SIERRA/upload"
    header = {
        "Authorization": token
    }
    x = requests.post(url=s3_api, json=json_data, headers=header)
    return x.text

def verify_token(token):
    verification_url = "https://afzpve4n13.execute-api.ap-southeast-2.amazonaws.com/verify_token"
    header = {
        "Authorization": token
    }
    x = requests.post(url=verification_url, headers=header)
    return(json.loads(x.text)["isAuthorized"])

class SenderCSV(sending_pb2_grpc.SenderCSVServicer):

    def SendFile(self, request, context):
        verified = verify_token(request.token)
        if (not verified):
            return sending_pb2.SendResponse(message="(ERROR) Unverified token")            
        dumping_json = extract_data(request.data)
        # msg = dump_s3(dumping_json, request.token)
        return sending_pb2.SendResponse(message="Dumped data")            
            
    
def run():
    port = '80'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    sending_pb2_grpc.add_SenderCSVServicer_to_server(
        SenderCSV(), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()

if __name__ == '__main__':
    # logging.basicConfig()
    run()