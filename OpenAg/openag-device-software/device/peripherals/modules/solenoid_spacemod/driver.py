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

from device.peripherals.modules.solenoid_spacemod import exceptions


class SolenoidDriver:
    """Driver for array of led panels controlled by a dac5578."""

    # Initialize var defaults
    is_shutdown: bool = True

    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        i2c_lock: threading.RLock,
        simulate: bool = False,
        mux_simulator: Optional[MuxSimulator] = None,
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

    def setup_gpio(self) -> None:
        """
        Initialize the gpio line for a button
        """
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.OUT)
        return


    def turn_on(self) -> Dict[str, float]:
        """Turns the solenoid on and off"""
        if self.pin != None:
            GPIO.output(self.pin, GPIO.HIGH)
            # Misting on time
            time.sleep(10000)
            GPIO.output(self.pin, GPIO.LOW)


    def turn_off(self) -> Dict[str, float]:
        """Hard reset for the solenoid"""
        if self.pin != None:
            GPIO.output(self.pin, GPIO.LOW)            

    def check_status(self):
        """Device Heartbeat Check"""
        self.turn_on()
        return 1