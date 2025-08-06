import os
import logging
from contextlib import contextmanager
from typing import Iterator

from doipclient import DoIPClient
from udsoncan.connections import DoIPConnection
from udsoncan.client import Client as UdsClient
from udsoncan.configs import config

log = logging.getLogger(__name__)

# --- Configuration ---
# DoIP server configuration - can be overridden with environment variables.
# Example usage:
#   export DOIP_SERVER_IP="192.168.1.11"
#   export ECU_LOGICAL_ADDRESS="4096"
ECU_IP_ADDRESS = os.environ.get("DOIP_SERVER_IP", "192.168.200.1")
ECU_LOGICAL_ADDRESS = int(os.environ.get("ECU_LOGICAL_ADDRESS", "0x0680"), 0)
CLIENT_LOGICAL_ADDRESS = int(os.environ.get("CLIENT_LOGICAL_ADDRESS", "0x0E00"), 0)


def foxtron_security_algo(level, seed, params=None):
    """
    Security algorithm for FoxtronPI.
    This function is called by udsoncan to generate a key from a seed.
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    backend = default_backend()

    keys = {
        1: bytes.fromhex("A8AB5F37723AF4D22BBC7F47D80F8E39"),
        3: bytes.fromhex("8DA76FA39411624E448D2403F8F34ED5"),
        5: bytes.fromhex("74EDB045DCBBCF1FE553B53BCF464691"),
    }

    if level not in keys:
        raise ValueError(f"Unsupported security level: {level}")

    cipher = Cipher(algorithms.AES(keys[level]), modes.ECB(), backend=backend)
    encryptor = cipher.encryptor()
    key = encryptor.update(seed) + encryptor.finalize()
    return key


@contextmanager
def get_uds_client() -> Iterator[UdsClient]:
    """
    A context manager for establishing a DoIP/UDS connection and yielding a client.
    Handles connection setup, teardown, and basic connection errors.
    """
    # Set udsoncan to not validate the length of DID data, as it can be variable.
    config["data_size_check"] = False
    config["security_algo"] = foxtron_security_algo
    config["data_identifiers"] = {
        0x0E04: "16s",  # FD system time YYYYmmddTHHMMSSZ,  16 bytes
        0xF090: "22s",  # FVT VIN
        0xF16F: "10s",  # CAN message map vesrion
        0xF181: "10s",  # Partition number
        0xF184: "10s",  # Application software fingerprint
        0xF187: "10s",  # Spare part number
        0xF190: "17s",  # VIN code
        0xF193: "10s",  # HW version
        0xF195: "10s",  # SW version
    }

    log.info(f"Connecting to ECU at {ECU_IP_ADDRESS} (logical address: {ECU_LOGICAL_ADDRESS:#04x})...")
    try:
        doip_conn = DoIPClient(ECU_IP_ADDRESS, ECU_LOGICAL_ADDRESS)
        with DoIPConnection(doip_conn, client_logical_address=CLIENT_LOGICAL_ADDRESS) as conn:
            with UdsClient(conn) as client:
                log.info("Connection established successfully.")
                yield client
    except (ConnectionRefusedError, TimeoutError) as e:
        log.error(f"Connection to {ECU_IP_ADDRESS} failed: {e}")
        raise
