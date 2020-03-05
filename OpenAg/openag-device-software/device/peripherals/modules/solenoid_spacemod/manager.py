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
    misting_interval: float # seconds
    prev_reinit_time: float = 0
    reinit_interval: float = 300  # seconds -> every 5 minutes

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize light driver."""

        # Initialize parent class
        super().__init__(*args, **kwargs)


        # Initialize panel and channel configs
        self.config = self.communication

        # Initialize variable names
        self.misting_interval = self.variables["actuator"]["misting_cycle"]

        if self.misting_interval == None:
            self.misting_interval = 60 # misting cycle - defaults to every minute


    def initialize_peripheral(self) -> None:
        """Initializes peripheral."""
        self.logger.info("Initializing")

        # Clear reported values
        self.clear_reported_values()

        # Initialize health
        self.health = 100.0

        # Initialize driver
        try:
            self.driver = driver.LEDSpacemodDriver(
                name=self.name,
                config=self.config,
                i2c_lock=self.i2c_lock,
                simulate=self.simulate,
                mux_simulator=self.mux_simulator,
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
            self.health = (100.0)
        except exceptions.DriverError as e:
            self.logger.exception("Unable to setup")
            self.mode = modes.ERROR
            return


    def update_peripheral(self) -> None:
        """Updates peripheral if misting cycle changes."""

        # Check for misting timeout - must send update to device every misting cycle
        misting_required = False
        if self.misting_interval != None:
            misting_delta = time.time() - self.prev_misting_time
            if misting_delta > self.misting_interval:
                misting_required = True
                self.prev_misting_time = time.time()

        # Write outputs to hardware every misting interval if update isn't inevitable
        if misting_required:
            self.logger.debug("Sending misting signal to solenoid")
            self.driver.check_status()

        # Check if update is required
        if not misting_required:
            return

        # Update latest misting time
        self.prev_misting_time = time.time()

    def clear_reported_values(self) -> None:
        """Clears reported values."""
        self.intensity = None
        self.spectrum = None
        self.distance = None
        self.channel_setpoints = None
        self.prev_desired_intensity = None
        self.prev_desired_spectrum = None
        self.prev_desired_distance = None


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
