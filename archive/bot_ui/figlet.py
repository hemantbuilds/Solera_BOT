import pyfiglet
import curses

def main(stdscr):
    # Clear the screen
    stdscr.clear()

    # Generate ASCII art for "SOLERA BOT !!"
    ascii_art = pyfiglet.figlet_format("SOLERA_BOT !!", font="slant")

    # Get screen dimensions
    height, width = stdscr.getmaxyx()

    # Ensure terminal is large enough
    if height < 10 or width < 40:
        stdscr.addstr(0, 0, "Terminal too small! Resize and try again.")
        stdscr.refresh()
        stdscr.getch()
        return

    # Draw the boundaries using ASCII characters
    for x in range(0, width - 1):  # Leave the last column for safety
        stdscr.addch(0, x, '-')  # Top border
        stdscr.addch(height - 2, x, '-')  # Bottom border

    for y in range(0, height - 1):  # Leave the last row for safety
        stdscr.addch(y, 0, '|')  # Left border
        stdscr.addch(y, width - 2, '|')  # Right border

    # Add corner decorations safely
    stdscr.addch(0, 0, '+')  # Top-left corner
    if width > 1:
        stdscr.addch(0, width - 2, '+')  # Top-right corner
    if height > 1:
        stdscr.addch(height - 2, 0, '+')  # Bottom-left corner
        if width > 1:
            stdscr.addch(height - 2, width - 2, '+')  # Bottom-right corner

    # Calculate the starting position to center the ASCII art
    lines = ascii_art.splitlines()
    start_y = max(1, (height - len(lines)) // 2)  # Leave space for top border
    start_x = max(1, (width - max(len(line) for line in lines)) // 2)  # Leave space for side borders

    # Display the ASCII art line by line
    for i, line in enumerate(lines):
        if start_y + i < height - 2:  # Ensure the line fits in the terminal
            stdscr.addstr(start_y + i, start_x, line[:width - 3])  # Trim line to fit width safely

    # Refresh the screen to show changes
    stdscr.refresh()

    # Wait for a key press (optional)
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)
