import time
from gpiozero import LED

__all__ = ['StatusLeds']


class StatusLedsCtx:
    def __init__(self, led_yellow):
        self.led_yellow = led_yellow

    def __enter__(self, *args):
        self.led_yellow.on()
        return None

    def __exit__(self, *args):
        self.led_yellow.off()


class StatusLeds:
    def __init__(self):
        self.led_yellow = LED(23)
        self.led_green = LED(24)
        self.led_green.off()
        self.led_yellow.off()

    def enter_new_person(self):
        return StatusLedsCtx(self.led_yellow)

    def blink_ok(self):
        self.led_green.on()
        time.sleep(1)
        self.led_green.off()
