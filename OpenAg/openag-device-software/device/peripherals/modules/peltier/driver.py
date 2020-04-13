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

from device.peripherals.modules.spacevac import exceptions


class PeltierDriver():
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
        # self.fan_pin = config.get("fan_pin")
        # self.fan_pin_roots = config.get("fan_pin_roots")
        # self.humidifier_pin = config.get("humidifier_pin")
        # self.heater_pin = config.get("heater_pin")
        self.peltier_pin = config.get("pin")
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

        # if self.fan_pin != None:
        #     self.fan_pin = int(self.fan_pin)

        # if self.fan_pin_roots != None:
        #     self.fan_pin_roots = int(self.fan_pin_roots)

        # if self.humidifier_pin != None:
        #     self.humidifier_pin = int(self.humidifier_pin)

        # if self.heater_pin != None:
        #     self.heater_pin = int(self.heater_pin)    

        if self.peltier_pin != None:
            self.peltier_pin = int(self.peltier_pin)

    def setup_gpio(self) -> None:
        """
        Initialize the gpio line for a button
        """
        # if self.fan_pin != None and self.fan_pin_roots != None and self.humidifier_pin != None and self.heater_pin != None and pi_gpio_available and not self.simulate:
        if self.peltier_pin != None and pi_gpio_available and not self.simulate:
            try:

                GPIO.setmode(GPIO.BOARD)
                # GPIO.setup(self.fan_pin, GPIO.OUT)
                # GPIO.setup(self.fan_pin_roots, GPIO.OUT)
                # GPIO.setup(self.humidifier_pin, GPIO.OUT)
                # GPIO.setup(self.heater_pin, GPIO.OUT)
                GPIO.setup(self.peltier_pin, GPIO.OUT)
                return
            except Exception as e:
                raise exceptions.GPIOSetupError(logger=self.logger) from e


        if not pi_gpio_available and not self.simulate:
            raise exceptions.GPIOSetupError(logger=self.logger)
            

    def cool(self) -> Dict[str, float]:
        if self.peltier_pin != None and pi_gpio_available and not self.simulate:
            """ Cooling """
            try:
                GPIO.output(self.peltier_pin, GPIO.LOW)
                time.sleep(0.1)

                self.logger.debug("Cooling")
                return 1
            except Exception as e:
                raise exceptions.TurnOffError(logger=self.logger) from e
            return 0 # Failed
        else:
            if self.simulate:
                self.logger.debug("Cooling")
                return 1 # Simulating a successful command
            else:
                return 0 #Failed

    def turn_off(self) -> Dict[str, float]:
        if self.peltier_pin != None and pi_gpio_available and not self.simulate:
            """ Turn Off"""
            try:
                GPIO.output(self.peltier_pin, GPIO.LOW)
                time.sleep(0.1)


                self.logger.debug("Turning off the Peltier")
                return 0
            except Exception as e:
                raise exceptions.TurnOffError(logger=self.logger) from e
            return 1 # Failed to reset
        else:
            if self.simulate:
                self.logger.debug("Turning off the Peltier")
                return 0 # Simulating a successful reset
            else:
                return 1 #Failed to reset


