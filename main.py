# to run the script with FastAPI: fastapi dev main.py
# to run the script with uvicorn with fastapi at port 55722: uvicorn main:app --host 0.0.0.0 --port 55722

# import the Fast API package
from fastapi import FastAPI, Response
from datetime import date
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from fastapi import Request
import pymongo
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from typing import List
from fastapi import BackgroundTasks

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware

from pyfcm import FCMNotification
fcm = FCMNotification(service_account_file="pushasg5-firebase-adminsdk-wx129-51ffe89fcb.json", project_id="pushasg5")

# for testing, you can update this one to your student ID
student_list = ["1155222493"] 

# MongoDB Atlas connection
uri = "mongodb+srv://usrxinyi:xinyi@xinyidemo.65xoh.mongodb.net/?retryWrites=true&w=majority&appName=XinyiDemo"

client = MongoClient(uri, server_api=ServerApi('1'))
db = client['MobileAsg']  # 替换为你的数据库名
collection_room = db['Chatroom']
collection_history = db['HistoryMessage']
# collection_history = db['User']
# collection = db["User"]
collection_tokens = db["UserTokens"]
# define a Fast API app
app = FastAPI()


# define a route, binding a function to a URL (e.g. GET method) of the server
@app.get("/")
async def root():
    return {"message": "Hello World"}


class DemoItem(BaseModel):
  a: int
  b: int
class TokenItem(BaseModel):
    user_id: int  # 用户的唯一 ID
    token: str    # 从 Firebase 获取的 FCM 令牌
    
@app.post("/demo/")
async def post_demo(item: DemoItem):  
    print(item)
    if item.a + item.b == 10:
        data = {"status": "OK"}
        return JSONResponse(content=jsonable_encoder(data))
        
    data = {"status": "ERROR", "message": "can see"}
    return JSONResponse(status_code=400, content=jsonable_encoder(data))


class Chatroom(BaseModel):
    id: int  # 使用 str 类型，因为 MongoDB 的 ObjectId 是字符串
    name: str
    
class MessageItem(BaseModel):
    message: str
    name: str
    message_time: str
    user_id: int
    # chatroom_id: int
    

@app.get("/get_chatrooms/", response_model=List[Chatroom])
async def get_chatrooms(request: Request):
    res = {
        # 客户端连接的 host
        "host": request.client.host,
        # 客户端连接的端口号
        "port": request.client.port,
        # 请求方法
        "method": request.method,
        # 请求路径
        "base_url": request.base_url,
        # request headers
        "headers": request.headers,
        # request cookies
        "cookies": request.cookies
    }
    print(f'HTTP request-----{res}')
    if request.query_params:
        data = {"status": "ERROR", "message": "Excess parameters"}
        print('Excess parameters')
        return JSONResponse(status_code=400, content=jsonable_encoder(data))
    chatrooms = list(collection_room.find())
    data_list = [
        Chatroom(id=chatroom["id"], name=chatroom["name"])
        for chatroom in chatrooms
    ]
    data = {"data": data_list, "status": "OK"} 
    return JSONResponse(content=jsonable_encoder(data))
    
@app.get("/get_messages/")
async def get_messages(request: Request, chatroom_id: int = -1, status_code=200):
    res = {
        "host": request.client.host,# 客户端连接的 host
        "port": request.client.port,# 客户端连接的端口号
        "method": request.method,
        "base_url": request.base_url,# 请求路径
        "headers": request.headers,# request headers
        "cookies": request.cookies# request cookies
    }
    print(f'HTTP request-----{res}')
    # calculate param number
    param_str = request.query_params.__str__()
    param_num = 0
    for s in param_str:
        if s == '=':
            param_num += 1
    if param_num > 1:
        data = {"status": "ERROR", "message": "Excess parameters"}
        print('Excess parameters')
        return JSONResponse(status_code=400, content=jsonable_encoder(data))
    if not request.query_params:
        data = {"status": "ERROR", "message": "Insufficient parameters"}
        print('Insufficient parameters')
        return JSONResponse(status_code=400, content=jsonable_encoder(data))
    print(f'get chatroom_id is:{chatroom_id}')
    print(type(chatroom_id))
    if chatroom_id in [2, 3, 4]:
        messages = list(collection_history.find({"chatroom_id": chatroom_id}))
        print(f'corr messages: {messages}')
        data_list = [
            MessageItem(message=msg["message"], name=msg["name"], message_time = msg["message_time"], user_id = msg['user_id'])
            # MessageItem(message=msg["message"], name=msg["name"], user_id = msg['user_id'])
            for msg in messages
        ]
        data = {
            "data": {
                "messages": data_list
            },
            "status": "OK"
        }
        return JSONResponse(content=jsonable_encoder(data))
    # error message
    data = {
        "data": {"messages": []},
        "status": "ERROR"
    }
    return JSONResponse(content=jsonable_encoder(data))

