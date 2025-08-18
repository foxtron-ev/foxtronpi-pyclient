import os
from doipclient import DoIPClient
from doipclient.connectors import DoIPClientUDSConnector
from udsoncan.client import Client
from udsoncan.services import *
from common import get_uds_client
from client_config import DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS


doip_client = DoIPClient(DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS, protocol_version=3)
uds_connection = DoIPClientUDSConnector(doip_client)
assert uds_connection.is_open
with Client(uds_connection, request_timeout=4, config=get_uds_client()) as client:

    user_input = input("Enter VIN code: ")
    response = client.change_session(
        DiagnosticSessionControl.Session.extendedDiagnosticSession
    )
    response = client.unlock_security_access(1)
    response = client.write_data_by_identifier(0xF190, user_input.encode("utf-8"))
    print(f"VIN: {response.data.hex()}")