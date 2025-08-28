from doipclient import DoIPClient
from doipclient.connectors import DoIPClientUDSConnector
from common import get_uds_client
from client_config import DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS
from udsoncan.client import Client
from udsoncan.services import *
from FoxPi_write import FoxPiWriteDID



doip_client = DoIPClient(DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS, protocol_version=3) #creat a DoIP object (IP, Logical Address and DoIP protocol version 3)
uds_connection = DoIPClientUDSConnector(doip_client) #Use the previously created doip_client to construct a connection object for UDS (diagnostic services).
assert uds_connection.is_open #Verify whether the UDS connection has been successfully established
with Client(uds_connection, request_timeout=4, config=get_uds_client()) as client: #Execute it within a context manager so that the connection is automatically closed when finished.

    FoxPi = FoxPiWriteDID(client)
    WID_map = {
        1: FoxPi.FoxPi_Driving_Ctrl,
        2: FoxPi.FoxPi_Lamp_Ctrl,
        3: FoxPi.Driving_Ctrl_toFF,
        4: FoxPi.FoxPi_Ctrl_Enable_Switch
    }

    WID_param = {
        1: ["AccReq","AccReq_A","TargetSpdReq","TargetSpdReq_A","Angle_Target_Valid","Angle_Target_Req",
            "Angle_Target","Torque_Target_Valid","Torque_Target_Req","Torque_Target","VINP_APSVMCReqA_flg",
            "VINP_APSStaSystem_enum","VINP_APSShiftPosnReq_enum","VINP_APSSpeedCMD_kph"],
        2: ["Position_Lamp_Control_Enable","Position_Lamp","Low_Beam_Control_Enable","Low_Beam",
            "High_Beam_Control_Enable","High_Beam","Right_Daytime_Running_Light_Control_Enable",
            "Right_Daytime_Running_Light","Left_Daytime_Running_Light_Control_Enable","Left_Daytime_Running_Light",
            "Left_TurnLamp_Control_Enable","Left_TurnLamp","Right_TurnLamp_Control_Enable","Right_TurnLamp",
            "Brake_Lamp_Control_Enable","Brake_Lamp","Reverse_Lamp_Control_Enable","Reverse_Lamp",
            "Rear_Fog_Lamp_Control_Enable","Rear_Fog_Lamp","Amblight_Control_Enable","Control area",
            "RGB 64 Color","Bright adjustment","Breathing and Alert Mode"],
        3: [],
        4: ["Ctrl_Enable_Switch"]
    }

    default_value = {
        1: [-10, 1, 255.875, 1, 1, 1, -900, 1, 1, -10, 1, 4, 7, 20],
        2: [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,7,63,100,7],
        3: [],
        4: [0]
    }

    
    while True:

        print(f"\n\033[33mPlease input the number(1-4) of the DID you want to write:\033[0m")
        for i,j in WID_map.items():
            print(f"{i} = {j.__name__}")
        
        try:
            WID = int(input("Enter your choice number(or 0 to exit):"))
        except ValueError as e:
            print(f"\033[91m{e}\033[0m")
            continue
        
        excute = WID_map.get(WID)
        if  WID==0:
            break
        elif not excute:
            print("\033[91mInvalid input. Please enter a number between 1 to 4.\033[0m")
            continue

        defult = default_value.get(WID,[])
        param = WID_param.get(WID,[])
        user_input = []

        if param:
            if input(f"Press \033[92mEnter\033[0m to use defaule or input \033[91mn\033[0m to setup parameters: ") == "":
                user_input = defult
            else:
                for i in param:
                    while True:
                        raw = input(f"{i}: ")
                        try:
                            value = float(raw) if ('.' in raw) else int(raw)
                            user_input.append(value)
                            break
                        except ValueError as e:
                            print(f"\033[91m{e}\033[0m")
                            continue
            print(f"\033[92mYour input values are: {user_input}\033[0m")
            excute(user_input)
        else:
            print(f"\033[92mNo parameters needed input for {excute.__name__}\033[0m")
            excute()