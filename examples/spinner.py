"""Simple spinner utility for displaying loading indicators."""
import sys
import time
import threading


class Spinner:
    """A simple spinner that can be started and stopped."""
    
    def __init__(self, message: str = "Loading...", chars: str = "|/-\\", delay: float = 0.1):
        """
        Initialize a spinner.
        
        Args:
            message: The message to display before the spinner
            chars: Characters to cycle through for the spinner
            delay: Delay between character changes in seconds
        """
        self.message = message
        self.chars = chars
        self.delay = delay
        self.stop_event = threading.Event()
        self.thread = None
    
    def start(self):
        """Start the spinner in a background thread."""
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the spinner and clean up the display."""
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        # Clear the spinner line
        sys.stdout.write("\r" + " " * (len(self.message) + 3) + "\r")
        sys.stdout.flush()
    
    def _spin(self):
        """Internal method that runs the spinner animation."""
        i = 0
        while not self.stop_event.is_set():
            sys.stdout.write(f"\r{self.message} {self.chars[i % len(self.chars)]}")
            sys.stdout.flush()
            time.sleep(self.delay)
            i += 1
    
    def __enter__(self):
        """Context manager entry - starts the spinner."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stops the spinner."""
        self.stop()
        return False

