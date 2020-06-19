# Import standard python libraries
import os, sys

# Set system path
sys.path.append(os.environ["PROJECT_ROOT"])

# Import run peripheral parent class
from device.peripherals.classes.peripheral.scripts.run_manager import ManagerRunnerBase

# Import peripheral manager
from device.peripherals.modules.led_spacemod.manager import LEDSpacemodManager


class ManagerRunner(ManagerRunnerBase):  # type: ignore
    """Runs manager."""

    # Initialize manager class
    Manager = LEDSpacemodManager

    # Initialize defaults
    default_device = "spacefarmers"
    default_name = "LEDPanel-Side"


# Run main
if __name__ == "__main__":
    runner = ManagerRunner()
    runner.run()
