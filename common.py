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
ECU_IP_ADDRESS = os.environ.get("DOIP_SERVER_IP", "192.168.1.10")
ECU_LOGICAL_ADDRESS = int(os.environ.get("ECU_LOGICAL_ADDRESS", "0x1000"), 0)
CLIENT_LOGICAL_ADDRESS = int(os.environ.get("CLIENT_LOGICAL_ADDRESS", "0x0E00"), 0)


@contextmanager
def get_uds_client() -> Iterator[UdsClient]:
    """
    A context manager for establishing a DoIP/UDS connection and yielding a client.
    Handles connection setup, teardown, and basic connection errors.
    """
    # Set udsoncan to not validate the length of DID data, as it can be variable.
    config["data_size_check"] = False

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