import os

DOIP_SERVER_IP = os.environ.get("DOIP_SERVER_IP", "192.168.200.1")
DoIP_LOGICAL_ADDRESS = int(os.environ.get("DoIP_LOGICAL_ADDRESS", "0x0680"), 0)
CLIENT_LOGICAL_ADDRESS = int(os.environ.get("CLIENT_LOGICAL_ADDRESS", "0x0E00"), 0)