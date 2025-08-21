from doipclient import DoIPClient
from doipclient.connectors import DoIPClientUDSConnector
from common import get_uds_client
from client_config import DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS
from udsoncan.client import Client
from udsoncan.services import *
import datetime
import os
import math


class FoxPiWriteDID:

    def __init__(self, client: Client): # Initialization function; pass in the client parameter, which is the UDS communication object.
        self.client = client

    def debug_print(self,msg): #Print the current time (in blue) and the message
        print(f"\033[34m{datetime.datetime.now()}\033[0m: {msg}")

    def FoxPi_Driving_Ctrl(self,user_input:str) -> bytes: #Define FoxPi_Driving_Ctrl to write DID 0x1001

        try:
            #Ensure user_input length is not equal to 14
            if len(user_input) != 14:
                raise ValueError(f"\033[91mFoxPi_Driving_Ctrl Input must contain exactly 14 values but you only provided {len(user_input)} values.\033[0m")
            
            #to convert all elements to int, if they are float and integer, otherwise keep as is
            DID_list = [int(x) if isinstance(x, float) and x.is_integer() else x for x in user_input]

            #Use to limit values and prevent out-of-range writes to the signal.
            Value_limit = [
                (0, -15, 10.55, "Acceleration Request"),
                (1, 0, 1, "Acceleration Request A"),
                (2, 0, 255.875, "Target Speed Request"),
                (3, 0, 1, "Target Speed Request A"),
                (4, 0, 1, "Angle Target Valid"),
                (5, 0, 1, "Angle Target Request"),
                (6, -900, 900, "Angle Target"),
                (7, 0, 1, "Torque Target Valid"),
                (8, 0, 1, "Torque Target Request"),
                (9, -10, 10, "Torque Target"),
                (10, 0, 1, "APS_flg"),
                (11, 0, 4, "VINP_APSStaSystem_enum"),
                (12, 0, 7, "VINP_APSShiftPosnReq_enum"),
                (13, 0, 20, "VINP_APSSpeedCMD_kph"),
            ]

            #Check whether user_input is out-of-range the specified range.
            for idx, min, max, name in Value_limit:
                idx_value = DID_list[idx]
                if not (min <=idx_value <= max): #Print an error if it not within the specified range
                    raise ValueError(f"\033[91mFoxPi_Driving_Ctrl {name}[{idx}] must be between \033[33m{min} \033[91mand \033[33m{max} \033[91mbut you provided <{idx_value}>\033[0m")

            # <<4 is means shift left by 4 bits, <<1 is shift left by 1 bit
            # 0 0 0 0 0 0 0 0
            # 7 6 5 4 3 2 1 0
            # Ex: 7 6 5 4, "<< 4" | 3 2 1, "<< 1" | 0
            # Ex: 7 6 5 4 3 2 1 "<< 1" | 0
            APS_bit = (DID_list[12] << 4) | (DID_list[11] << 1) | DID_list[10] # | is bitwise OR operation combining the bits into a single byte

            # pack all user_input value into the byte_list array
            byte_list = [
                math.floor((DID_list[0]-(-15))/0.05).to_bytes(3, byteorder="big"), #math.floor rounds down to the nearest integer(3.7->3,-3.7->-4,5.0->5), ACCReq = 3byte
                math.floor(DID_list[1]).to_bytes(1, byteorder="big"), #ACCReq_A = 1byte
                math.floor(DID_list[2]/0.125).to_bytes(3, byteorder="big"), #TargetSpdReq = 3byte
                math.floor(DID_list[3]).to_bytes(1, byteorder="big"), #TargetSpdReq_A = 1byte
                math.floor(DID_list[4]).to_bytes(1, byteorder="big"),#Angle_Target_Valid = 1byte
                math.floor(DID_list[5]).to_bytes(1,byteorder="big"), #Angle_Target_Req= 1byte
                math.floor((DID_list[6]-(-900))/0.1).to_bytes(4, byteorder="big"), #Angle_Target = 4byte
                math.floor(DID_list[7]).to_bytes(1, byteorder="big"), #Torque_Target_Valid = 1byte
                math.floor(DID_list[8]).to_bytes(1, byteorder="big"), #Torque_Target_Req = 1byte
                math.floor((DID_list[9]-(-10))/0.01).to_bytes(3, byteorder="big"), #Torque_Target = 3byte
                APS_bit.to_bytes(1, byteorder="big"),  # APS = 1byte
                math.floor(DID_list[13]/0.125).to_bytes(1, byteorder="big") #VINP_APSSpeedCMD_kph = 1byte
            ] # all 21 bytes for FoxPi_Driving_Ctrl

            ##merge the byte_list elements into a single contiguous bytes payload.
            merged_bytes = b''.join(byte_list)

            print(f"Processed input: {merged_bytes}")

            #Change Diagnostic Session to Extended DiagnosticSession
            response = client.change_session(DiagnosticSessionControl.Session.extendedDiagnosticSession)
            response = client.unlock_security_access(1)#Set the security_access key=1
            response = client.write_data_by_identifier(0x1001, merged_bytes)#write the previously merged_bytes to DID(0x1001)

            self.debug_print(f"The response sevice is {response.service_data}, data is {response.data.hex()}")

            return merged_bytes
        
        except Exception as e:#Print an error message if an error occurs
            print(f"Error processing input: {e}")
            return None

    def FoxPi_Lamp_Ctrl(self,user_input:str) -> bytes:#Define FoxPi_Lamp_Ctrl to write DID 0x1001

        try:

            #Ensure user_input length is not equal to 25
            if len(user_input) != 25:
                raise ValueError(f"\033[91mFoxPi_Lamp_Ctrl Input must contain exactly 25 values but you only provided {len(user_input)} values.\033[0m")
            
            #to convert all elements to int, if they are float and integer, otherwise keep as is
            DID_list = [int(x) if float(x).is_integer() else (_ for _ in ()).throw(ValueError(f"\033[91mYou input not int：{x}\033[0m")) for x in user_input]
            print(f"Input values: {DID_list}")

            #Use to limit values and prevent out-of-range writes to the signal.
            Value_limit = [
                (0, 0, 1, "Position_Lamp_Control_Enable"),
                (1, 0, 1, "Position_Lamp"),
                (2, 0, 1, "Low_Beam_Control_Enable"),
                (3, 0, 1, "Low_Beam"),
                (4, 0, 1, "High_Beam_Control_Enable"),
                (5, 0, 1, "High_Beam"),
                (6, 0, 1, "Right_Daytime_Running_Light_Control_Enable"),
                (7, 0, 1, "Right_Daytime_Running_Light"),
                (8, 0, 1, "Left_Daytime_Running_Light_Control_Enable"),
                (9, 0, 1, "Left_Daytime_Running_Light"),
                (10, 0, 1, "Left_TurnLamp_Control_Enable"),
                (11, 0, 1, "Left_TurnLamp"),
                (12, 0, 1, "Right_TurnLamp_Control_Enable"),
                (13, 0, 1, "Right_TurnLamp"),
                (14, 0, 1, "Brake_Lamp_Control_Enable"),
                (15, 0, 1, "Brake_Lamp"),
                (16, 0, 1, "Reverse_Lamp_Control_Enable"),
                (17, 0, 1, "Reverse_Lamp"),
                (18, 0, 1, "Rear_Fog_Lamp_Control_Enable"),
                (19, 0, 1, "Rear_Fog_Lamp"),
                (20, 0, 1, "Amblight_Control_Enable"),
                (21, 0, 7, "Control area"),
                (22, 0, 63, "RGB 64 Color"),
                (23, 0, 100, "Bright adjustment"),
                (24, 0, 7, "Breathing and Alert Mode"),
            ]

            #Check whether user_input is out-of-range the specified range.
            for idx, min, max, name in Value_limit:
                idx_value = DID_list[idx]
                if not (min <= idx_value <= max):
                    raise ValueError(f"\033[91mFoxPi_Lamp_Ctrl {name}[{idx}] must be between \033[33m{min} \033[91mand \033[33m{max} \033[91mbut you provided <{idx_value}>\033[0m")
            
            # bit1,bit2,bit3: Pack all user input values into their corresponding bit positions
            bit1 = ((DID_list[7] << 7) | #Right_Daytime_Running_Light
                        (DID_list[6] << 6) | #Right_Daytime_Running_Light_Control_Enable
                        (DID_list[5] << 5) | #High_Beam
                        (DID_list[4] << 4) | #High_Beam_Control_Enable
                        (DID_list[3] << 3) | #Low_Beam
                        (DID_list[2] << 2) | #Low_Beam_Control_Enable
                        (DID_list[1] << 1) | #Position_Lamp
                        (DID_list[0] << 0) ) #Position_Lamp_Control_Enable
            
            bit2 = ((DID_list[15] << 7) | #Brake_Lamp
                        (DID_list[14] << 6) | #Brake_Lamp_Control_Enable
                        (DID_list[13] << 5) | #Right_TurnLamp
                        (DID_list[12] << 4) | #Right_TurnLamp_Control_Enable
                        (DID_list[11] << 3) | #Left_TurnLamp
                        (DID_list[10] << 2) | #Left_TurnLamp_Control_Enable
                        (DID_list[9] << 1) | #Left_Daytime_Running_Light
                        (DID_list[8] << 0) ) #Left_Daytime_Running_Light_Control_Enable
            
            bit3 = ((DID_list[21] << 5) | #Control area
                        (DID_list[20] << 4) | #Amblight_Control_Enable
                        (DID_list[19] << 3) | #Rear_Fog_Lamp
                        (DID_list[18] << 2) | #Rear_Fog_Lamp_Control_Enable
                        (DID_list[17] << 1) | #Reverse_Lamp
                        (DID_list[16] << 0) ) #Reverse_Lamp_Control_Enable
            


            #Pack bit1~bit3 into the byte_list array (big-endian)
            byte_list = [
                bit1.to_bytes(1, byteorder="big"),
                bit2.to_bytes(1, byteorder="big"),
                bit3.to_bytes(1, byteorder="big"),
                DID_list[22].to_bytes(1, byteorder="big"), #RGB 64 Color = 1byte
                DID_list[23].to_bytes(1, byteorder="big"), #Bright adjustment
                DID_list[24].to_bytes(1, byteorder="big")  #Breathing and Alert Mode
            ]

            print(f"Processed input: {byte_list}")
            #merge the byte_list elements into a single contiguous bytes payload.
            merged_bytes = b''.join(byte_list)
            print(f"Merged bytes: {merged_bytes}")

            #Change Diagnostic Session to Extended DiagnosticSession
            response = client.change_session(DiagnosticSessionControl.Session.extendedDiagnosticSession)
            response = client.unlock_security_access(1) #Set the security_access key=1
            response = client.write_data_by_identifier(0x100C, merged_bytes)  #write the previously merged_bytes to DID(0x100C)

            self.debug_print(f"The response sevice is {response.service_data}, data is {response.data.hex()}")

            return merged_bytes
               
        except Exception as e:#Print an error message if an error occurs
            print(f"Error processing input: {e}")
            return None

    def FoxPi_Ctrl_Enable_Switch(self,user_input:str) -> bytes:#Define FoxPi_Ctrl_Enable_Switch to write DID 0x1001

        try:

            #Ensure user_input length is not equal to 25
            if len(user_input) != 1:
                raise ValueError(f"\033[91mFoxPi_Ctrl_Enable_Switch Input must contain exactly 1 values but you only provided {len(user_input)} values.\033[0m")
            print(f"Input values: {user_input}")
            
            #Validate: user_input[0] must be an integer 0 or 1
            if not isinstance(user_input[0], int) or user_input[0] not in [0, 1]:
                raise ValueError(f"\033[91mFoxPi_Ctrl_Enable_Switch Input must be either 0 or 1 but you provided {user_input[0]}\033[0m")

            # Convert user_input[0] to a 1-byte value (big-endian)
            Ctrl_Enable = user_input[0].to_bytes(1, byteorder="big") # Convert user_input[0] to a 1-byte value (big-endian)

            #Change Diagnostic Session to Extended DiagnosticSession
            response = client.change_session(DiagnosticSessionControl.Session.extendedDiagnosticSession)
            response = client.unlock_security_access(1) #Set the security_access key=1
            response = client.write_data_by_identifier(0x1012, Ctrl_Enable) #write the previously merged_bytes to DID(0x1012)

            self.debug_print(f"The response sevice is {response.service_data}, data is {response.data.hex()}")

            return Ctrl_Enable
            
        except Exception as e:#Print an error message if an error occurs
            print(f"Error processing input: {e}")
            return None
            
    def Driving_Ctrl_toFF(self) -> bytes:#write the Driving_Ctrl signal to 0xFF (default value)
        
        try:

            data_toFF = bytes([0xff]*21) # 21 bytes of 0xFF
            print(f"Processed input: {data_toFF}")

            #Change Diagnostic Session to Extended DiagnosticSession
            response = client.change_session(DiagnosticSessionControl.Session.extendedDiagnosticSession)
            response = client.unlock_security_access(1)#Set the security_access key=1
            response = client.write_data_by_identifier(0x1001, data_toFF)#write the previously merged_bytes to DID(0x1001)


            self.debug_print(f"The response sevice is {response.service_data}, data is {response.data.hex()}")

            return data_toFF

        except Exception as e:#Print an error message if an error occurs
            print(f"Error processing: {e}")
            return None
    



doip_client = DoIPClient(DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS, protocol_version=3) #creat a DoIP object (IP, Logical Address and DoIP protocol version 3)
uds_connection = DoIPClientUDSConnector(doip_client) #Use the previously created doip_client to construct a connection object for UDS (diagnostic services).
assert uds_connection.is_open #Verify whether the UDS connection has been successfully established
with Client(uds_connection, request_timeout=4, config=get_uds_client()) as client: #Execute it within a context manager so that the connection is automatically closed when finished.

    FoxPi = FoxPiWriteDID(client)
    #FoxPi.FoxPi_Driving_Ctrl(user_input=[-10, 1, 255.875, 1, 1, 1, -900, 1, 1, -10, 1, 4, 7, 20])
    FoxPi.FoxPi_Lamp_Ctrl(user_input=[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,7,63,100,7])
    #FoxPi.Driving_Ctrl_toFF()
    #FoxPi.FoxPi_Lamp_Ctrl(user_input=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    #FoxPi.FoxPi_Ctrl_Enable_Switch(user_input=[1])

