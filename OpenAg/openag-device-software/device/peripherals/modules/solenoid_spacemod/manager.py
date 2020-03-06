# Import standard python modules
import threading, time

# Import python types
from typing import Optional, Tuple, Dict, Any

# Import manager elements
from device.peripherals.classes.peripheral import manager, modes
from device.peripherals.modules.solenoid_spacemod import driver, exceptions, events


class SolenoidManager(manager.PeripheralManager):
    """Manages an Pump Solenoid"""

    prev_misting_time: float = 0
    prev_reinit_time: float = 0
    reinit_interval: float = 300  # seconds -> every 5 minutes

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize light driver."""

        # Initialize parent class
        super().__init__(*args, **kwargs)

        # Initialize panel and channel configs
        self.solenoid_config = self.communication

        # Initialize variable names
        self.misting_cycle_name = self.variables["actuator"]["misting_cycle"]
        self.mister_on_name = self.variables["actuator"]["mister_on_time"]
        # self.misting_solenoid_state = self.variables["actuator"]["misting_solenoid_state"]

    @property
    def misting_interval(self) -> Any:
        """Gets spectrum value."""
        return self.state.get_peripheral_reported_sensor_value(
            self.name, self.misting_cycle_name
        )

    @misting_interval.setter
    def misting_interval(self, value: Optional[Dict[str, float]]) -> None:
        """Sets spectrum value in shared state."""
        self.state.set_peripheral_reported_sensor_value(
            self.name, self.misting_cycle_name, value
        )
        self.state.set_environment_reported_sensor_value(
            self.name, self.misting_cycle_name, value, simple=True
        )
        self.logger.debug("Setting Misting Interval to {}".format(value))

    @property
    def desired_misting_interval(self) -> Optional[float]:
        """Gets desired misting cycle time from shared environment state if not 
        in manual mode, otherwise gets it from peripheral state."""
        if self.mode != modes.MANUAL:
            value = self.state.get_environment_desired_sensor_value(self.misting_cycle_name)
            if value != None:
                self.logger.info("Misting Value {}".format(value))
                return int(value)
            return None
        else:
            value = self.state.get_peripheral_reported_sensor_value(
                self.name, self.misting_cycle_name
            )
            if value != None:
                return int(value)
            return None

    @property
    def misting_on_time(self) -> Any:
        """Gets spectrum value."""
        return self.state.get_peripheral_reported_sensor_value(
            self.name, self.mister_on_name
        )

    @misting_on_time.setter
    def misting_on_time(self, value: Optional[Dict[str, float]]) -> None:
        """Sets spectrum value in shared state."""
        self.state.set_peripheral_reported_sensor_value(
            self.name, self.mister_on_name, value
        )
        self.state.set_environment_reported_sensor_value(
            self.name, self.mister_on_name, value, simple=True
        )
        self.logger.debug("Setting Mister On Time to {}".format(value))

    @property
    def desired_misting_on_time(self) -> Optional[float]:
        """Gets desired misting cycle time from shared environment state if not 
        in manual mode, otherwise gets it from peripheral state."""
        if self.mode != modes.MANUAL:
            value = self.state.get_environment_desired_sensor_value(self.mister_on_name)
            if value != None:
                self.logger.info("Misting On Time Value {}".format(value))
                return int(value)
            return None
        else:
            value = self.state.get_peripheral_reported_sensor_value(
                self.name, self.mister_on_name
            )
            if value != None:
                return int(value)
            return None


    def initialize_peripheral(self) -> None:
        """Initializes peripheral."""
        self.logger.info("Initializing")

        # Clear reported values
        self.clear_reported_values()

        if self.misting_interval == None and self.desired_misting_interval != None:
            self.misting_interval = self.desired_misting_interval
        else:
            self.misting_interval = 600

        if self.misting_on_time == None and self.desired_misting_on_time != None:
            self.misting_on_time = self.desired_misting_on_time
        else:
            self.misting_on_time = 600

        # Initialize health
        self.health = 100.0

        # Initialize driver
        try:
            self.driver = driver.SolenoidDriver(
                name=self.name,
                config=self.solenoid_config,
                i2c_lock=self.i2c_lock,
                simulate=self.simulate,
                mux_simulator=self.mux_simulator,
                on_time=self.misting_on_time
            )
            self.health = (100.0)
        except exceptions.DriverError as e:
            self.logger.exception("Manager unable to initialize")
            self.health = 0.0
            self.mode = modes.ERROR

    def setup_peripheral(self) -> None:
        """Sets up peripheral by turning off the solenoid."""
        self.logger.debug("Setting up")
        try:
            self.driver.turn_off()
            self.state.set_peripheral_reported_actuator_value(
            self.name, self.mister_on_name, self.desired_misting_on_time
            )
            self.state.set_peripheral_reported_actuator_value(
            self.name, self.misting_cycle_name, self.desired_misting_interval
            )
            self.state.set_environment_reported_actuator_value(
                self.misting_on_time, self.desired_misting_on_time
            )
            self.state.set_environment_reported_actuator_value(
                self.misting_cycle_name, self.desired_misting_interval
            )

            self.health = (100.0)

        except exceptions.DriverError as e:
            self.logger.exception("Unable to setup")
            self.mode = modes.ERROR
            return


    def update_peripheral(self) -> None:
        """Updates peripheral if misting cycle changes."""

        # Check for misting timeout - must send update to device every misting cycle
        misting_required = False
        if self.desired_misting_interval != None and self.prev_misting_time != None:
            misting_delta = time.time() - self.prev_misting_time
            if misting_delta > (self.desired_misting_interval + self.desired_misting_on_time):
                misting_required = True
                self.prev_misting_time = time.time()

        # Write outputs to hardware every misting interval if update isn't inevitable
        if misting_required:
            self.logger.debug("Sending misting signal to solenoid")
            self.driver.check_status()

            # Update latest misting time
            self.prev_misting_time = time.time()

        # Check if update is required
        if not misting_required:
            return


    def clear_reported_values(self) -> None:
        """Clears reported values."""
        self.misting_interval = None
        self.misting_on_time = None
        self.prev_misting_time = None


    ##### EVENT FUNCTIONS ##############################################################

    def create_peripheral_specific_event(
        self, request: Dict[str, Any]
    ) -> Tuple[str, int]:
        """Processes peripheral specific event."""
        if request["type"] == events.TURN_ON:
            return self.turn_on()
        elif request["type"] == events.TURN_OFF:
            return self.turn_off()
        else:
            return "Unknown event request type", 400

    def check_peripheral_specific_events(self, request: Dict[str, Any]) -> None:
        """Checks peripheral specific events."""
        if request["type"] == events.TURN_ON:
            self._turn_on()
        elif request["type"] == events.TURN_OFF:
            self._turn_off()
        else:
            message = "Invalid event request type in queue: {}".format(request["type"])
            self.logger.error(message)

    def turn_on(self) -> Tuple[str, int]:
        """Pre-processes turn on event request."""
        self.logger.debug("Pre-processing turn on event request")

        # Require mode to be in manual
        if self.mode != modes.MANUAL:
            return "Must be in manual mode", 400

        # Add event request to event queue
        request = {"type": events.TURN_ON}
        self.event_queue.put(request)

        # Successfully turned on
        return "Turning on", 200

    def _turn_on(self) -> None:
        """Processes turn on event request."""
        self.logger.debug("Processing turn on event request")

        # Require mode to be in manual
        if self.mode != modes.MANUAL:
            self.logger.critical("Tried to turn on from {} mode".format(self.mode))

        # Turn on driver and update reported variables
        try:
            self.driver.turn_on()
            self.state.set_peripheral_reported_actuator_value(
            self.name, self.mister_solenoid_state, "On"
            )
            self.state.set_peripheral_reported_actuator_value(
            self.name, self.misting_cycle_name, self.desired_misting_interval
            )
            self.state.set_environment_reported_actuator_value(
                self.mister_solenoid_state, "On"
            )
            self.state.set_environment_reported_actuator_value(
                self.mister_solenoid_state, self.desired_misting_interval
            )
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
            self.driver.turn_off()
        except exceptions.DriverError as e:
            self.mode = modes.ERROR
            message = "Unable to turn off: {}".format(e)
            self.logger.debug(message)
        except:
            self.mode = modes.ERROR
            message = "Unable to turn off, unhandled exception"
            self.logger.exception(message)
