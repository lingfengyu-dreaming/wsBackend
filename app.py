# encoding=utf8
"""
Author Lingfengyu
Date 2024-07-21 10:35
LastEditors Lingfengyu
LastEditTime 2024-07-31 17:11
Description 
Feature 
"""

import asyncio
import base64
import binascii
# from curses import echo
import json
import logging
import os
import shutil
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
        # log.info(f"{websocket.remote_address[0]} - Connection receive:{rec}")
        if 'image' in rec:
            try:
                with open("image/image.jpg", "wb") as image_file:
                    image_file.write(base64.b64decode(rec["image"]))
            except (binascii.Error, ValueError):
                log.error(f"{websocket.remote_address[0]} - Image error.")
                await call_result(websocket, "400", "", "", "Bad request.")
                await websocket.close()
        else:
            log.error(f"{websocket.remote_address[0]} - Image missing.")
            await call_result(websocket, "400", "", "", "Bad request.")
            await websocket.close()
        char, score = test_model()
        print(f"Char:{char}, Score:{score}")
        if char == -1 and score == -1:
            log.error(f"{websocket.remote_address[0]} - Server internal error")
            await call_result(websocket, "500", "", "", "An error occured.")
            await websocket.close()
        else:
            log.info(f"{websocket.remote_address[0]} - Result: char{char}, score{score}.")
            await call_result(websocket, "200", f"{char}", f"{score}", "OK.")

async def echo(websocket):
    """
    @Description 在运行之前检查请求头
    @Feature 
    @param websocket
    """
    client_ip, client_port = websocket.remote_address[0], websocket.remote_address[1]
    print(f"Connect to: {client_ip}:{client_port}")
    log.info(f"Connect to {client_ip}:{client_port}")
    headers = websocket.request_headers
    if headers.get("RQ-From-Client") == "MMQM":
        if headers.get("Result-Type") == "SCORE":
            log.info(f"{websocket.remote_address[0]} - Client Header OK.")
            await handler(websocket)
        else:
            log.error(f"{websocket.remote_address[0]} - Client Header Error! Connection BLOCKED.")
            await call_result(websocket, "403", "", "", "Forbidden.")
            await websocket.close()
    else:
        log.error(f"{websocket.remote_address[0]} - Client Header Error! Connection BLOCKED.")
        await call_result(websocket, "403", "", "", "Forbidden.")
        await websocket.close()

async def main():
    async with websockets.serve(echo, "", 26451, logger=log):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    # 备份日志文件
    if os.path.exists("log/"):
        if os.path.exists("log/current.log"):
            shutil.copyfile("log/current.log", "log/last.log")
        open("log/current.log", "w", encoding="UTF-8")
    else:
        os.mkdir("log/")
        open("log/current.log", 'w', encoding="UTF-8")
    # 输出日志
    log = logging.getLogger("ws")
    log.setLevel(logging.INFO)
    file_handler = logging.FileHandler("log/current.log")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    log.info("Websocket Server launch OK.")
    print("Logger Launch OK.")
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
        log.error("User manually exit.")
        print("User manually exit.")
    except ConnectionError:
        log.error("Connection error.")
        print("Remote user closed a connection unexcepted.")
    except websockets.exceptions.ConnectionClosedError():
        log.error("Websockets Connection Closed Error.")
        print("Remote connection shutdown without closed.")
    except websockets.exceptions.ConnectionClosedOK():
        log.error("Websocket Connection Closed OK.")
        print("Remote connection close OK.")
