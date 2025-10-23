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
        self.doip_client._ecu_logical_address = DoIP_FUNCTION_ADDRESS # change to the functional address to read all DTCs
        resp = self.client.read_dtc_information(ReadDTCInformation.Subfunction.reportDTCByStatusMask, status_mask=0x0F) # 0x0F to read problem DTC 
        print(f"response: {resp}")
        if resp.service_data.dtcs is None or len(resp.service_data.dtcs) == 0:
            self.doip_client._ecu_logical_address = DoIP_LOGICAL_ADDRESS # change back to the physical address
            return "Success, no DTCs found"
        else:
            cfg = {}
            for dtc in resp.service_data.dtcs:
                #print(f"DTC=0x{dtc.id:06X}  pending={dtc.status.pending}  confirmed={dtc.status.confirmed}  test_failed={dtc.status.test_failed}")
                cfg[dtc] ={
                    "DTC": f"0x{dtc.id:06X}",
                    "pending": dtc.status.pending,
                    "confirmed": dtc.status.confirmed,
                    "test_failed": dtc.status.test_failed
                }
            self.doip_client._ecu_logical_address = DoIP_LOGICAL_ADDRESS # change back to the physical address
            return cfg
    
    def Clear_DTCs(self):
        self.doip_client._ecu_logical_address = DoIP_FUNCTION_ADDRESS # change to the functional address to clear all DTCs
        try:
            resp = self.client.clear_dtc(group=0xFFFFFF) # 0xFFFFFF= clear all DTC
            self.doip_client._ecu_logical_address = DoIP_LOGICAL_ADDRESS# change back to the physical address
            return "Clear DTCs successful"
        except Exception as e:
            #print(f"Clear DTCs failed: {e}")
            self.doip_client._ecu_logical_address = DoIP_LOGICAL_ADDRESS # change back to the physical address
            return e