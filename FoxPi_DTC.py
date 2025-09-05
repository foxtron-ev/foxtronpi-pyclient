from doipclient import DoIPClient
from doipclient.connectors import DoIPClientUDSConnector
from udsoncan.client import Client
from udsoncan.services import ReadDTCInformation
from common import get_uds_client
from client_config import DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS, DoIP_FUNCTION_ADDRESS

class FoxPiDTC:

    def __init__(self, client, doip_client): # Initialization function; pass in the client parameter, which is the UDS communication object.
        self.client = client
        self.doip_client = doip_client

    def Read_DTCs(self):
        self.doip_client._ecu_logical_address = DoIP_FUNCTION_ADDRESS
        resp = self.client.read_dtc_information(ReadDTCInformation.Subfunction.reportDTCByStatusMask, status_mask=0x0F)
        print(f"response: {resp}")
        if resp.service_data.dtcs is None or len(resp.service_data.dtcs) == 0:
            print("No DTCs found.")
            self.doip_client._ecu_logical_address = DoIP_LOGICAL_ADDRESS
            return []
        else:
            for dtc in resp.service_data.dtcs:
                print(f"DTC=0x{dtc.id:06X}  pending={dtc.status.pending}  confirmed={dtc.status.confirmed}  test_failed={dtc.status.test_failed}")
            self.doip_client._ecu_logical_address = DoIP_LOGICAL_ADDRESS
            return 
    
    def Clear_DTCs(self):
        self.doip_client._ecu_logical_address = DoIP_FUNCTION_ADDRESS
        try:
            resp = self.client.clear_dtc(group=0xFFFFFF)
            print(f"Clear DTCs successful, response: {resp}")
            self.doip_client._ecu_logical_address = DoIP_LOGICAL_ADDRESS
            return
        except Exception as e:
            print(f"Clear DTCs failed: {e}")
            self.doip_client._ecu_logical_address = DoIP_LOGICAL_ADDRESS
            return

