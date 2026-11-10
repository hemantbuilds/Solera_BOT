#!/usr/bin/env python3
"""ZMQ agent processor — forwards transcripts to the SendAI / Agent Kit API."""

import os
import re
import time
from pathlib import Path

import requests
import zmq
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

API_URL = os.getenv(
    "AGENT_API_URL",
    "https://express-agent-kit.onrender.com/api/chat",
)
SUB_ADDRESS = "tcp://127.0.0.1:5557"
PUB_ADDRESS = "tcp://127.0.0.1:5556"


def filter_response_text(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"[^\w\s\.,!\?\-]", "", text)
    return text.strip()


def main() -> None:
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect(SUB_ADDRESS)
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

    pub_socket = context.socket(zmq.PUB)
    pub_socket.bind(PUB_ADDRESS)

    session = requests.Session()
    print(f"Processor listening on {SUB_ADDRESS}, publishing to {PUB_ADDRESS}")
    print(f"Agent API: {API_URL}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            incoming_msg = sub_socket.recv_string().strip()
            if not incoming_msg or incoming_msg.upper() == "NULL":
                continue

            print(f"Received: '{incoming_msg}'. Calling API...")
            pub_socket.send_string("Thinking")

            try:
                start_time = time.time()
                response = session.post(
                    API_URL, json={"message": incoming_msg}, timeout=10
                )
                elapsed = time.time() - start_time

                if response.status_code == 200:
                    api_text = str(response.json())
                    filtered = filter_response_text(api_text)
                    print(f"Raw ({elapsed:.2f}s): {api_text}")
                    print(f"Filtered: {filtered}")
                    pub_socket.send_string(filtered)
                else:
                    print(f"API HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"API call error: {e}")

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        sub_socket.close()
        pub_socket.close()
        session.close()
        context.term()


if __name__ == "__main__":
    main()
