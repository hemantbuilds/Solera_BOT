from flask import Flask, render_template
import zmq
import threading
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

# ZMQ Addresses
START_STOP_IP = "tcp://127.0.0.1:5560"
TRANSCRIBED_IP = "tcp://127.0.0.1:5557"
FINAL_RESPONSE_IP = "tcp://127.0.0.1:5556"
FINISHED_IP = "tcp://127.0.0.1:5569"

def zmq_listener(ip, event_name):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(ip)
    socket.setsockopt_string(zmq.SUBSCRIBE, "")

    while True:
        message = socket.recv_string()
        socketio.emit(event_name, {'message': message})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    threading.Thread(target=zmq_listener, args=(START_STOP_IP, 'start_stop'), daemon=True).start()
    threading.Thread(target=zmq_listener, args=(TRANSCRIBED_IP, 'transcribed'), daemon=True).start()
    threading.Thread(target=zmq_listener, args=(FINAL_RESPONSE_IP, 'final_response'), daemon=True).start()
    threading.Thread(target=zmq_listener, args=(FINISHED_IP, 'finished'), daemon=True).start()

    socketio.run(app, debug=True)
