# encoding=utf8
"""
Author Lingfengyu
Date 2024-07-21 10:35
LastEditors Lingfengyu
LastEditTime 2024-07-23 22:32
Description 
Feature 
"""

import asyncio
import base64
from curses import echo
import json
import os
import websockets

from model import test_model

async def call_result(websocket, code, char, score, message):
    """
    @Description 返回结果
    @Feature 
    @param websocket
    @param code 状态码
    @param char 识别字符
    @param score 识别分数
    @param message 消息
    """
    result = {"code": code, "char": char, "score": score, "message": message}
    await websocket.send(json.dumps(result, ensure_ascii=False))

async def handler(websocket):
    """
    @Description 处理事务的逻辑
    @Feature 接受图片调用模型返回分数
    @param websocket 
    """
    async for message in websocket:
        rec = json.loads(message)
        with open("image/image.jpg", "wb") as image_file:
            image_file.write(base64.b64decode(rec["image"]))
        char, score = test_model()
        if char == -1 and score == -1:
            await call_result(websocket, "500", "", "", "An error occured.")
        else:
            await call_result(websocket, "200", f"{char}", f"{score}", "OK.")

async def echo(websocket):
    """
    @Description 在运行之前检查请求头
    @Feature 
    @param websocket
    """
    headers = websocket.request_headers
    if headers.get("RQ-From-Client") == "MMQM":
        if headers.get("Result-Type") == "SCORE":
            await handler(websocket)
    await call_result(websocket, "403", "", "", "Forbidden.")

async def main():
    async with websockets.serve(echo, "", 26451):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    # 启动时创建或清空image文件夹
    if os.path.exists("image/"):
        for i in os.listdir("image/"):
            os.remove("image/" + i)
    else:
        os.mkdir("image")
    # 哪来那么多异常，都是自找苦吃
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("User manually exit.")
    except ConnectionError:
        print("Remote user closed a connection unexcepted.")
    except websockets.exceptions.ConnectionClosedError():
        print("Remote connection shutdown without closed.")
