import struct
from dataclasses import dataclass
import os
import logging
from udsoncan.exceptions import NegativeResponseException

from foxtronpi_client.common import get_uds_client

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# DID for FoxPi_Motion_Status
DID_MOTION_STATUS = 0x1002

@dataclass
class MotionStatus:
    """Represents the parsed data from DID 0x1002 (FoxPi_Motion_Status)."""
    vehicle_speed_kmh: float
    longitudinal_accel_g: float
    longitudinal_accel_valid: bool
    lateral_accel_g: float
    lateral_accel_valid: bool
    yaw_rate_deg_s: float
    yaw_rate_valid: bool

def parse_motion_status(data: bytes) -> MotionStatus:
    """
    Parses the 13-byte raw response for DID 0x1002 into a MotionStatus object.

    The data structure is based on the FoxtronPi specification (Motorola/big-endian):
    - Bytes 0-1:  Vehicle speed (unsigned, 16-bit)
    - Byte 2:     Reserved/Padding
    - Bytes 3-4:  Longitudinal Acceleration (unsigned, 16-bit)
    - Byte 5:     Longitudinal Acceleration Validity (unsigned, 8-bit)
    - Bytes 6-7:  Lateral Acceleration (unsigned, 16-bit)
    - Byte 8:     Lateral Acceleration Validity (unsigned, 8-bit)
    - Bytes 9-10: Yaw Rate (unsigned, 16-bit)
    - Byte 11:    Reserved/Padding
    - Byte 12:    Yaw Rate Validity (unsigned, 8-bit)
    """
    if len(data) != 13:
        raise ValueError(f"Expected 13 bytes for Motion Status, but got {len(data)}")

    # Unpack the raw integer values from the byte string using big-endian format.
    # '>': big-endian
    # 'H': unsigned short (2 bytes)
    # 'B': unsigned char (1 byte)
    # 'x': padding byte (ignored)
    (
        raw_speed,
        raw_long_accel,
        raw_long_accel_v,
        raw_lat_accel,
        raw_lat_accel_v,
        raw_yaw_rate,
        raw_yaw_rate_v,
    ) = struct.unpack(">H xH B H B H xB", data)

    # Apply scaling factors and offsets to convert to physical values
    status = MotionStatus(
        vehicle_speed_kmh=raw_speed * 0.125,
        longitudinal_accel_g=(raw_long_accel * 0.01) - 1.27,
        longitudinal_accel_valid=(raw_long_accel_v == 0x0), # 0x0: valid, 0x1: invalid
        lateral_accel_g=(raw_lat_accel * 0.01) - 1.27,
        lateral_accel_valid=(raw_lat_accel_v == 0x0), # 0x0: valid, 0x1: invalid
        yaw_rate_deg_s=(raw_yaw_rate * 0.1) - 100,
        yaw_rate_valid=(raw_yaw_rate_v == 0x0), # 0x0: valid, 0x1: invalid
    )

    return status

def main():
    """
    Main function to connect to the ECU, read the motion status DID,
    parse the data, and print the results.
    """
    try:
        with get_uds_client() as client:
            log.info(f"Attempting to read DID 0x{DID_MOTION_STATUS:04x} (FoxPi_Motion_Status)...")

            # Send the ReadDataByIdentifier request
            response = client.read_data_by_identifier(DID_MOTION_STATUS)

            if response.positive:
                log.info("Positive response received. Parsing data...")
                motion_data = parse_motion_status(response.data)

                # Print the parsed data in a readable format
                print("\n--- FoxtronEV D31X Motion Status ---")
                print(f"  Vehicle Speed: {motion_data.vehicle_speed_kmh:.3f} km/h")
                print(f"  Longitudinal Accel: {motion_data.longitudinal_accel_g:.2f} G's (Valid: {motion_data.longitudinal_accel_valid})")
                print(f"  Lateral Accel: {motion_data.lateral_accel_g:.2f} G's (Valid: {motion_data.lateral_accel_valid})")
                print(f"  Yaw Rate: {motion_data.yaw_rate_deg_s:.1f} deg/s (Valid: {motion_data.yaw_rate_valid})")
                print("-------------------------------------\n")

    except NegativeResponseException as e:
        log.error(f"Server returned a negative response: {e}")
    except (ConnectionRefusedError, TimeoutError):
        log.error("Could not connect to ECU. Please check network and ECU status. Exiting.")
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    # To run this example:
    # 1. Make sure you have the dependencies installed: pip install python-doipclient python-udsoncan
    # 2. Update the ECU_IP_ADDRESS and ECU_LOGICAL_ADDRESS constants above.
    # 3. Run the script: python read_motion_status_example.py
    main()