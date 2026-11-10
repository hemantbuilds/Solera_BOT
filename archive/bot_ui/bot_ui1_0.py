import pyfiglet
import curses
import zmq
import time
import threading

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
    Draws the main UI with SOLERA BOT at the center or slightly upward.
    """
    stdscr.clear()

    ascii_art = pyfiglet.figlet_format("SOLERA BOT !!", font="slant")
    height, width = stdscr.getmaxyx()

    lines = ascii_art.splitlines()
    start_y = max(0, (height - len(lines)) // 2)
    if status_message == "Listening...":
        start_y -= 3

    start_x = max(0, (width - max(len(line) for line in lines)) // 2)

    # Display ASCII art
    for i, line in enumerate(lines):
        stdscr.addstr(start_y + i, start_x, line[:width - 1])

    # Add a status message below the ASCII art
    stdscr.addstr(start_y + len(lines) + 2, start_x, f"Status: {status_message}", curses.A_BOLD)

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
