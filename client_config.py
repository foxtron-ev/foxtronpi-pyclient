import os

DOIP_SERVER_IP = os.environ.get("DOIP_SERVER_IP", "192.168.200.1") # Get an IP(FD) from the environment; use 192.168.200.1 if none is provided. 
DoIP_LOGICAL_ADDRESS = int(os.environ.get("DoIP_LOGICAL_ADDRESS", "0x0680"), 0) # Get an DoIP_LOGICAL_ADDRESS(FD) from the environment; use 0x0680 if none is provided.
CLIENT_LOGICAL_ADDRESS = int(os.environ.get("CLIENT_LOGICAL_ADDRESS", "0x0E00"), 0) # Get an LIENT_LOGICAL_ADDRESS from the environment; use 0x0E00 if none is provided.