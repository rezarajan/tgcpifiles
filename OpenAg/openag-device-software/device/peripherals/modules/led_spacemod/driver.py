# Import standard python modules
import os, time, threading
import RPi.GPIO as GPIO

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
        simulate: bool,
        mux_simulator: Optional[MuxSimulator],
        logger: logger.Logger,
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

    def setup_gpio(self) -> None:
        """
        Initialize the gpio line for a button
        """
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.OUT)
        return


    def toggle(self) -> Dict[str, float]:
        """Toggles LED Soft Latch"""
        GPIO.output(self.pin, GPIO.HIGH)
        # Soft Latch RC Time
        time.sleep(0.1)
        GPIO.output(self.pin, GPIO.LOW)

    def turn_on(self) -> Dict[str, float]:
        """Toggles LED Soft Latch On"""
        if self.is_on == False:
            self.toggle()
            self.logger.debug("Turning on")
            self.is_on = True
            return 100

    def turn_off(self) -> Dict[str, float]:
        """Toggles LED Soft Latch Off"""
        if self.is_on == True:
            self.toggle()
            self.logger.debug("Turning off")
            self.is_on = False
            return 0

    def check_status(self):
        """Device Heartbeat Check"""
        if self.is_on == True:
            return 1
        if self.is_on == False:
            return 0