@app.post("/send_message/")
async def send_message(request: Request): 
    res = {
        "host": request.client.host,# 客户端连接的 host
        "port": request.client.port,# 客户端连接的端口号
        "method": request.method,
        "base_url": request.base_url,# 请求路径
        "headers": request.headers,# request headers
        "cookies": request.cookies# request cookies
    }
    print(f'HTTP request-----{res}')
    item = await request.json()
    item["chatroom_id"] = int(item["chatroom_id"])
    item["user_id"] = int(item["user_id"])
    print(item)
    list_of_keys = list(item.keys())
    print(f'list_of_keys: {list_of_keys}')
    if len(list_of_keys) != 5:
        print('1')
        data = {"status": "ERROR", "message": list_of_keys +" Insufficient or excess parameters"}
        print('Insufficient or excess parameters')
        return JSONResponse(status_code=400, content=jsonable_encoder(data))
    
    if "chatroom_id" not in item.keys() or item["chatroom_id"] not in [2, 3, "2", "3"]: # 用于chatroom的err msg
        data = {"status": "ERROR", "message": "Non-existing chatroom id"}
        print(data['message'])
        return JSONResponse(status_code=400, content=jsonable_encoder(data))
    
    if len(item['message']) > 200:
        data = {
            "status": "ERROR",
            "message": "Message is INVALID due to length larger than 200 characters"
        }
        print(data['message'])
        return Response(status_code=400, content=data['message'])
        
    if len(item['name']) > 20:
        data = {"status": "ERROR", "message_name": item['name'] + " is INVALID due to message name's length larger than 20 characters"}
        print('INVALID due to message name length larger than 20 characters')
        return JSONResponse(status_code=400, content=jsonable_encoder(data))
    

    collection_history.insert_one(item)
    data = {"status": "OK", "message": item['message'] + " is created"}  
    print(data['message'])
    
        # Check if recipient is in the same chatroom
        
    # fcm_token = "fRFhCg1qQbqu6Mq1cYh8HY:APA91bFbVJD1UO-Cr0PrrsfynS7FODqBWvr7Cgm5v6mpsOga-jVd1BJPvV1DCVBnryQvxaebokxktxnJYGtnhMZuOksgXB9b1Z3BbI5eT6kcI1tHY8Nm_ec"
    # fcm_token = "dM0LX7ndQca92tNzxCx81k:APA91bGymj6D5BBzIoHPAIVRVrgO-70c_-GSfVmWdUXPnr8z0ME3A2zrfAByccn3pOLRqJmJEJ51DV9uFID55JAd2lXI98cWDdNU8sxbukIOrbSVsRoD_B0"
    # notification_title = "Main sends you a message!"
    # notification_body = "Hello from Danny Main!"
    # result = fcm.notify(fcm_token=fcm_token, notification_title=notification_title, notification_body=notification_body)
    # Sending a notification with data message payload
    # data_payload = {"foo": "bar","body": "great match!","room": "PortugalVSDenmark"}
    # To a single device
    
    # recipient_tokens = collection_tokens.find({"user_id": item["user_id"]})
    all_utoken = list(collection_tokens.find())
    print(f'all user_token_collection:{all_utoken}')
    print(f'current user_id: {item["user_id"]}')
    cur_token = list(collection_tokens.find({"user_id": item['user_id']}))
    print(f'cur_token: {cur_token}')
    for push_utoken in all_utoken:
        ptoken = push_utoken['token']
        if ptoken != cur_token[0]['token']:
            print(f'should be sent token:{ptoken}')
            notification_title = list(collection_room.find({"id": item["chatroom_id"]}))[0]['name']
            print(f'notification_title: {notification_title}')
            result = fcm.notify(fcm_token=ptoken, notification_title=notification_title, notification_body=item['message'])
    #     print('push token')
    #     print(f'push_token: {push_token}')
    #     result = send_push_notification(push_token['token'], item["message"])
    #     # print(result)
    return JSONResponse(content=jsonable_encoder(data))

@app.post("/store_token/")
async def store_token(item: TokenItem):
    # TokenItem should have user_id and token fields
    collection_tokens.insert_one({"user_id": item.user_id, "token": item.token})
    return JSONResponse(content={"status": "OK"})
# @app.post("/send_message/")
# async def send_message(request: Request): 
#     item = await request.json()
#     list_of_keys = list(item.keys())
#     data = {"status": "OK", "message": item['message'] + " SUCCESSFULLY CREATED"}
#     return JSONResponse(status_code=400, content=jsonable_encoder(data))
#     if len(list_of_keys) != 4:
#         data = {"status": "ERROR", "message": "Insufficient or excess parameters" + str(list_of_keys)}
#         return JSONResponse(status_code=400, content=jsonable_encoder(data))
    
#     if "chatroom_id" not in item or item["chatroom_id"] not in [2, 3, "2", "3"]:
#         data = {"status": "ERROR", "message": "Non-existing chatroom id"}
#         return JSONResponse(status_code=400, content=jsonable_encoder(data))
    
#     if len(item['message']) > 200:
#         data = {
#             "status": "ERROR",
#             "message": "Message is INVALID due to length larger than 200 characters"
#         }
#         return JSONResponse(status_code=400, content=jsonable_encoder(data))
        
#     if len(item['name']) > 20:
#         data = {"status": "ERROR", "message": "INVALID due to name length larger than 20 characters"}
#         return JSONResponse(status_code=400, content=jsonable_encoder(data))
    
#     # 假设item有效，可以插入
#     collection.insert_one(item)
#     data = {"status": "OK", "message": item['message'] + " SUCCESSFULLY CREATED"}
#     return JSONResponse(status_code=201, content=jsonable_encoder(data))
async def send_push_notification(token: str, message: str):
    # url = "https://fcm.googleapis.com/fcm/send"
    # headers = {
    #     "Authorization": "key=YOUR_SERVER_KEY",
    #     "Content-Type": "application/json"
    # }
    data_payload = {
        "to": token,
        "notification": {
            "title": "New Message",
            "body": message
        }
    }
    notification_title = "Sent Successful!"
    notification_body = "Hello from Server!"
    # requests.post(url, headers=headers, json=payload)
    result = fcm.notify(fcm_token=token, notification_body=notification_body, data_payload=data_payload)
    return result
