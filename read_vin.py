import os
from doipclient import DoIPClient
from doipclient.connectors import DoIPClientUDSConnector
from udsoncan.client import Client
from common import get_uds_client
from client_config import DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS


doip_client = DoIPClient(DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS, protocol_version=3)
uds_connection = DoIPClientUDSConnector(doip_client)
assert uds_connection.is_open
with Client(uds_connection, request_timeout=4, config=get_uds_client()) as client:
    DID = int("0x"+input("Please input DID Number:"),16)
    print(type(DID))
    response = client.read_data_by_identifier(DID)
    print(f"VIN: {response.service_data.values[DID]}")