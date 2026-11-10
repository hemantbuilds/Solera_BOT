#!/usr/bin/env python3
"""Flask + Socket.IO web UI that mirrors Solera_BOT ZMQ events."""

import threading

import zmq
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

START_STOP_IP = "tcp://127.0.0.1:5560"
TRANSCRIBED_IP = "tcp://127.0.0.1:5557"
FINAL_RESPONSE_IP = "tcp://127.0.0.1:5556"
FINISHED_IP = "tcp://127.0.0.1:5569"


def zmq_listener(ip: str, event_name: str) -> None:
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(ip)
    socket.setsockopt_string(zmq.SUBSCRIBE, "")

    while True:
        message = socket.recv_string()
        socketio.emit(event_name, {"message": message})


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    threading.Thread(
        target=zmq_listener, args=(START_STOP_IP, "start_stop"), daemon=True
    ).start()
    threading.Thread(
        target=zmq_listener, args=(TRANSCRIBED_IP, "transcribed"), daemon=True
    ).start()
    threading.Thread(
        target=zmq_listener, args=(FINAL_RESPONSE_IP, "final_response"), daemon=True
    ).start()
    threading.Thread(
        target=zmq_listener, args=(FINISHED_IP, "finished"), daemon=True
    ).start()

    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
