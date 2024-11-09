import socket
import threading
import time
import struct
from enum import IntEnum
import select
import queue
import json

# Define the message types using an enum
class MessageType(IntEnum):
	STRING = 1
	COORDINATES = 2

# Pack a message of the format: Message Type, Own port number, string data
def packMessage(messageType, port_ip, json_data):
	data_length = len(json_data)
	portNumber = port_ip[1]
	data = struct.pack('BH%ds'%data_length, messageType, portNumber, json_data.encode())
	attempts = 0
	return (data, attempts)

# Message sending thread that monitors a queue and sends any messages added to it
def send_with_confirmation(mainSocket, subSocket, port_ip, message_queue, stop_event):
	print("Send thread started")
	MAX_ATTEMPTS = 3
	while not stop_event.is_set():
		try:
			(data, attempts) = message_queue.get(timeout=0.1)  # Wait for a message
			print(f"Sending message: {data}")
			mainSocket.sendto(data, port_ip)

			# Wait for confirmation
			#   100ms of overhead between messages may be excessive but start with this to be safe
			time.sleep(0.1)
			ready = select.select([subSocket], [], [], 0.01)
			if ready[0]:
				confirmation, _ = subSocket.recvfrom(1)  # Assume 1 byte for confirmation
				if confirmation == b'\x01':
					print("Confirmation received!")
			else:
				print("No confirmation received, will resend later.")
				attempts = attempts + 1
				if attempts < MAX_ATTEMPTS:
					message_queue.put((data, attempts))  # Re-add message to the queue for later sending

		except queue.Empty:
			continue  # Continue waiting for messages

# Message recieving thread that appends message data to a queue and replies with confirmation
def message_receiver(port_ip, message_queue, stop_event):
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as mainSocket:
		mainSocket.bind(port_ip) #keep the socket in blocking mode since using "select"
		print("Binding mainSocket on %d."%port_ip[1])
		print("Checking for data every 1 ms with select")
		try:
			#Initialize the sending socket for future stuff
			sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			while not stop_event.is_set():
				ready_to_read, _, _ = select.select([mainSocket],[],[],0.001)
				if ready_to_read:
					data, _ = mainSocket.recvfrom(1024)  # Buffer size of 1024 bytes
					print("Data received: %s"%data)
					portNumber = struct.unpack('H',data[2:4])[0] #Use struct to avoid big/little endian issues
					message_queue.put(data)
					print("Sending confirmation to %s,%s"%('localhost', portNumber))
					sendSocket.sendto(bytes([1]), ('localhost',portNumber))

		#Finally seems to be called both at error and natural termination
		finally:
			sendSocket.close()
			print("Send socket has been closed.")
		print("Program has terminated.")

# Parse the message based on the specified message type
def parse_message(data):
	messageType = data[0]
	if messageType == MessageType.STRING:
		jsonData = json.loads(data[4:].decode())
		timestamp = jsonData["timestamp"]
		timenow = time.time()
		delta = timenow-timestamp

		print("Timestamp: %s"%timestamp)
		print("Message: %s"%jsonData["message"])	
		print("Timenow: %s"%timenow)
		print("Latency: %s"%delta)

	elif messageType == MessageType.COORDINATES:
		pass#Add your custom message types here

	else:
		print("Unsupported message type. %d"%messageType)