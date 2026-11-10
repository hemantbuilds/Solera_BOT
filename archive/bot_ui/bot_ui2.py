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
current_mode = "IDLE"  # Modes: IDLE, LISTENING, TRANSCRIBING, RESPONDING
ui_lock = threading.Lock()  # Thread-safe UI updates
transcribed_text = ""  # To store the transcribed message
response_text = ""  # To store the final response


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
        if message == "START" and current_mode in ["IDLE", "RESPONDING"]:
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
    global transcribed_text, current_mode
    with ui_lock:
        if current_mode in ["TRANSCRIBING", "RESPONDING"]:
            transcribed_text = message
            draw_ui(stdscr, "Transcribing...")  # Update the UI
            display_message(stdscr, message, start_y=10, label="You: ")
            current_mode = "RESPONDING"


def final_response_handler(stdscr, message):
    """
    Handles final filtered response.
    """
    global response_text, current_mode
    with ui_lock:
        if current_mode == "RESPONDING":
            response_text = message
            draw_ui(stdscr, "Responding...")  # Update the UI
            display_message(stdscr, message, start_y=12, label="Bot: ")


def finished_handler(stdscr, message):
    """
    Handles 'Finished' signal.
    """
    global current_mode
    with ui_lock:
        if message == "Finished":
            current_mode = "IDLE"
            draw_ui(stdscr, "SOLERA BOT !!")  # Reset UI to initial state


def play_tun_dun():
    """
    Plays a sound when 'START' is received.
    """
    import os
    os.system('play -nq -t alsa synth 0.1 sine 440 vol 0.5')


def display_message(stdscr, text, start_y=10, label=""):
    """
    Displays a message immediately below the SOLERA BOT !! banner.
    """
    height, width = stdscr.getmaxyx()
    start_x = 4

    # Print the label before the text
    if label:
        stdscr.addstr(start_y, start_x, label, curses.A_BOLD)
        start_x += len(label)

    # Clear the line and print the message
    stdscr.move(start_y, start_x)
    stdscr.clrtoeol()
    stdscr.addstr(start_y, start_x, text[:width - start_x - 1])

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

    # Display status at the bottom
    stdscr.addstr(height - 1, 2, f"Status: {status_message}", curses.A_BOLD)

    # Reserve space for the transcribed text and response
    stdscr.addstr(8, 4, "Transcribed Text:", curses.A_UNDERLINE)
    stdscr.addstr(10, 4, "You: ", curses.A_BOLD)
    stdscr.addstr(12, 4, "Bot: ", curses.A_BOLD)

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

