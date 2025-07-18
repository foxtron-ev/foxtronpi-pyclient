import logging
from dataclasses import dataclass, fields, asdict
import os
from enum import Enum
from udsoncan.exceptions import NegativeResponseException

from foxtronpi_client.common import get_uds_client

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# DID for FoxPi_Lamp_Ctrl (Read/Write)
DID_LAMP_CTRL = 0x100C

# --- Enums for Readability and Safety ---

class AmbianceControlArea(Enum):
    OFF = 0
    IP = 1
    CONSOLE = 2
    FRONT_DOOR_LEFT = 3
    FRONT_DOOR_RIGHT = 4
    REAR_DOOR_LEFT = 5
    REAR_DOOR_RIGHT = 6
    ALL_AREA = 7

class AmbianceMode(Enum):
    OFF = 0
    WELCOME = 1
    BREATH_RED = 2
    FLASH_KEEP_RED = 3
    SWITCH_TO_RED = 4
    SWITCH_TO_BLUE = 5
    FLASH_KEEP = 6
    BREATH_KEEP = 7

# A subset of the available colors for demonstration
class AmbianceColor(Enum):
    LIGHT_PINK = 0x00
    RED = 0x3F
    BLUE = 0x13
    CYAN = 0x1F
    YELLOW = 0x32
    GREEN = 0x2B

@dataclass
class LampControl:
    """
    Represents the state of DID 0x100C (FoxPi_Lamp_Ctrl).
    Each field corresponds to a bit or byte in the 6-byte payload.
    """
    # Byte 0
    position_lamp_ctrl_en: bool = False
    position_lamp_on: bool = False
    low_beam_ctrl_en: bool = False
    low_beam_on: bool = False
    high_beam_ctrl_en: bool = False
    high_beam_on: bool = False
    right_drl_ctrl_en: bool = False
    right_drl_on: bool = False
    # Byte 1
    left_drl_ctrl_en: bool = False
    left_drl_on: bool = False
    left_turn_lamp_ctrl_en: bool = False
    left_turn_lamp_on: bool = False
    right_turn_lamp_ctrl_en: bool = False
    right_turn_lamp_on: bool = False
    brake_lamp_ctrl_en: bool = False
    brake_lamp_on: bool = False
    # Byte 2
    reverse_lamp_ctrl_en: bool = False
    reverse_lamp_on: bool = False
    rear_fog_lamp_ctrl_en: bool = False
    rear_fog_lamp_on: bool = False
    ambiance_ctrl_en: bool = False
    ambiance_area: AmbianceControlArea = AmbianceControlArea.OFF
    # Byte 3
    ambiance_color: AmbianceColor = AmbianceColor.LIGHT_PINK
    # Byte 4
    ambiance_brightness_percent: int = 0  # Range 0-100
    # Byte 5
    ambiance_mode: AmbianceMode = AmbianceMode.OFF

def pack_lamp_control(state: LampControl) -> bytes:
    """Packs a LampControl object into a 6-byte payload for writing."""
    payload = bytearray(6)

    # Byte 0
    payload[0] |= (1 << 0) if state.position_lamp_ctrl_en else 0
    payload[0] |= (1 << 1) if state.position_lamp_on else 0
    payload[0] |= (1 << 2) if state.low_beam_ctrl_en else 0
    payload[0] |= (1 << 3) if state.low_beam_on else 0
    payload[0] |= (1 << 4) if state.high_beam_ctrl_en else 0
    payload[0] |= (1 << 5) if state.high_beam_on else 0
    payload[0] |= (1 << 6) if state.right_drl_ctrl_en else 0
    payload[0] |= (1 << 7) if state.right_drl_on else 0

    # Byte 1
    payload[1] |= (1 << 0) if state.left_drl_ctrl_en else 0
    payload[1] |= (1 << 1) if state.left_drl_on else 0
    payload[1] |= (1 << 2) if state.left_turn_lamp_ctrl_en else 0
    payload[1] |= (1 << 3) if state.left_turn_lamp_on else 0
    payload[1] |= (1 << 4) if state.right_turn_lamp_ctrl_en else 0
    payload[1] |= (1 << 5) if state.right_turn_lamp_on else 0
    payload[1] |= (1 << 6) if state.brake_lamp_ctrl_en else 0
    payload[1] |= (1 << 7) if state.brake_lamp_on else 0

    # Byte 2
    payload[2] |= (1 << 0) if state.reverse_lamp_ctrl_en else 0
    payload[2] |= (1 << 1) if state.reverse_lamp_on else 0
    payload[2] |= (1 << 2) if state.rear_fog_lamp_ctrl_en else 0
    payload[2] |= (1 << 3) if state.rear_fog_lamp_on else 0
    payload[2] |= (1 << 4) if state.ambiance_ctrl_en else 0
    payload[2] |= (state.ambiance_area.value & 0b111) << 5

    # Byte 3
    payload[3] = state.ambiance_color.value

    # Byte 4
    payload[4] = max(0, min(100, state.ambiance_brightness_percent))

    # Byte 5
    payload[5] = state.ambiance_mode.value & 0b111

    return bytes(payload)

