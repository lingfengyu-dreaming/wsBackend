# encoding=utf8
"""
Author Lingfengyu
Date 2024-07-21 10:35
LastEditors Lingfengyu
LastEditTime 2024-08-02 14:30
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
        # log.debug(f"{websocket.remote_address[0]} - Connection receive:{rec}")
        if 'image' in rec and rec["image"] is not "":
            try:
                with open("image/image.jpg", "wb") as image_file:
                    image_file.write(base64.b64decode(rec["image"]))
                    # log.debug(f"{websocket.remote_address[0]} - Image decode:{base64.b64decode(rec["image"])}")
            except (binascii.Error, ValueError):
                log.error(f"{websocket.remote_address[0]} - Image error.")
                await call_result(websocket, "400", "", "", "Bad request.")
                return
        else:
            log.error(f"{websocket.remote_address[0]} - Image missing.")
            await call_result(websocket, "400", "", "", "Bad request.")
            return
        char, score = test_model()
        print(f"Char:{char}, Score:{score}")
        if char == -1:
            log.error(f"{websocket.remote_address[0]} - Server internal error")
            if score == -1:
                log.error("ERROR TYPE :-: Torch Device Error.")
            elif score == -2:
                log.error("ERROR TYPE :-: Getdata Error.")
            elif score == -3:
                log.error("ERROR TYPE :-: Image Empty Error.")
            elif score == -4:
                log.error("ERROR TYPE :-: Load Dataset & Model Error.")
            elif score == -5:
                log.error("ERROR TYPE :-: Predict Result Error.")
            elif score == -6:
                log.error("ERROR TYPE :-: Convert Char Error.")
            elif score == -7:
                log.error("ERROR TYPE :-: Torch Grad Error & Break Out For Error.")
            await call_result(websocket, "500", "", "", "An error occured in server.")
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
    log.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler("log/current.log")
    file_handler.setLevel(logging.DEBUG)
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
    # ***好多异常
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.error("User manually exit.")
        print("User manually exit. Everything OK.")
    except ConnectionError as e:
        log.warn(type(e).__name__)
        log.error("Connection error.")
        print("Remote user closed a connection unexcepted.")
    except websockets.exceptions.ConnectionClosedError() as e:
        log.warn(type(e).__name__)
        log.error("Websockets Connection Closed Error.")
        print("Remote connection shutdown without closed.")
    except websockets.exceptions.ConnectionClosedOK() as e:
        log.warn(type(e).__name__)
        log.error("Websocket Connection Closed OK.")
        print("Remote connection close OK.")
    except asyncio.exceptions.IncompleteReadError() as e:
        log.warn(type(e).__name__)
        log.error("Connection closed without receiving or sending a close frame.")
        print("Connection closed without receiving or sending a close frame.")
    except json.JSONDecodeError() as e:
        log.warn(type(e).__name__)
        log.error("Decode JSON from received message error. May caused by Internal Error.")
        print("Decode JSON from received message error.")
