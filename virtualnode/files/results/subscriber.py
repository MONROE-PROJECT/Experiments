import zmq
import netifaces

# Default 172.17.0.2
# IP = netifaces.ifaddresses('metadata')[netifaces.AF_INET][0]['addr']

context = zmq.Context()
socket = context.socket(zmq.SUB)
#socket.connect("tcp://{}:5556".format(IP))
socket.connect("tcp://172.17.0.2:5556")

#  Empty string is everything
topicfilter = ''
socket.setsockopt(zmq.SUBSCRIBE, topicfilter)

while True:
    string = socket.recv()
    print string
