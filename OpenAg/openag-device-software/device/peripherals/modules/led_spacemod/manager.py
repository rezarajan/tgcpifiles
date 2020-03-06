# Import standard python modules
import threading, time

# Import python types
from typing import Optional, Tuple, Dict, Any

# Import manager elements
from device.peripherals.classes.peripheral import manager, modes
from device.peripherals.modules.led_spacemod import driver, exceptions, events


class LEDSpacemodManager(manager.PeripheralManager):
    """Manages an LED soft latch"""

    prev_desired_intensity: Optional[float] = None
    prev_desired_spectrum: Optional[Dict[str, float]] = None
    prev_desired_distance: Optional[float] = None
    prev_heartbeat_time: float = 0
    heartbeat_interval: float = 60  # seconds -> every minute
    prev_lighting_time: float = 0
    prev_reinit_time: float = 0
    reinit_interval: float = 300  # seconds -> every 5 minutes

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize light driver."""

        # Initialize parent class
        super().__init__(*args, **kwargs)

        # Initialize panel and channel configs
        self.config = self.communication
        self.panel_properties = self.setup_dict.get("properties")

        # Initialize variable names
        self.intensity_name = self.variables["sensor"]["ppfd_umol_m2_s"]
        self.spectrum_name = self.variables["sensor"]["spectrum_nm_percent"]
        self.distance_name = self.variables["sensor"]["illumination_distance_cm"]
        self.channel_setpoints_name = self.variables["actuator"][
            "channel_output_percents"
        ]

        self.lighting_on_name = self.variables["actuator"]["lighting_on_time"]
        self.lighting_off_name = self.variables["actuator"]["lighting_off_time"]
        self.lighting_status_name = self.variables["actuator"]["lighting_status"]

        # Parse panel properties
        self.channel_types = self.panel_properties.get(  # type: ignore
            "channel_types", {}
        )

    @property
    def spectrum(self) -> Any:
        """Gets spectrum value."""
        return self.state.get_peripheral_reported_sensor_value(
            self.name, self.spectrum_name
        )

    @spectrum.setter
    def spectrum(self, value: Optional[Dict[str, float]]) -> None:
        """Sets spectrum value in shared state."""
        self.state.set_peripheral_reported_sensor_value(
            self.name, self.spectrum_name, value
        )
        self.state.set_environment_reported_sensor_value(
            self.name, self.spectrum_name, value, simple=True
        )

    @property
    def desired_spectrum(self) -> Any:
        """Gets desired spectrum value from shared environment state if not 
        in manual mode, otherwise gets it from peripheral state."""
        if self.mode != modes.MANUAL:
            return self.state.get_environment_desired_sensor_value(self.spectrum_name)
        else:
            return self.state.get_peripheral_desired_sensor_value(
                self.name, self.spectrum_name
            )

    @property
    def intensity(self) -> Optional[float]:
        """Gets intensity value."""
        value = self.state.get_peripheral_reported_sensor_value(
            self.name, self.intensity_name
        )
        if value != None:
            return float(value)
        return None

    @intensity.setter
    def intensity(self, value: float) -> None:
        """Sets intensity value in shared state."""
        self.state.set_peripheral_reported_sensor_value(
            self.name, self.intensity_name, value
        )
        self.state.set_environment_reported_sensor_value(
            self.name, self.intensity_name, value, simple=True
        )

    @property
    def desired_intensity(self) -> Optional[float]:
        """Gets desired intensity value from shared environment state if not 
        in manual mode, otherwise gets it from peripheral state."""
        if self.mode != modes.MANUAL:
            value = self.state.get_environment_desired_sensor_value(self.intensity_name)
            if value != None:
                return float(value)
            return None
        else:
            value = self.state.get_peripheral_reported_sensor_value(
                self.name, self.intensity_name
            )
            if value != None:
                return float(value)
            return None

    @property
    def distance(self) -> Optional[float]:
        """Gets distance value."""
        value = self.state.get_peripheral_reported_sensor_value(
            self.name, self.distance_name
        )
        if value != None:
            return float(value)
        return None

    @distance.setter
    def distance(self, value: float) -> None:
        """Sets distance value in shared state."""
        self.state.set_peripheral_reported_sensor_value(
            self.name, self.distance_name, value
        )
        self.state.set_environment_reported_sensor_value(
            self.name, self.distance_name, value, simple=True
        )

    @property
    def desired_distance(self) -> Optional[float]:
        """Gets desired distance value from shared environment state if not 
        in manual mode, otherwise gets it from peripheral state."""
        if self.mode != modes.MANUAL:
            value = self.state.get_environment_desired_sensor_value(self.distance_name)
            if value != None:
                return float(value)
            return None
        else:
            value = self.state.get_peripheral_reported_sensor_value(
                self.name, self.distance_name
            )
            if value != None:
                return float(value)
            return None

    @property
    def channel_setpoints(self) -> Any:
        """Gets channel setpoints value."""
        return self.state.get_peripheral_reported_actuator_value(
            self.name, self.channel_setpoints_name
        )

    @channel_setpoints.setter
    def channel_setpoints(self, value: int) -> None:
        """ Sets channel outputs value in shared state. """
        self.state.set_peripheral_reported_actuator_value(
            self.name, self.channel_setpoints_name, value
        )
        self.state.set_environment_reported_actuator_value(
            self.channel_setpoints_name, value
        )

    @property
    def desired_channel_setpoints(self) -> Any:
        """ Gets desired distance value from shared environment state if not 
            in manual mode, otherwise gets it from peripheral state. """
        if self.mode != modes.MANUAL:
            return self.state.get_environment_desired_actuator_value(
                self.channel_setpoints_name
            )
        else:
            return self.state.get_peripheral_desired_actuator_value(
                self.name, self.channel_setpoints_name
            )

    @property
    def lighting_status(self) -> Any:
        """Gets lighting status value."""
        return

    @lighting_status.setter
    def lighting_status(self, value: Optional[Dict[str, float]]) -> None:
        """Sets lighting status value in shared state."""
        status = "OFF"
        if value == 1:
            status = "ON"
        elif value == 0:
            status = "OFF"
        else:
            status = "INITIALIZING"
        self.state.set_peripheral_reported_sensor_value(
            self.name, self.lighting_status_name, status
        )
        self.state.set_environment_reported_sensor_value(
            self.name, self.lighting_status_name, status, simple=True
        )
        self.logger.debug("Setting Lighting Status to {}".format(status))

    @property
    def desired_lighting_time(self) -> Optional[float]:
        """Gets desired lighting cycle time from shared environment state if not 
        in manual mode, otherwise gets it from peripheral state."""

        if self.lighting_status == 1:
            lighting_mode_name = self.lighting_on_name
        elif self.lighting_status == 0:
            lighting_mode_name = self.lighting_off_name
        else:
            # Initializing, turn on light
            lighting_mode_name = self.lighting_on_name
        if self.mode != modes.MANUAL:
            value = self.state.get_environment_desired_sensor_value(lighting_mode_name)
            if value != None:
                self.logger.info("Desired {} Value {}".format(lighting_mode_name, value))
                return int(value)
            return None
        else:
            value = self.state.get_peripheral_reported_sensor_value(
                self.name, lighting_mode_name
            )
            if value != None:
                return int(value)
            return None

    @property
    def lighting_delta(self) -> Any:
        """Gets spectrum value."""
        return

    @lighting_delta.setter
    def lighting_delta(self, value: Optional[Dict[str, float]]) -> None:
        """Sets spectrum value in shared state."""
        name = self.lighting_off_name
        if self.lighting_status == 1:
            name = self.lighting_on_name
        elif self.lighting_status == 0:
            name = self.lighting_off_name
        else:
            # Initializing, turn on light
            name = self.lighting_on_name

        self.state.set_peripheral_reported_sensor_value(
            self.name, name, value
        )
        self.state.set_environment_reported_sensor_value(
            self.name, name, value, simple=True
        )
        self.logger.debug("Setting Lighting Time Delta to {}".format(value))          

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
            setup_ok = self.driver.turn_off()
            if setup_ok:
                # Turn the lights back on to start
                self.lighting_status = self.driver.toggle()
            self.health = (100.0)
        except exceptions.DriverError as e:
            self.logger.exception("Unable to setup")
            self.mode = modes.ERROR
            return

        # Update reported variables
        self.update_reported_variables()

    def update_peripheral(self) -> None:
        """Updates peripheral if desired spectrum, intensity, or distance value changes."""

        # Initialize update flag
        update_required = False

        # Check for new desired intensity
        if (
            self.desired_intensity != None
            and self.desired_intensity != self.prev_desired_intensity
        ):
            self.logger.info("Received new desired intensity")
            self.logger.debug(
                "desired_intensity = {} Watts".format(self.desired_intensity)
            )
            self.distance = self.desired_distance
            update_required = True

        # Check for new desired spectrum
        if (
            self.desired_spectrum != None
            and self.desired_spectrum != self.prev_desired_spectrum
        ):
            self.logger.info("Received new desired spectrum")
            self.logger.debug("desired_spectrum = {}".format(self.desired_spectrum))
            update_required = True

        # Check for new illumination distance
        if (
            self.desired_distance != None
            and self.desired_distance != self.prev_desired_distance
        ):
            self.logger.info("Received new desired illumination distance")
            self.logger.debug("desired_distance = {} cm".format(self.desired_distance))
            update_required = True

        # Check if all desired values exist:
        all_desired_values_exist = True
        if (
            self.desired_intensity == None
            or self.desired_spectrum == None
            or self.desired_distance == None
        ):
            all_desired_values_exist = False

        # Check for misting timeout - must send update to device every misting cycle
        lighting_change_required = False
        if self.desired_lighting_time != None:
            if self.prev_lighting_time != None:
                self.lighting_delta = time.time() - self.prev_lighting_time
            else:
                # Initializing State
                self.lighting_delta = 0
            if self.lighting_delta != None:
                if self.lighting_delta > self.desired_lighting_time:
                    lighting_change_required = True
                    self.prev_lighting_time = time.time()

        # Write outputs to hardware every misting interval if update isn't inevitable
        if lighting_change_required:
            self.logger.debug("Sending signal to toggle lights")
            self.lighting_status = self.driver.check_status() # 0: off; 1: on
            self.logger.debug("Lighting Status: {}".format(self.lighting_status))
            self.lighting_status = self.driver.toggle()

            # Update latest misting time
            self.prev_lighting_time = time.time()

        # Check if update is required
        if not lighting_change_required:
            return

        # Update prev desired values
        self.prev_desired_intensity = self.desired_intensity
        self.prev_desired_spectrum = self.desired_spectrum
        self.prev_desired_distance = self.desired_distance

        # Update latest heartbeat time
        self.prev_heartbeat_time = time.time()

    def clear_reported_values(self) -> None:
        """Clears reported values."""
        self.intensity = None
        self.spectrum = None
        self.distance = None
        self.channel_setpoints = None
        self.prev_desired_intensity = None
        self.prev_desired_spectrum = None
        self.prev_desired_distance = None
        self.prev_lighting_time = None
        self.lighting_status = None
        self.lighting_delta = None

    def update_reported_variables(self) -> None:
        """Updates reported variables."""
        self.logger.debug("Updating reported variables")

        # Get previously used distance or default setup distance as average of min
        # and max calibrated distances
        if self.distance == None:
            self.distance = 0

        # Get previously used spectrum or default setup spectrum for reference spd
        if self.spectrum != None:
            reference_spectrum = self.spectrum
        else:
            for channel_key, channel_dict in self.channel_types.items():
                reference_spectrum = channel_dict.get("spectrum_nm_percent", {})
                break

    ##### EVENT FUNCTIONS ##############################################################

    def create_peripheral_specific_event(
        self, request: Dict[str, Any]
    ) -> Tuple[str, int]:
        """Processes peripheral specific event."""
        if request["type"] == events.TOGGLE:
            return self.toggle()
        elif request["type"] == events.TURN_OFF:
            return self.turn_off()
        else:
            return "Unknown event request type", 400

    def check_peripheral_specific_events(self, request: Dict[str, Any]) -> None:
        """Checks peripheral specific events."""
        if request["type"] == events.TOGGLE:
            self._toggle()
        elif request["type"] == events.TURN_OFF:
            self._turn_off()
        else:
            message = "Invalid event request type in queue: {}".format(request["type"])
            self.logger.error(message)

    def toggle(self) -> Tuple[str, int]:
        """Pre-processes turn on event request."""
        self.logger.debug("Pre-processing turn on event request")

        # Require mode to be in manual
        if self.mode != modes.MANUAL:
            return "Must be in manual mode", 400

        # Add event request to event queue
        request = {"type": events.TOGGLE}
        self.event_queue.put(request)

        # Successfully turned on
        return "Turning on", 200

    def _toggle(self) -> None:
        """Processes turn on event request."""
        self.logger.debug("Processing turn on event request")

        # Require mode to be in manual
        if self.mode != modes.MANUAL:
            self.logger.critical("Tried to turn on from {} mode".format(self.mode))

        # Turn on driver and update reported variables
        try:
            seld.lighting_status = self.driver.toggle()
            self.update_reported_variables()
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
            self.channel_setpoints = self.driver.turn_off()
            self.update_reported_variables()
        except exceptions.DriverError as e:
            self.mode = modes.ERROR
            message = "Unable to turn off: {}".format(e)
            self.logger.debug(message)
        except:
            self.mode = modes.ERROR
            message = "Unable to turn off, unhandled exception"
            self.logger.exception(message)