def parse_lamp_control(data: bytes) -> LampControl:
    """Parses a 6-byte response from reading DID 0x100C."""
    if len(data) != 6:
        raise ValueError(f"Expected 6 bytes for Lamp Control, but got {len(data)}")

    return LampControl(
        # Byte 0
        position_lamp_ctrl_en=bool((data[0] >> 0) & 1),
        position_lamp_on=bool((data[0] >> 1) & 1),
        low_beam_ctrl_en=bool((data[0] >> 2) & 1),
        low_beam_on=bool((data[0] >> 3) & 1),
        high_beam_ctrl_en=bool((data[0] >> 4) & 1),
        high_beam_on=bool((data[0] >> 5) & 1),
        right_drl_ctrl_en=bool((data[0] >> 6) & 1),
        right_drl_on=bool((data[0] >> 7) & 1),
        # Byte 1
        left_drl_ctrl_en=bool((data[1] >> 0) & 1),
        left_drl_on=bool((data[1] >> 1) & 1),
        left_turn_lamp_ctrl_en=bool((data[1] >> 2) & 1),
        left_turn_lamp_on=bool((data[1] >> 3) & 1),
        right_turn_lamp_ctrl_en=bool((data[1] >> 4) & 1),
        right_turn_lamp_on=bool((data[1] >> 5) & 1),
        brake_lamp_ctrl_en=bool((data[1] >> 6) & 1),
        brake_lamp_on=bool((data[1] >> 7) & 1),
        # Byte 2
        reverse_lamp_ctrl_en=bool((data[2] >> 0) & 1),
        reverse_lamp_on=bool((data[2] >> 1) & 1),
        rear_fog_lamp_ctrl_en=bool((data[2] >> 2) & 1),
        rear_fog_lamp_on=bool((data[2] >> 3) & 1),
        ambiance_ctrl_en=bool((data[2] >> 4) & 1),
        ambiance_area=AmbianceControlArea((data[2] >> 5) & 0b111),
        # Byte 3
        ambiance_color=AmbianceColor(data[3]),
        # Byte 4
        ambiance_brightness_percent=data[4],
        # Byte 5
        ambiance_mode=AmbianceMode(data[5] & 0b111),
    )

def print_lamp_status(state: LampControl):
    """Prints the lamp status in a human-readable format."""
    print("\n--- FoxtronEV D31X Lamp Status ---")
    for field in fields(state):
        value = getattr(state, field.name)
        if isinstance(value, Enum):
            print(f"  {field.name:<28}: {value.name} ({value.value})")
        else:
            print(f"  {field.name:<28}: {value}")
    print("------------------------------------\n")

def main():
    """
    Main function to connect, read current lamp status, write a new command,
    and verify the change.
    """
    try:
        with get_uds_client() as client:
            # 1. Read the initial lamp status
            log.info(f"Attempting to read DID 0x{DID_LAMP_CTRL:04x} (FoxPi_Lamp_Ctrl)...")
            response = client.read_data_by_identifier(DID_LAMP_CTRL)
            if not response.positive:
                log.error(f"Failed to read initial lamp status: {response.code_name}")
                return

            current_state = parse_lamp_control(response.data)
            log.info("Successfully read initial lamp status.")
            print_lamp_status(current_state)

            # 2. Prepare and write a new command
            log.info("Preparing a new command to turn on low beams and set blue ambient light...")
            new_state = LampControl(
                low_beam_ctrl_en=True,
                low_beam_on=True,
                ambiance_ctrl_en=True,
                ambiance_area=AmbianceControlArea.ALL_AREA,
                ambiance_color=AmbianceColor.BLUE,
                ambiance_brightness_percent=75,
                ambiance_mode=AmbianceMode.BREATH_KEEP
            )

            payload = pack_lamp_control(new_state)
            log.info(f"Sending write command with payload: {payload.hex(' ')}")
            write_response = client.write_data_by_identifier(DID_LAMP_CTRL, payload)

            if write_response.positive:
                log.info("Successfully sent write command.")
            else:
                log.error(f"Failed to write lamp control: {write_response.code_name}")
                return

            # 3. (Optional) Read back the status to verify the change
            log.info("Reading back lamp status to verify changes...")
            verify_response = client.read_data_by_identifier(DID_LAMP_CTRL)
            if verify_response.positive:
                verified_state = parse_lamp_control(verify_response.data)
                log.info("Successfully verified lamp status.")
                print_lamp_status(verified_state)
            else:
                log.error(f"Failed to verify lamp status: {verify_response.code_name}")

    except NegativeResponseException as e:
        log.error(f"Server returned a negative response: {e}")
    except (ConnectionRefusedError, TimeoutError):
        log.error("Could not connect to ECU. Please check network and ECU status. Exiting.")
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()