import threading
import time
import queue

from networkManager import MessageType, message_receiver, parse_message

# Use a queue as a shared memory buffer. ~20x faster than a deque
message_queue = queue.Queue()

#Event for terminating the message receiver thread
stop_event = threading.Event()

port_ip = ('localhost', 12346)
recv_thread = threading.Thread(target=message_receiver, args=(port_ip, message_queue, stop_event))
recv_thread.start()

startTime = time.time()

#Catch errors in the parse message function and exit threads safely
try:
    while time.time()-startTime < 10:#seconds
        #catch the queue.Empty error that it returns when no data available
        try:
            data = message_queue.get(timeout=0.1)
            parse_message(data)
        except queue.Empty:
            continue

finally:
    stop_event.set()  # Signal the thread to stop
    recv_thread.join()  # Wait for the thread to exit