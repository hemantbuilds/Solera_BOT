import pyfiglet
import curses
import zmq
import time
import threading
from PIL import Image
from art import *
from pathlib import Path

# ZMQ Addresses
START_STOP_IP = "tcp://127.0.0.1:5560"
TRANSCRIBED_IP = "tcp://127.0.0.1:5557"
FINAL_RESPONSE_IP = "tcp://127.0.0.1:5556"
FINISHED_IP = "tcp://127.0.0.1:5569"

# Global variables
current_mode = "IDLE"  # Modes: IDLE, LISTENING, RESPONDING
ui_lock = threading.Lock()  # Thread-safe UI updates


def zmq_listener(stdscr, ip, callback):
    """
    Listens for messages on a ZMQ socket and triggers a callback with the message.
    """
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(ip)
    socket.setsockopt_string(zmq.SUBSCRIBE, "")

    while True:
        message = socket.recv_string()
        callback(stdscr, message)


def start_signal_handler(stdscr, message):
    """
    Handles START and STOP signals.
    """
    global current_mode
    with ui_lock:
        if message == "START" and current_mode == "IDLE":
            current_mode = "LISTENING"
            draw_ui(stdscr, "Listening...")
            play_tun_dun()
        elif message == "STOP" and current_mode == "LISTENING":
            current_mode = "TRANSCRIBING"
            draw_ui(stdscr, "Transcribing...")


def transcribed_message_handler(stdscr, message):
    """
    Handles final transcribed message.
    """
    global current_mode
    with ui_lock:
        #if current_mode == "TRANSCRIBING":
        if current_mode in ["TRANSCRIBING", "LISTENING"]:
            #message= "zinda hun !!"
            display_typing_effect(stdscr, message, start_y=8)
            current_mode = "RESPONDING"


def final_response_handler(stdscr, message):
    """
    Handles final filtered response.
    """
    global current_mode
    with ui_lock:
        #if current_mode == "RESPONDING":
        if current_mode in ["TRANSCRIBING", "LISTENING", "RESPONDING"]:
            display_typing_effect(stdscr, message, start_y=10)


def finished_handler(stdscr, message):
    """
    Handles 'Finished' signal.
    """
    global current_mode
    with ui_lock:
        if message == "Finished":
            current_mode = "IDLE"
            draw_ui(stdscr, "SOLERA BOT !!")


def play_tun_dun():
    """
    Plays a sound when 'START' is received.
    """
    import os
    os.system('play -nq -t alsa synth 0.1 sine 440 vol 0.5')


def display_typing_effect(stdscr, text, delay=0.05, start_y=8):
    """
    Displays text on the terminal as if someone is typing.
    """
    height, width = stdscr.getmaxyx()
    start_x = max(0, (width - len(text)) // 2)

    y, x = start_y, start_x
    for char in text:
        stdscr.addstr(y, x, char)
        x += 1
        if x >= width - 2:
            x = start_x
            y += 1
        stdscr.refresh()
        time.sleep(delay)

    stdscr.refresh()


def draw_ui(stdscr, status_message):
    """
    Draws the main UI with an image instead of ASCII art.
    """
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    # Load and display the image
    image_path = Path('idle_smiley.png')
    if image_path.exists():
        print("Image found")
        # Convert image to ASCII art
        img = Image.open(image_path)
        # Resize image to fit terminal
        new_width = min(width - 4, 80)
        ratio = new_width / img.size[0]
        new_height = int(img.size[1] * ratio * 0.5)  # 0.5 to account for terminal character aspect ratio
        img = img.resize((new_width, new_height))
        
        # Convert to ASCII art
        ascii_art = text2art("SOLERA BOT")  # Fallback to text art
        
        # Calculate starting position
        lines = ascii_art.splitlines()
        start_y = max(0, (height - len(lines)) // 2)
        if status_message == "Listening...":
            start_y -= 3

        # Display the ASCII art
        for i, line in enumerate(lines):
            if start_y + i < height:
                stdscr.addstr(start_y + i, 2, line[:width-4])

        # Add status message
        status_y = start_y + len(lines) + 1
        status_x = max(0, (width - len(status_message) - 8) // 2)
        if status_y < height:
            stdscr.addstr(status_y, status_x, f"Status: {status_message}", curses.A_BOLD)
    else:
        print("Image not found")
        # Fallback to text if image is not found
        message = "SOLERA BOT"
        stdscr.addstr(height//2, (width - len(message))//2, message)
        status_y = height//2 + 1
        status_x = (width - len(status_message) - 8) // 2
        stdscr.addstr(status_y, status_x, f"Status: {status_message}", curses.A_BOLD)

    stdscr.refresh()


def main(stdscr):
    """
    Main UI loop.
    """
    curses.curs_set(0)
    draw_ui(stdscr, "SOLERA BOT !!")

    threading.Thread(target=zmq_listener, args=(stdscr, START_STOP_IP, start_signal_handler), daemon=True).start()
    threading.Thread(target=zmq_listener, args=(stdscr, TRANSCRIBED_IP, transcribed_message_handler), daemon=True).start()
    threading.Thread(target=zmq_listener, args=(stdscr, FINAL_RESPONSE_IP, final_response_handler), daemon=True).start()
    threading.Thread(target=zmq_listener, args=(stdscr, FINISHED_IP, finished_handler), daemon=True).start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    curses.wrapper(main)
