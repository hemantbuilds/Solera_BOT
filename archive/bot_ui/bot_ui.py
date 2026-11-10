import pygame
import zmq
import threading
import time

# Adjust these paths to the images you have
IDLE_IMAGE_PATH = "idle_smiley.png"
THINKING_IMAGE_PATH = "thinking_smiley.png"
RESPONSE_IMAGE_PATH = "thumbs_up_smiley.png"

# ZeroMQ addresses
SUB_INPUT_ADDRESS = "tcp://127.0.0.1:5555"   # Input from some publisher
SUB_RESPONSE_ADDRESS = "tcp://127.0.0.1:5556" # Response from another publisher (optional, depending on your design)

# Possible states
STATE_IDLE = "idle"
STATE_THINKING = "thinking"
STATE_RESPONSE = "response"

class RaspiUI:
    def __init__(self):
        pygame.init()

        # Full screen on Raspberry Pi
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("My Fullscreen ZMQ UI")

        self.clock = pygame.time.Clock()

        # Load images
        self.idle_image = pygame.image.load(IDLE_IMAGE_PATH).convert_alpha()
        self.thinking_image = pygame.image.load(THINKING_IMAGE_PATH).convert_alpha()
        self.response_image = pygame.image.load(RESPONSE_IMAGE_PATH).convert_alpha()

        # Current UI state and text
        self.state = STATE_IDLE
        self.last_input = ""
        self.last_response = ""

        # Font for displaying text
        self.font = pygame.font.SysFont("Arial", 32)

        # Start ZMQ in another thread
        self.zmq_thread = threading.Thread(target=self.zmq_listener, daemon=True)
        self.zmq_thread.start()

    def zmq_listener(self):
        """
        Listens on multiple addresses for ZeroMQ messages.
        - If we receive a non-NULL input, switch to THINKING state.
        - If we receive a response, switch to RESPONSE state.
        """
        import zmq

        context = zmq.Context()

        # SUB socket #1 (input)
        socket_input = context.socket(zmq.SUB)
        socket_input.connect(SUB_INPUT_ADDRESS)
        socket_input.setsockopt_string(zmq.SUBSCRIBE, "")

        # SUB socket #2 (response), if needed
        socket_response = context.socket(zmq.SUB)
        socket_response.connect(SUB_RESPONSE_ADDRESS)
        socket_response.setsockopt_string(zmq.SUBSCRIBE, "")

        poller = zmq.Poller()
        poller.register(socket_input, zmq.POLLIN)
        poller.register(socket_response, zmq.POLLIN)

        while True:
            # Poll for messages (1 second timeout)
            events = dict(poller.poll(1000))

            # Handle input messages
            if socket_input in events and events[socket_input] == zmq.POLLIN:
                msg_in = socket_input.recv_string().strip()
                if msg_in.upper() != "NULL":
                    self.last_input = msg_in
                    self.state = STATE_THINKING
            
            # Handle response messages
            if socket_response in events and events[socket_response] == zmq.POLLIN:
                msg_out = socket_response.recv_string().strip()
                if msg_out.upper() != "NULL":
                    self.last_response = msg_out
                    self.state = STATE_RESPONSE
            
            time.sleep(0.05)

    def draw(self):
        """ Draws the current state on the screen. """
        self.screen.fill((0, 0, 0))  # Fill screen with black

        if self.state == STATE_IDLE:
            # Draw idle image in the center
            self.draw_centered(self.idle_image)

        elif self.state == STATE_THINKING:
            # Draw thinking image
            self.draw_centered(self.thinking_image)

            # Display the input text below the image
            text_surface = self.font.render(f"Input: {self.last_input}", True, (255, 255, 255))
            self.draw_text_below_image(text_surface, self.thinking_image)

        elif self.state == STATE_RESPONSE:
            # Draw response image
            self.draw_centered(self.response_image)

            # Display the response text below the image
            text_surface = self.font.render(f"Response: {self.last_response}", True, (255, 255, 255))
            self.draw_text_below_image(text_surface, self.response_image)

        pygame.display.flip()

    def draw_centered(self, image):
        """ Helper to draw an image at the center of the screen. """
        screen_rect = self.screen.get_rect()
        image_rect = image.get_rect(center=screen_rect.center)
        self.screen.blit(image, image_rect)

    def draw_text_below_image(self, text_surface, image):
        """ Helper to draw text below the given image. """
        screen_rect = self.screen.get_rect()
        image_rect = image.get_rect(center=screen_rect.center)
        text_rect = text_surface.get_rect(midtop=(image_rect.centerx, image_rect.bottom + 20))
        self.screen.blit(text_surface, text_rect)

    def run(self):
        """ Main loop. """
        running = True
        while running:
            # Check for quit or ESC key
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            self.draw()
            self.clock.tick(30)  # Limit to 30 FPS

        pygame.quit()

if __name__ == "__main__":
    app = RaspiUI()
    app.run()
