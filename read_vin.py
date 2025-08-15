from typing import cast

from doipclient import DoIPClient
from doipclient.connectors import DoIPClientUDSConnector
from udsoncan import ClientConfig
from udsoncan.client import Client
from udsoncan.services import *


def foxtron_security_algo(level, seed, params=None):
    """
    Security algorithm for FoxtronPI.
    This function is called by udsoncan to generate a key from a seed.
    """
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

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


client_config: ClientConfig = cast(
    ClientConfig,
    {
        "security_algo": foxtron_security_algo,
        "server_memorysize_format": None,  # 8,16,24,32,40
        "data_identifiers": {0xF190: "17s"},
    },
)


client = DoIPClient("169.254.200.1", 0x0680, protocol_version=3)
uds_connection = DoIPClientUDSConnector(client)
with Client(uds_connection, config=client_config) as uds_client:
    response = uds_client.read_data_by_identifier(0xF190)
    uds_client.change_session(3)
    uds_client.unlock_security_access(1)

    print(response.service_data.values[0xF190])
