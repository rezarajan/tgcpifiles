# Import standard python modules
import os, time, threading
try:
    import RPi.GPIO as GPIO
    pi_gpio_available = True
except ImportError:
    pi_gpio_available = False

# Import python types
from typing import NamedTuple, Optional, Tuple, Dict, Any, List

# Import device utilities
from device.utilities import logger, bitwise
from device.utilities.communication.i2c.main import I2C
from device.utilities.communication.i2c.exceptions import I2CError
from device.utilities.communication.i2c.mux_simulator import MuxSimulator

from device.peripherals.modules.led_spacemod import exceptions


class LEDSpacemodDriver:
    """Driver for array of led panels controlled by a dac5578."""

    # Initialize var defaults
    is_shutdown: bool = True

    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        i2c_lock: threading.RLock,
        simulate: bool = False,
        mux_simulator: Optional[MuxSimulator] = None
    ) -> None:
        """Initializes panel."""

        # Initialize panel parameters
        self.name = name
        self.bus = config.get("bus")
        self.mux = config.get("mux")
        self.active_high = config.get("is_active_high")
        self.address = config.get("address")
        self.port = config.get("port")
        self.pin = config.get("pin")
        self.hard_reset_pin = config.get("hard_reset_pin")
        self.i2c_lock = i2c_lock
        self.simulate = simulate
        self.mux_simulator = mux_simulator
        self.is_on = False

        # Initialize logger
        logname = "Driver({})".format(name)
        self.logger = logger.Logger(logname, "peripherals")

        # Check if using default bus
        if self.bus == "default":
            self.logger.debug("Using default i2c bus")
            self.bus = os.getenv("DEFAULT_I2C_BUS")

        # Convert exported value from non-pythonic none to pythonic None
        if self.bus == "none":
            self.bus = None

        if self.bus != None:
            self.bus = int(self.bus)

        # Check if using default mux
        if self.mux == "default":
            self.logger.debug("mux is default")
            self.mux = os.getenv("DEFAULT_MUX_ADDRESS")

        # Convert exported value from non-pythonic none to pythonic None
        if self.mux == "none":
            self.mux = None
        self.logger.debug("mux = {}".format(self.mux))

        # Convert i2c config params from hex to int if they exist
        if self.address != None:
            self.address = int(self.address, 16)
        if self.mux != None:
            self.mux = int(self.mux, 16)

        if self.pin != None:
            self.pin = int(self.pin)

        if self.hard_reset_pin != None:
            self.hard_reset_pin = int(self.hard_reset_pin)    

    def setup_gpio(self) -> None:
        """
        Initialize the gpio line for a button
        """
        if self.pin != None and pi_gpio_available and not self.simulate:
            try:

                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(self.pin, GPIO.OUT)
                GPIO.setup(self.hard_reset_pin, GPIO.OUT)
                return
            except:
                raise exceptions.GPIOSetupError(logger=self.logger)
            

    def turn_on(self) -> Dict[str, float]:
        if self.pin != None and pi_gpio_available and not self.simulate:
            """Sets Soft Latch On"""
            try:
                GPIO.output(self.pin, GPIO.HIGH)
                # Soft Latch RC Time
                time.sleep(0.1)
                GPIO.output(self.pin, GPIO.LOW)

                self.logger.debug("Turning on")
                self.is_on = True
                return 1
            except:
                raise exceptions.TurnOffError(logger=self.logger)
            return 0 # Failed to reset
        else:
            if self.simulate:
                self.logger.debug("Turning on ")
                return 1 # Simulating a successful latch set
            else:
                return 0 #Failed to set latch

    def turn_off(self) -> Dict[str, float]:
        if self.hard_reset_pin != None and pi_gpio_available and not self.simulate:
            """Drains LED Soft Latch - Reset"""
            try:
                GPIO.output(self.hard_reset_pin, GPIO.HIGH)
                # Soft Latch RC Time
                time.sleep(0.1)
                GPIO.output(self.hard_reset_pin, GPIO.LOW)

                self.logger.debug("Turning off")
                self.is_on = False
                return 1
            except:
                raise exceptions.TurnOffError(logger=self.logger)
            return 0 # Failed to reset
        else:
            if self.simulate:
                self.logger.debug("Turning off (hard reset)")
                return 1 # Simulating a successful reset
            else:
                return 0 #Failed to reset

    def toggle(self) -> Dict[str, float]:
            """Toggles LED Soft Latch"""
            if self.pin != None and pi_gpio_available and not self.simulate:
                try:
                    if self.is_on == False:
                        self.logger.debug("Turning on")
                        self.turn_on()
                        return 1
                    elif self.is_on == True:
                        self.logger.debug("Turning off")
                        self.turn_off()
                        return 0
                except:
                    raise exceptions.ToggleError(logger=self.logger)

            
            if self.simulate:
                if self.is_on == False:
                    self.logger.debug("Turning on")
                    self.is_on = True
                    return 1
                elif self.is_on == True:
                    self.logger.debug("Turning off")
                    self.is_on = False
                    return 0

