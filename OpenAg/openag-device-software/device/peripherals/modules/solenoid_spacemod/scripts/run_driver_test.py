# Import standard python modules
import os, time, threading
try:
    import RPi.GPIO as GPIO
except ImportError:
    pi_gpio_available = False


class SolenoidDriver:
    """Driver for array of led panels controlled by a dac5578."""

    def __init__(self):
        """Initializes panel."""

        # Initialize soenoid parameters
        self.pin = 16
        self.hard_reset_pin = 22
        self.is_on = False
        GPIO.cleanup()

    def setup_gpio(self):
        """
        Initialize the gpio line for a button
        """
        if self.pin != None:
            try:

                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(self.pin, GPIO.OUT)
                return
            except:
                print(e)
                GPIO.cleanup()


    def toggle(self):
        """Toggles LED Soft Latch"""
        if self.pin != None:
            try:
                GPIO.output(self.pin, GPIO.HIGH)
                # Soft Latch RC Time
                time.sleep(10)
                GPIO.output(self.pin, GPIO.LOW)
                time.sleep(5)

            except Exception as e:
                print(e)
                GPIO.cleanup()


if __name__ == "__main__":
    run = SolenoidDriver()
    run.__init__()
    run.setup_gpio()
    while True:
        run.toggle()