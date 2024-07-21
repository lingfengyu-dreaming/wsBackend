"""
Author Lingfengyu
Date 2024-07-21 10:35
LastEditors Lingfengyu
LastEditTime 2024-07-21 18:09
Description 
Feature 
"""

import asyncio
import base64
import json
import os
import websockets

from model import test_model

async def handler(websocket):
    """
    @Description 处理事务的逻辑
    @Feature 接受图片调用模型返回分数
    @param websocket
    @return 
    """
    async for message in websocket:
        rec = json.loads(message)
        with open("image/image.jpg", "wb") as image_file:
            image_file.write(base64.b64decode(rec["image"]))
        char, score = test_model()
        result = {"code": "", "char": "", "score": "", "message": ""}
        if char == -1 and score == -1:
            result["code"] = "500"
            result["message"] = "An error occured."
        else:
            result["code"] = "200"
            result["char"] = f"{char}"
            result["score"] = f"{score}"
        await websocket.send(json.dumps(result))

async def main():
    async with websockets.serve(handler, "", 26451):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    # 启动时创建或清空image文件夹
    if os.path.exists("image/"):
        for i in os.listdir("image/"):
            os.remove("image/" + i)
    else:
        os.mkdir("image")
    # 哪来那么多异常，都是自作自受
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("User manually exit.")
    except ConnectionError:
        print("Remote user closed a connection unexcepted.")
    except websockets.exceptions.ConnectionClosedError():
        print("Remote connection shutdown without closed.")
