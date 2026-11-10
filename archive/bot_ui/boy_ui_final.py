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
        if current_mode in ["TRANSCRIBING", "LISTENING"]:
            display_text(stdscr, message, position="above")


def final_response_handler(stdscr, message):
    """
    Handles final filtered response.
    """
    global current_mode
    with ui_lock:
        if current_mode in ["RESPONDING", "TRANSCRIBING", "LISTENING"]:
            display_text(stdscr, message, position="below")


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


def display_text(stdscr, text, position):
    """
    Displays text either above or below the "SOLERA BOT" banner.
    """
    height, width = stdscr.getmaxyx()

    if position == "above":
        # Display transcribed text above the banner
        start_y = max(1, height // 2 - 8)
    elif position == "below":
        # Display response text below the banner and status line
        start_y = height // 2 + 6
    else:
        return

    stdscr.move(start_y, 2)
    stdscr.clrtoeol()
    stdscr.addstr(start_y, 2, text[:width - 4])  # Limit text to screen width
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
