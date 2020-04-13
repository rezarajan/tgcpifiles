# Import standard python modules
import threading, time

# Import python types
from typing import Optional, Tuple, Dict, Any

# Import manager elements
from device.peripherals.classes.peripheral import manager, modes
from device.peripherals.modules.peltier import driver, exceptions, events


class PeltierManager(manager.PeripheralManager):
    """Manages a Peltier Cooler"""

    prev_heartbeat_time: float = 0
    heartbeat_interval: float = 60  # seconds -> every minute
    prev_reinit_time: float = 0
    reinit_interval: float = 300  # seconds -> every 5 minutes

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize light driver."""

        # Initialize parent class
        super().__init__(*args, **kwargs)

        # Initialize panel and channel configs
        self.config = self.communication

        # Initialize variable names
        self.temperature_name = self.variables["sensor"]["water_temperature_celsius"]
        self.peltier_status_name = self.variables["actuator"]["peltier_status"]



    @property
    def temperature(self) -> Optional[float]:
        """Gets compensation temperature value from shared environment state."""
        value = self.state.get_environment_reported_sensor_value(self.temperature_name)
        if value != None:
            self.logger.debug(float(value))
            return float(value)
        return None

    @property
    def desired_temperature(self) -> Optional[float]:
        """Gets desired distance value from shared environment state if not 
        in manual mode, otherwise gets it from peripheral state."""
        if self.mode != modes.MANUAL:
            value = self.state.get_environment_desired_sensor_value(self.temperature_name)
            if value != None:
                self.logger.debug(float(value))
                return float(value)
            return None
        else:
            value = self.state.get_peripheral_reported_sensor_value(
                self.name, self.temperature_name
            )
            if value != None:
                return float(value)
            return None     

    @property
    def peltier_status(self) -> Any:
        """Gets Peltier status value."""
        value = self.state.get_environment_reported_sensor_value(self.peltier_status_name)
        if value != None:
            self.logger.debug(value)
            return value
        return None
        
    @peltier_status.setter
    def peltier_status(self, value: Optional[Dict[str, float]]) -> None:
        """Sets peltier status value in shared state."""

        status = "OFF"
        if value == 0:
            status = "COOLING OFF"
        elif value == 1:
            status = "COOLING RESERVOIR"

        self.state.set_peripheral_reported_sensor_value(
            self.name, self.peltier_status_name, status
        )
        self.state.set_environment_reported_sensor_value(
            self.name, self.peltier_status_name, status, simple=True
        )
        self.logger.debug("Setting Peltier Status to {}".format(status)) 
   
   
    def initialize_peripheral(self) -> None:
        """Initializes peripheral."""
        self.logger.info("Initializing")

        # Clear reported values
        self.clear_reported_values()

        # Initialize health
        self.health = 100.0

        # Initialize driver
        try:
            self.driver = driver.PeltierDriver(
                name=self.name,
                config=self.config,
                i2c_lock=self.i2c_lock,
                simulate=self.simulate,
                mux_simulator=self.mux_simulator
            )
            self.health = (100.0)
        except exceptions.DriverError as e:
            self.logger.exception("Manager unable to initialize")
            self.health = 0.0
            self.mode = modes.ERROR

    def setup_peripheral(self) -> None:
        """Sets up peripheral by turning off leds."""
        self.logger.debug("Setting up")
        try:
            self.driver.setup_gpio()
            setup_ok = not self.driver.turn_off()
            if setup_ok:
                self.logger.debug("Setup OK")
                self.peltier_status = 0
            self.health = (100.0)
        except exceptions.DriverError as e:
            self.logger.exception("Unable to setup")
            self.mode = modes.ERROR
            return

        # Update reported variables
        # self.update_reported_variables()

    def update_peripheral(self) -> None:
        """Updates peripheral if desired temperature value changes."""

        # Initialize update flag
        cooling_required = False

        # Check for new desired temperature
        if (
            self.temperature != None and self.desired_temperature != None
            and self.temperature > self.desired_temperature + 0.0
        ):
            self.logger.info("Temperature too high, Cooling!")
            cooling_required = True
        

        # Check for misting timeout - must send update to device every misting cycle
        if cooling_required:
                self.logger.debug("Sending signal to cool")
                self.driver.setup_gpio()
                self.peltier_status = self.driver.cool()
        else:
            self.peltier_status = self.driver.turn_off()
            self.logger.debug("Turning off")
            return


    def clear_reported_values(self) -> None:
        """Clears reported values."""


    def update_reported_variables(self) -> None:
        """Updates reported variables."""
        self.logger.debug("Updating reported variables")

    ##### EVENT FUNCTIONS ##############################################################

    def create_peripheral_specific_event(
        self, request: Dict[str, Any]
    ) -> Tuple[str, int]:
        """Processes peripheral specific event."""
        if request["type"] == events.COOL:
            return self.cool()
        elif request["type"] == events.TURN_OFF:
            return self.turn_off()
        else:
            return "Unknown event request type", 400

    def check_peripheral_specific_events(self, request: Dict[str, Any]) -> None:
        """Checks peripheral specific events."""
        if request["type"] == events.COOL:
            self._cool()
        elif request["type"] == events.TURN_OFF:
            self._turn_off()
        else:
            message = "Invalid event request type in queue: {}".format(request["type"])
            self.logger.error(message)


    def cool(self) -> Tuple[str, int]:
        """Pre-processes turn on event request."""
        self.logger.debug("Pre-processing turn on event request")

        # Require mode to be in manual
        if self.mode != modes.MANUAL:
            return "Must be in manual mode", 400

        # Add event request to event queue
        request = {"type": events.COOL}
        self.event_queue.put(request)

        # Successfully turned on
        return "Cooling", 200

    def _cool(self) -> None:
        """Processes turn on event request."""
        self.logger.debug("Processing turn on event request")

        # Require mode to be in manual
        if self.mode != modes.MANUAL:
            self.logger.critical("Tried to turn on from {} mode".format(self.mode))

        # Turn on driver and update reported variables
        try:
            self.driver.setup_gpio()
            self.peltier_status = self.driver.cool()
            # self.update_reported_variables()
        except exceptions.DriverError as e:
            self.mode = modes.ERROR
            message = "Unable to turn on: {}".format(e)
            self.logger.debug(message)
        except:
            self.mode = modes.ERROR
            message = "Unable to turn on, unhandled exception"
            self.logger.exception(message)

   
    def turn_off(self) -> Tuple[str, int]:
        """Pre-processes turn off event request."""
        self.logger.debug("Pre-processing turn off event request")

        # Require mode to be in manual
        if self.mode != modes.MANUAL:
            return "Must be in manual mode", 400

        # Add event request to event queue
        request = {"type": events.TURN_OFF}
        self.event_queue.put(request)

        # Successfully turned off
        return "Turning off", 200

    def _turn_off(self) -> None:
        """Processes turn off event request."""
        self.logger.debug("Processing turn off event request")

        # Require mode to be in manual
        if self.mode != modes.MANUAL:
            self.logger.critical("Tried to turn off from {} mode".format(self.mode))

        # Turn off driver and update reported variables
        try:
            self.driver.setup_gpio()
            self.peltier_status = self.driver.turn_off()
            # self.update_reported_variables()
        except exceptions.DriverError as e:
            self.mode = modes.ERROR
            message = "Unable to turn off: {}".format(e)
            self.logger.debug(message)
        except:
            self.mode = modes.ERROR
            message = "Unable to turn off, unhandled exception"
            self.logger.exception(message)
