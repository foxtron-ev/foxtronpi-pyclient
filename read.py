from doipclient import DoIPClient
from doipclient.connectors import DoIPClientUDSConnector
from udsoncan.client import Client
from common import get_uds_client
from client_config import DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS
from FoxPi_read import FoxPiReadDID
import datetime



print(f"{datetime.datetime.now()}: Connecting to vehicle at {DOIP_SERVER_IP} with logical address {DoIP_LOGICAL_ADDRESS}") # print the DOIP_SERVER_IP,DoIP_LOGICAL_ADDRESS and the current time
doip_client = DoIPClient(DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS, protocol_version=3) #creat a DoIP object (IP, Logical Address and DoIP protocol version 3)
uds_connection = DoIPClientUDSConnector(doip_client) #Use the previously created doip_client to construct a connection object for UDS (diagnostic services).
assert uds_connection.is_open #Verify whether the UDS connection has been successfully established
with Client(uds_connection, request_timeout=4, config=get_uds_client()) as client: #Execute it within a context manager so that the connection is automatically closed when finished.
    
    Foxpi = FoxPiReadDID(client)
    RID_map = {
    1: Foxpi.FoxPi_Driving_Ctrl,
    2: Foxpi.FoxPi_Motion_Status,
    3: Foxpi.FoxPi_Brake_Status,
    4: Foxpi.FoxPi_WheelSpeed,
    5: Foxpi.FoxPi_EPS_Status,
    6: Foxpi.FoxPi_Button_Status,
    7: Foxpi.FoxPi_USS_Distance,
    8: Foxpi.FoxPi_USS_Fault_Status,
    9: Foxpi.FoxPi_PTG_USS_SW,
    10: Foxpi.FoxPi_Switch_Status,
    11: Foxpi.FoxPi_Lamp_Status,
    12: Foxpi.FoxPi_Lamp_Ctrl,
    13: Foxpi.FoxPi_Battery_Status,
    14: Foxpi.FoxPi_TPMS_Status,
    15: Foxpi.FoxPi_Pedal_position,
    16: Foxpi.FoxPi_Motor_Status,
    17: Foxpi.FoxPi_Shifter_allow,
    18: Foxpi.FoxPi_Ctrl_Enable_Switch
}
    while True:

        print(f"\n\033[33mPlease input the number(1-18) of the DID you want to read:\033[0m")
        for i,j in RID_map.items():
            print(f"{i} = {j.__name__}")
        
        try:
            RID = int(input("Enter your choice number(or 0 to exit):"))

        except ValueError as e:
            print(f"\033[91m{e}\033[0m")
            continue

        excute = RID_map.get(RID)
        if  RID==0:
            break
        elif excute:
            excute()
        else:
            print("\033[91mInvalid input. Please enter a number between 1 to 18.\033[0m")