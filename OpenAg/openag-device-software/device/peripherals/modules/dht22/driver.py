# Import standard python modules
import time, threading

try:
    import Adafruit_DHT
    import_ok = True
except ImportError:
    import_ok = False

# Import python types
from typing import NamedTuple, Optional, Dict, Any, Tuple

# Import device utilities
from device.utilities import logger, bitwise
from device.utilities.communication.i2c.main import I2C
from device.utilities.communication.i2c.exceptions import I2CError
from device.utilities.communication.i2c.mux_simulator import MuxSimulator

# Import driver elements
from device.peripherals.modules.dht22 import exceptions


class DHT22Driver:
    """Driver for dht22 temperature and humidity sensor."""

    # Initialize variable properties
    min_temperature = -40  # celsius
    max_temperature = 125  # celsius
    min_humidity = 0  # %RH
    max_humidity = 100  # %RH

    def __init__(
        self,
        name: str,
        i2c_lock: threading.RLock,
        bus: int,
        address: int,
        config: Dict[str, Any],
        mux: Optional[int] = None,
        channel: Optional[int] = None,
        simulate: Optional[bool] = False,
        mux_simulator: Optional[MuxSimulator] = None,
    ) -> None:
        """Initializes driver."""

        # Initialize logger
        logname = "Driver({})".format(name)
        self.logger = logger.Logger(logname, "peripherals")

        self.pin = config.get("pin")
        self.simulate = simulate

        if import_ok and not self.simulate:
            try:
                self.DHT_SENSOR = Adafruit_DHT.DHT22
            except:
                raise exceptions.SetupError(logger=self.logger)




    def read_temperature(self, retry: bool = True) -> Optional[float]:
        """ Reads temperature value."""
        self.logger.debug("Reading humidity value from hardware")
        if import_ok and not self.simulate:
            try:
                _, temperature = Adafruit_DHT.read_retry(self.DHT_SENSOR, self.pin)

                # Verify temperature value within valid range
                if temperature > self.min_temperature and temperature < self.min_temperature:
                    self.logger.warning("Temperature outside of valid range")
                    return None

                # Successfully read temperature
                self.logger.debug("Temperature: {} C".format(temperature))
                return temperature
            except:
                    raise exceptions.ReadTemperatureError(logger=self.logger)
        else:
            temperature = 27.0
            self.logger.debug("Temperature: {} C".format(temperature))
            return temperature

    def read_humidity(self, retry: bool = True) -> Optional[float]:
        """Reads humidity value."""
        self.logger.debug("Reading humidity value from hardware")
        if import_ok and not self.simulate:
            try:
                humidity, _ = Adafruit_DHT.read_retry(self.DHT_SENSOR, self.pin)

                # Verify humidity value within valid range
                if humidity > self.min_humidity and humidity < self.min_humidity:
                    self.logger.warning("Humidity outside of valid range")
                    return None

                # Successfully read humidity
                self.logger.debug("Humidity: {} %".format(humidity))
                return humidity
            except:
                    raise exceptions.ReadHumidityError(logger=self.logger)
        else:
            humidity = 61.0
            self.logger.debug("Humidity: {} %".format(humidity))
            return humidity


    def reset(self, retry: bool = True) -> Optional[float]:
        """Reads humidity value."""
        self.logger.debug("Resetting")
        if import_ok and not self.simulate:
            try:
                self.DHT_SENSOR = Adafruit_DHT.DHT22
                self.logger.debug("Reset Successful")
            except:
                raise exceptions.SetupError(logger=self.logger)
        else:
            self.logger.debug("Reset Successful")

            
