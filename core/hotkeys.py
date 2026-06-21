"""Global emergency-stop listener used while replaying a signature."""

from typing import Callable


class EmergencyStopListener:
    """Listen for Escape even after the user switches to another application."""

    def __init__(self, on_stop: Callable[[], None]):
        self.on_stop = on_stop
        self._listener = None

    def start(self) -> bool:
        if self._listener is not None:
            return True
        try:
            from pynput import keyboard

            def on_press(key):
                if key == keyboard.Key.esc:
                    self.on_stop()
                    return False

            self._listener = keyboard.Listener(on_press=on_press)
            self._listener.daemon = True
            self._listener.start()
            return True
        except Exception as error:
            print(f"无法启用全局 ESC 监听: {error}")
            self._listener = None
            return False

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
