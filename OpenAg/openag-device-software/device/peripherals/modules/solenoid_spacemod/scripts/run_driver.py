# Import standard python modules
import os, sys, threading

# Import python types
from typing import Any

# Set system path
sys.path.append(os.environ["PROJECT_ROOT"])

# Import run peripheral parent class
from device.peripherals.classes.peripheral.scripts.run_peripheral import RunnerBase

# Import driver
from device.peripherals.modules.solenoid_spacemod.driver import SolenoidDriver


class DriverRunner(RunnerBase):  # type: ignore
    """Runs driver."""

    # Initialize defaults
    default_device = "spacefarmers"
    default_name = "Mister Solenoid Actuator"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initializes run driver."""

        # Initialize parent class
        super().__init__(*args, **kwargs)

        # Initialize parser
        self.parser.add_argument("--on", action="store_true", help="turn on solenoid")
        self.parser.add_argument("--off", action="store_true", help="turn off leds")

    def run(self, *args: Any, **kwargs: Any) -> None:
        """Runs driver."""

        # Run parent class
        super().run(*args, **kwargs)

        # Initialize panel variables
        self.config = self.communication

        # Initialize driver
        self.driver = SolenoidDriver(
            name=self.args.name,
            i2c_lock=threading.RLock(),
            config=self.config
        )

        # Check if setting a channel to a value
        if self.args.on != None:
            self.driver.turn_on()

        # Check if turning off
        elif self.args.off:
            self.driver.turn_off()


# Run main
if __name__ == "__main__":
    dr = DriverRunner()
    dr.run()
