from concurrent import futures

import datetime, json, requests

import grpc
import sending_pb2_grpc
import sending_pb2

def extract_data(request):
    curr_time = str(datetime.datetime.now())
    data_dict = {
        "data_source": request.data_source,
        "dataset_type": request.dataset_type,
        "dataset_id": request.name + str(int(datetime.datetime.now().timestamp())),    
        "time_object": {
            "timestamp": curr_time,
            "timezone": "GMT+11" 
        },
        "events": [],
    }
    formatted_data = request.data.splitlines()
    attributes_list = formatted_data[0].split(',')
    for (idx, record) in enumerate(formatted_data):
        if idx != 0:
            record = record.split(',')
            data_dict["events"].append(add_event(record, attributes_list, request.event_type))
    return data_dict

def add_event(record, attribute_list, event_type): 
    # getting dictionary of attributes
    attribute_dict = {}
    for i in range(1, len(attribute_list)):
        attribute_dict[attribute_list[i]] = record[i]
    given_time = datetime.datetime.strptime(record[0], '%Y-%m-%d %H:%M:%S.%f')
    new_dict = {
        "time_object": { 
            "timestamp": record[0], 
            "duration": (datetime.datetime.now() - given_time).total_seconds(), 
            "duration_unit": "seconds", 
            "timezone": "GMT+11" 
        },
        "event_type": event_type, 
        "attribute": attribute_dict
    }
    return new_dict

def dump_s3(json_data, token):
    s3_api = "https://afzpve4n13.execute-api.ap-southeast-2.amazonaws.com/F12A_ZULU/upload_s3"
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
    if (not json.loads(x.text)["isAuthorized"]):
        raise Exception('Unverified token')
    
class SenderCSV(sending_pb2_grpc.SenderCSVServicer):
    def SendFile(self, request, context):
        msg = ""
        try:
            verify_token(request.token)
            dumping_data = extract_data(request)
            msg = dump_s3(dumping_data, request.token)
        except Exception as e:
            return sending_pb2.SendResponse(message="(ERROR):"+e.args[0])
        return sending_pb2.SendResponse(message=msg)               
    
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
    run()