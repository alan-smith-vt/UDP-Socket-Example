import socket
import threading
import time
import struct
from enum import IntEnum
import select
import queue
import json

from networkManager import MessageType, packMessage, send_with_confirmation

#Event for terminating the message receiver thread
stop_event = threading.Event()

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as subSocket:
    listener_port_ip = ('localhost', 12345)
    subSocket.bind(listener_port_ip) #keep the socket in blocking mode since using "select"

    mainSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Main program
    message_queue = queue.Queue()
    sender_port_ip = ('localhost', 12346)
    sender_thread = threading.Thread(target=send_with_confirmation,args=(mainSocket, subSocket, sender_port_ip, message_queue, stop_event))
    sender_thread.start()
    try:
        timestamp = time.time() #floating-point number
        data = {
            "message": "test",
            "timestamp": timestamp
        }
        json_data = json.dumps(data)#json string

        data = packMessage(MessageType.STRING, listener_port_ip, json_data)
        print("Data: %s, %s"%(data[0],data[1]))
        message_queue.put(data)
        time.sleep(3)
    finally:
        stop_event.set()  # Signal the thread to stop
        sender_thread.join()  # Wait for the thread to exit
        mainSocket.close()