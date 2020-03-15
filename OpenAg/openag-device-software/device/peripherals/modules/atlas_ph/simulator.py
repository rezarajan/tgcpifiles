# Import python types
from typing import Any, Dict

# Import device utilities
from device.utilities.bitwise import byte_str

# Import simulator base clase
from device.peripherals.classes.atlas.simulator import AtlasSimulator, ATLAS_SUCCESS_31


class AtlasPHSimulator(AtlasSimulator):  # type: ignore
    """Simulates communication with sensor."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """ Initializes simulator."""

        # Initialize parent class
        super().__init__(*args, **kwargs)

        self.registers: Dict = {}

        # Initialize write and response bytes
        PH_WRITE_BYTES = bytes([0x52, 0x00])
        PH_RESPONSE_BYTES = bytes(
            [
                0x01,
                0x34,
                0x2E,
                0x30,
                0x30,
                0x31,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )
        self.writes[byte_str(PH_WRITE_BYTES)] = PH_RESPONSE_BYTES

        PH_TEMP_COMPENSATION_WRITE_BYTES = bytes([0x54, 0x2C, 0x32, 0x32, 0x2E, 0x39, 0x37, 0x00])
        PH_TEMP_COMPENSATION_RESPONSE_BYTES = ATLAS_SUCCESS_31

        
        self.writes[
            byte_str(PH_TEMP_COMPENSATION_WRITE_BYTES)
        ] = PH_TEMP_COMPENSATION_RESPONSE_BYTES
