from doipclient import DoIPClient
from doipclient.connectors import DoIPClientUDSConnector
from common import get_uds_client
from client_config import DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS
from udsoncan.client import Client

from decimal import Decimal, ROUND_DOWN
from typing import Dict, Union
import datetime
import os


class FoxPiReadDID:
      
    def __init__(self, client): # Initialization function; pass in the client parameter, which is the UDS communication object.
        self.client = client

    def debug_print(self, msg): #Print the current time (in blue) and the message
        print(f"\033[34m{datetime.datetime.now()}\033[0m: {msg}")

    def bits_to_int(self, bits): #convert a list of bits to an integer
        return int(''.join(map(str, bits)), 2)

    def bytes_to_int(self, byte): #convert a byte to an integer
        return int(byte.hex(), 16)
    
    def FF(self,value,FF_check): #check value == FF
        return "FF" if FF_check else value

    def read(self, did, name): #call the read_data_by_identifier functiion to Read DID and return the response data
        response = self.client.read_data_by_identifier(did)
        self.debug_print(f"\033[33m{name}\033[0m: {hex(did)}: {response.service_data.values[did]}")
        return response.service_data.values[did][0] #Return DID byte data

    def FoxPi_Driving_Ctrl(self) -> Dict[str, Union[int, float, str]]: #Define FoxPi_Driving_Ctrl to read DID 0x1001 and decode the response byte data into a dict
        
        byte_data =self.read(0x1001,"FoxPi_Driving_Ctrl") #read DID

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw[x] * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.


        AccReq = self.bytes_to_int(byte_data[:3])*0.05-15 #3s,*Factor-offset
        AccReq_A = byte_data[3] #1S
        TargetSpdReq = self.bytes_to_int(byte_data[4:7])*0.125 #3s
        TargetSpdReq_A = byte_data[7] #1S

        Angle_Target_Valid = byte_data[8] #1S
        Angle_Target_Req = byte_data[9] #1s
        Angle_Target = self.bytes_to_int(byte_data[10:14])*0.1-900 #4s,*Factor-offset
        Torque_Target_Valid = byte_data[14] #1S
        Torque_Target_Req = byte_data[15] #1s
        Torque_Target = self.bytes_to_int(byte_data[16:19])*0.01-10 #4s,*Factor-offset

        #APS_byte= decimal_values[18]
        APS_bit= bin(byte_data[19])[2:].zfill(8) #[2:]cut off the '0b' prefix,.zfill(8) guarantees 8 bits
        bit_list= [int(bit) for bit in APS_bit] # Convert the binary string to a list of integers

        APSVMCReqA_flg = bit_list[7] #1bit
        APSStaSystem_enum = self.bits_to_int(bit_list[4:7]) #Convert the bits to an integer
        APSShiftPosnReq_enum = self.bits_to_int(bit_list[0:4]) #Convert the bits to an integer
        APS_SpeedCMD = byte_data[20]*0.125 #1S
        

        print("AccReq: \033[91mFF\033[0m m/s^2" if all(b==255 for b in byte_data[:3]) else f"AccReq: {AccReq} m/s^2")#\033[91m:red color \033[0m:reset to default color
        print("AccReq_A: \033[91mFF\033[0m" if AccReq_A==255 else f"AccReq_A: {AccReq_A}")
        print("TargetSpdReq: \033[91mFF\033[0m km/h" if all(b==255 for b in byte_data[4:7]) else f"TargetSpdReq: {TargetSpdReq} km/h")
        print("TargetSpdReq_A: \033[91mFF\033[0m" if TargetSpdReq_A==255 else f"TargetSpdReq_A: {TargetSpdReq_A}")

        print("Angle_Target_Valid: \033[91mFF\033[0m" if Angle_Target_Valid==255 else f"Angle_Target_Valid: {Angle_Target_Valid}")
        print("Angle_Target_Req: \033[91mFF\033[0m" if Angle_Target_Req==255 else f"Angle_Target_Req: {Angle_Target_Req}")
        print("Angle_Target: \033[91mFF\033[0m Deg" if all(b==255 for b in byte_data[10:13]) else f"Angle_Target: {Angle_Target}")

        print("Torque_Target_Valid: \033[91mFF\033[0m" if Torque_Target_Valid==255 else f"Torque_Target_Valid: {Torque_Target_Valid}")
        print("Torque_Target_Req: \033[91mFF\033[0m" if Torque_Target_Req==255 else f"Torque_Target_Req: {Torque_Target_Req}")
        print("Torque_Target: \033[91mFF\033[0m Nm" if all(b==255 for b in byte_data[15:18]) else f"Torque_Target: {Torque_Target}")

        #print(f"APS_bit: {APS_bit} -> {bit_list} -> {APSVMCReqA_flg}")
        print("APSVMCReqA_flg: \033[91mFF\033[0m \nAPSStaSystem_enum: \033[91mFF\033[0m \nAPSShiftPosnReq_enum: \033[91mFF\033[0m" if bit_list == [1]*8 
            else f"APSVMCReqA_flg: {APSVMCReqA_flg}\nAPSStaSystem_enum: {APSStaSystem_enum} \nAPSShiftPosnReq_enum: {APSShiftPosnReq_enum} ")
        #print(f"APSVMCReqA_flg: {APSVMCReqA_flg}")
        #print(f"APSStaSystem_enum: {APSStaSystem_enum} -> {APSStaSystem}")
        #print(f"APSShiftPosnReq_enum: {APSShiftPosnReq_enum} -> {APSShiftPosnReq}")
        print("APS_SpeedCMD: \033[91mFF\033[0m km/h" if byte_data[20]==255 else f"APS_SpeedCMD: {APS_SpeedCMD}")
        
        FF= "\033[91mFF\033[0m" 

         # FF mechanism: if the value is FF, output 'FF' directly
        return {
            "AccReq": FF if all(b==255 for b in byte_data[:3]) else AccReq,
            "AccReq_A": FF if AccReq_A==255 else AccReq_A,
            "TargetSpdReq": FF if all(b==255 for b in byte_data[4:7]) else TargetSpdReq,
            "TargetSpdReq_A": FF if TargetSpdReq_A==255 else TargetSpdReq_A,
            "Angle_Target_Valid": FF if Angle_Target_Valid==255 else Angle_Target_Valid,
            "Angle_Target_Req": FF if Angle_Target_Req==255 else Angle_Target_Req,
            "Angle_Target": FF if all(b==255 for b in byte_data[10:13]) else Angle_Target,
            "Torque_Target_Valid": FF if Torque_Target_Valid==255 else Torque_Target_Valid,
            "Torque_Target_Req": FF if Torque_Target_Req==255 else Torque_Target_Req,
            "Torque_Target": FF if all(b==255 for b in byte_data[15:18]) else Torque_Target,
            "APSVMCReqA_flg": FF if bit_list == [1]*8 else APSVMCReqA_flg,
            "APSStaSystem_enum": FF if bit_list == [1]*8 else APSStaSystem_enum,
            "APSShiftPosnReq_enum": FF if bit_list == [1]*8 else APSShiftPosnReq_enum,
            "APS_SpeedCMD": FF if byte_data[20]==255 else APS_SpeedCMD
            }

    def FoxPi_Motion_Status(self) -> Dict[str, Union[int, float, str]]: #Define FoxPi_Motion_Status to read DID 0x1002 and decode the response byte data into a dict

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        byte_data =self.read(0x1002,"FoxPi_Motion_Status") #Read DID
        VehicleSpeed = self.bytes_to_int(byte_data[0:3])*0.125 #3s,*Factor
        LongAccel = self.bytes_to_int(byte_data[3:5])*0.01-1.27 #2s*Factor-offset
        LongAccel_V = byte_data[5]#1S
        LatAccel = self.bytes_to_int(byte_data[6:8])*0.01-1.27 #2s
        LatAccel_V = byte_data[8]#1S
        YawRate = self.bytes_to_int(byte_data[9:12])*0.1-100 #3s
        YawRate_V = byte_data[12]

        print(f"VehicleSpeed: {VehicleSpeed} km/h")
        print(f"LongAccel: {LongAccel} G's")
        print(f"LongAccel_V: {LongAccel_V}")
        print(f"LatAccel: {LatAccel} G's")
        print(f"LatAccel_V: {LatAccel_V}")
        print(f"YawRate: {YawRate} Deg/s")
        print(f"YawRate_V: {YawRate_V}")

        return {
            "VehicleSpeed": VehicleSpeed,       # km/h
            "LongAccel": LongAccel,             # G's
            "LongAccel_V": LongAccel_V,
            "LatAccel": LatAccel,               # G's
            "LatAccel_V": LatAccel_V,
            "YawRate": YawRate,                 # Deg/s
            "YawRate_V": YawRate_V
        }

    def FoxPi_Brake_Status(self) -> Dict[str, Union[int, float, str]]: #Define FoxPi_Brake_Status to read DID 0x1002 and decode the response byte data into a dict

        byte_data =self.read(0x1003,"FoxPi_Brake_Status") #read DID

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        BrkSw_Sta = byte_data[0] #1s
        BrkSw_V = byte_data[1] #1s
        MCPressure_raw = self.bytes_to_int(byte_data[2:5])*0.1-9.7
        MCPressure = Decimal(str(MCPressure_raw)).quantize(Decimal('0.1'), rounding=ROUND_DOWN) #decimal quantization to 1 decimal place, rounding down
        MCPressure_V = byte_data[5] #1s
        PBA_Active = byte_data[6] #1s
        PBA_Failed = byte_data[7] #1s
        ABS_Active = byte_data[8] #1s
        ABS_Failed = byte_data[9] #1s
        EBD_Active = byte_data[10] #1s
        EBD_Failed = byte_data[11] #1s
        ACC_Availiability = byte_data[12] #1s


        print(f"BrkSw_Sta: {BrkSw_Sta}")
        print(f"BrkSw_V: {BrkSw_V}")
        print(f"MCPressure: {MCPressure} Bar") 
        print(f"MCPressure_V: {MCPressure_V}")
        print(f"PBA_Active: {PBA_Active}")
        print(f"PBA_Failed: {PBA_Failed}")
        print(f"ABS_Active: {ABS_Active}")
        print(f"ABS_Failed: {ABS_Failed}")
        print(f"EBD_Active: {EBD_Active}")
        print(f"EBD_Failed: {EBD_Failed}")
        print(f"ACC_Availiability: {ACC_Availiability}")

        return {
            "BrkSw_Sta": BrkSw_Sta,
            "BrkSw_V": BrkSw_V,
            "MCPressure": MCPressure,
            "MCPressure_V": MCPressure_V,
            "PBA_Active": PBA_Active,
            "PBA_Failed": PBA_Failed,
            "ABS_Active": ABS_Active,
            "ABS_Failed": ABS_Failed,
            "EBD_Active": EBD_Active,
            "EBD_Failed": EBD_Failed,
            "ACC_Availiability": ACC_Availiability
        }

    def FoxPi_WheelSpeed(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_WheelSpeed to read DID 0x1002 and decode the response byte data into a dict

        byte_data =self.read(0x1004,"FoxPi_Brake_Status")

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        RR_RawwhlSpeed = self.bytes_to_int(byte_data[:3])*0.0625
        RR_RawwhlSpeed_V = byte_data[3] #1S
        LR_RawwhlSpeed = self.bytes_to_int(byte_data[4:7])*0.0625
        LR_RawwhlSpeed_V = byte_data[7] #1S
        RF_RawwhlSpeed = self.bytes_to_int(byte_data[8:11])*0.0625
        RF_RawwhlSpeed_V = byte_data[11] #1S
        LF_RawwhlSpeed = self.bytes_to_int(byte_data[12:15])*0.0625
        LF_RawwhlSpeed_V = byte_data[15]


        print(f"RR_RaqwhlSpeed: {Decimal(str(RR_RawwhlSpeed)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN)} km/h")#decimal quantization to 1 decimal place, rounding down
        print(f"RR_RaqwhlSpeed_V: {RR_RawwhlSpeed_V}")
        print(f"LR_RawwhlSpeed: {Decimal(str(LR_RawwhlSpeed)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN)} km/h")
        print(f"LR_RawwhlSpeed_V: {LR_RawwhlSpeed_V}")
        print(f"RF_RawwhlSpeed: {Decimal(str(RF_RawwhlSpeed)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN)} km/h")
        print(f"RF_RawwhlSpeed_V: {RF_RawwhlSpeed_V}")
        print(f"LF_RawwhlSpeed: {Decimal(str(LF_RawwhlSpeed)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN)} km/h")
        print(f"LF_RawwhlSpeed_V: {LF_RawwhlSpeed_V}")

        return {
            "RR_RawwhlSpeed": Decimal(str(RR_RawwhlSpeed)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN),
            "RR_RawwhlSpeed_V": RR_RawwhlSpeed_V,
            "LR_RawwhlSpeed": Decimal(str(LR_RawwhlSpeed)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN),
            "LR_RawwhlSpeed_V": LR_RawwhlSpeed_V,
            "RF_RawwhlSpeed": Decimal(str(RF_RawwhlSpeed)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN),
            "RF_RawwhlSpeed_V": RF_RawwhlSpeed_V,
            "LF_RawwhlSpeed": Decimal(str(LF_RawwhlSpeed)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN),
            "LF_RawwhlSpeed_V": LF_RawwhlSpeed_V
        }

    def FoxPi_EPS_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_EPS_Status to read DID 0x1002 and decode the response byte data into a dict
        
        byte_data =self.read(0x1005,"FoxPi_EPS_Status")

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        SAS_Angle = self.bytes_to_int(byte_data[:4])*0.1-900
        SAS_V = byte_data[4]
        SAS_CAL = byte_data[5]
        EPS_AOI_Control = byte_data[6]
        EpasFailed = byte_data[7]
        EPS_TOI_Activation = byte_data[8]
        EPS_TOI_Unavailable = byte_data[9]
        EPS_TOI_Fault = byte_data[10]


        print(f"SAS_Angle: {SAS_Angle}")
        print(f"SAS_V: {SAS_V}")
        print(f"SAS_CAL: {SAS_CAL}")
        print(f"EPS_AOI_Control: {EPS_AOI_Control}")
        print(f"EpasFailed: {EpasFailed}")
        print(f"EPS_TOI_Activation: {EPS_TOI_Activation}")
        print(f"EPS_TOI_Unavailable: {EPS_TOI_Unavailable}")
        print(f"EPS_TOI_Fault: {EPS_TOI_Fault}")

        return {
            "SAS_Angle": SAS_Angle,
            "SAS_V": SAS_V,
            "SAS_CAL": SAS_CAL,
            "EPS_AOI_Control": EPS_AOI_Control,
            "EpasFailed": EpasFailed,
            "EPS_TOI_Activation": EPS_TOI_Activation,
            "EPS_TOI_Unavailable": EPS_TOI_Unavailable,
            "EPS_TOI_Fault": EPS_TOI_Fault
        }

    def FoxPi_Button_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Button_Status to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x1006, "FoxPi_Button_Status")

        #Get the raw signal value from the response byte array.
        
        SWC1 = bin(byte_data[0])[2:].zfill(8)
        SWC2 = bin(byte_data[1])[2:].zfill(8)
        SWC1_bit = [int(bit) for bit in SWC1]
        SWC2_bit = [int(bit) for bit in SWC2]

        print(f"SWC_ACC_sta: {SWC1_bit[7]}")
        print(f"SWC_CHANCEl_Sta: {SWC1_bit[6]}")
        print(f"SWC_SET_down_Sta: {SWC1_bit[5]}")
        print(f"SWC_RES_up__Sta: {SWC1_bit[4]}")
        print(f"SWC_Distance_Sta: {SWC1_bit[3]}")
        print(f"SWC_mode_Sta: {SWC1_bit[2]}")
        print(f"SWC_Up_Sta: {SWC1_bit[1]}")
        print(f"SWC_Down_Sta: {SWC1_bit[0]}")
        print(f"SWC_Left_Sta: {SWC2_bit[7]}")
        print(f"SWC_Right_Sta: {SWC2_bit[6]}")
        print(f"SWC_RegenDown: {SWC2_bit[5]}")
        print(f"SWC_Undefined_Sta: {SWC2_bit[4]}")
        print(f"SWC_VR_Sta: {SWC2_bit[3]}")
        print(f"SWC_LKA_Sta: {SWC2_bit[2]}")
        print(f"SWC_RegenUp: {SWC2_bit[1]}")
        print(f"SWC_Trip_Sta: {SWC2_bit[0]}")

        return {
            "SWC_ACC_sta": SWC1_bit[7],
            "SWC_CANCEL_Sta": SWC1_bit[6],
            "SWC_SET_down_Sta": SWC1_bit[5],
            "SWC_RES_up_Sta": SWC1_bit[4],
            "SWC_Distance_Sta": SWC1_bit[3],
            "SWC_mode_Sta": SWC1_bit[2],
            "SWC_Up_Sta": SWC1_bit[1],
            "SWC_Down_Sta": SWC1_bit[0],
            "SWC_Left_Sta": SWC2_bit[7],
            "SWC_Right_Sta": SWC2_bit[6],
            "SWC_RegenDown": SWC2_bit[5],
            "SWC_Undefined_Sta": SWC2_bit[4],
            "SWC_VR_Sta": SWC2_bit[3],
            "SWC_LKA_Sta": SWC2_bit[2],
            "SWC_RegenUp": SWC2_bit[1],
            "SWC_Trip_Sta": SWC2_bit[0]
        }

    def FoxPi_USS_Distance(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_USS_Distance to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x1007, "FoxPi_USS_Distance")

        #Get the raw signal value from the response byte array.

        PAS_A1 = [int(bit) for bit in bin(byte_data[0])[2:].zfill(8)]
        PAS_A2 = [int(bit) for bit in bin(byte_data[1])[2:].zfill(8)]
        PAS_A3 = [int(bit) for bit in bin(byte_data[2])[2:].zfill(8)]
        PAS_A4 = [int(bit) for bit in bin(byte_data[3])[2:].zfill(8)]

        PAS_A_RMR = self.bits_to_int(PAS_A1[4:8]) #4bit
        PAS_A_RML = self.bits_to_int(PAS_A1[:4]) #4bit
        PAS_A_RCR = self.bits_to_int(PAS_A2[4:8]) #4bit
        PAS_A_RCL = self.bits_to_int(PAS_A2[:4]) #4bit
        PAS_A_FMR = self.bits_to_int(PAS_A3[4:8]) #4bit
        PAS_A_FML = self.bits_to_int(PAS_A3[:4]) #4bit
        PAS_A_FCR = self.bits_to_int(PAS_A4[4:8]) #4bit
        PAS_A_FCL = self.bits_to_int(PAS_A4[:4]) #4bit
        PAS_D_RMR = byte_data[4]
        PAS_D_RML = byte_data[5]
        PAS_D_RCR = byte_data[6]
        PAS_D_RCL = byte_data[7]
        PAS_D_FMR = byte_data[8]
        PAS_D_FML = byte_data[9]
        PAS_D_FCR = byte_data[10]
        PAS_D_FCL = byte_data[11]
        APS_D_FLL = byte_data[12]
        APS_D_FLR = byte_data[13]
        APS_D_RLL = byte_data[14]
        APS_D_RLR = byte_data[15]
        PAS_Chime = byte_data[16]
        PAS_SNSR_Layout = byte_data[17]
        PAS_Mod_Operation = byte_data[18]
        PAS_Sta_F_Sys = byte_data[19]
        
        print(f"PAS_A_RMR: {PAS_A_RMR}")
        print(f"PAS_A_RML: {PAS_A_RML}")
        print(f"PAS_A_RCR: {PAS_A_RCR}")
        print(f"PAS_A_RCL: {PAS_A_RCL}")
        print(f"PAS_A_FMR: {PAS_A_FMR}")
        print(f"PAS_A_FML: {PAS_A_FML}")
        print(f"PAS_A_FCR: {PAS_A_FCR}")
        print(f"PAS_A_FCL: {PAS_A_FCL}")
        print(f"PAS_D_RMR: {PAS_D_RMR} cm")
        print(f"PAS_D_RML: {PAS_D_RML} cm")
        print(f"PAS_D_RCR: {PAS_D_RCR} cm")
        print(f"PAS_D_RCL: {PAS_D_RCL} cm")
        print(f"PAS_D_FMR: {PAS_D_FMR} cm")
        print(f"PAS_D_FML: {PAS_D_FML} cm")
        print(f"PAS_D_FCR: {PAS_D_FCR} cm")
        print(f"PAS_D_FCL: {PAS_D_FCL} cm")
        print(f"APS_D_FLL: {APS_D_FLL} cm")
        print(f"APS_D_FLR: {APS_D_FLR} cm")
        print(f"APS_D_RLL: {APS_D_RLL} cm")
        print(f"APS_D_RLR: {APS_D_RLR} cm")
        print(f"PAS_Chime: {PAS_Chime}")
        print(f"PAS_SNSR_Layout: {PAS_SNSR_Layout}")
        print(f"PAS_Mod_Operation: {PAS_Mod_Operation}")
        print(f"PAS_Sta_F_Sys: {PAS_Sta_F_Sys}")

        return {
            "PAS_A_RMR": PAS_A_RMR,
            "PAS_A_RML": PAS_A_RML,
            "PAS_A_RCR": PAS_A_RCR,
            "PAS_A_RCL": PAS_A_RCL,
            "PAS_A_FMR": PAS_A_FMR,
            "PAS_A_FML": PAS_A_FML,
            "PAS_A_FCR": PAS_A_FCR,
            "PAS_A_FCL": PAS_A_FCL,
            "PAS_D_RMR": PAS_D_RMR,
            "PAS_D_RML": PAS_D_RML,
            "PAS_D_RCR": PAS_D_RCR,
            "PAS_D_RCL": PAS_D_RCL,
            "PAS_D_FMR": PAS_D_FMR,
            "PAS_D_FML": PAS_D_FML,
            "PAS_D_FCR": PAS_D_FCR,
            "PAS_D_FCL": PAS_D_FCL,
            "APS_D_FLL": APS_D_FLL,
            "APS_D_FLR": APS_D_FLR,
            "APS_D_RLL": APS_D_RLL,
            "APS_D_RLR": APS_D_RLR,
            "PAS_Chime": PAS_Chime,
            "PAS_SNSR_Layout": PAS_SNSR_Layout,
            "PAS_Mod_Operation": PAS_Mod_Operation,
            "PAS_Sta_F_Sys": PAS_Sta_F_Sys
        }

    def FoxPi_USS_Fault_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_USS_Fault_Status to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x1008, "FoxPi_USS_Fault_Status")

        #Get the raw signal value from the response byte array.

        USS_bit1 = [int(bit) for bit in bin(byte_data[0])[2:].zfill(8)]
        USS_bit2 = [int(bit) for bit in bin(byte_data[1])[2:].zfill(8)]

        print(f"USS_Sta_RMR: {USS_bit1[7]}")
        print(f"USS_Sta_RML: {USS_bit1[6]}")
        print(f"USS_Sta_RCR: {USS_bit1[5]}")
        print(f"USS_Sta_RCL: {USS_bit1[4]}")
        print(f"USS_Sta_FMR: {USS_bit1[3]}")
        print(f"USS_Sta_FML: {USS_bit1[2]}")
        print(f"USS_Sta_FCR: {USS_bit1[1]}")
        print(f"USS_Sta_FCL: {USS_bit1[0]}")
        print(f"USS_Sta_RLR: {USS_bit2[7]}")
        print(f"USS_Sta_RLL: {USS_bit2[6]}")
        print(f"USS_Sta_FLR: {USS_bit2[5]}")
        print(f"USS_Sta_FLL: {USS_bit2[4]}")

        return {
            "USS_Sta_RMR": USS_bit1[7],
            "USS_Sta_RML": USS_bit1[6],
            "USS_Sta_RCR": USS_bit1[5],
            "USS_Sta_RCL": USS_bit1[4],
            "USS_Sta_FMR": USS_bit1[3],
            "USS_Sta_FML": USS_bit1[2],
            "USS_Sta_FCR": USS_bit1[1],
            "USS_Sta_FCL": USS_bit1[0],
            "USS_Sta_RLR": USS_bit2[7],
            "USS_Sta_RLL": USS_bit2[6],
            "USS_Sta_FLR": USS_bit2[5],
            "USS_Sta_FLL": USS_bit2[4]
        }

    def FoxPi_PTG_USS_SW(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_PTG_USS_SW to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x1009, "FoxPi_PTG_USS_SW")
        #Get the raw signal value from the response byte array.
        print(f"PTG_USS_SW_Sta: {byte_data[0]}") #1s

        return {
            "PTG_USS_SW_Sta": byte_data[0]
        }

    def FoxPi_Switch_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Switch_Status to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x100A, "FoxPi_Switch_Status")
        #Get the raw signal value from the response byte array.

        switch_bit1 = [int(bit) for bit in bin(byte_data[0])[2:].zfill(8)]
        switch_bit2 = [int(bit) for bit in bin(byte_data[1])[2:].zfill(8)]

        print(f"Crash Detect Status: {switch_bit1[7]}")
        print(f"Driver Lock Status: {switch_bit1[6]}")
        print(f"All Door Switch Status: {switch_bit1[5]}")
        print(f"Driver Door Switch Status: {switch_bit1[4]}")
        print(f"Passenger Door Switch Status: {switch_bit1[3]}")
        print(f"Rear Left Door Switch Status: {switch_bit1[2]}")
        print(f"Rear Right Door Switch Status: {switch_bit1[1]}")
        print(f"Tailgate Switch Status: {switch_bit1[0]}")
        print(f"Hood Switch Status: {switch_bit2[7]}")

        return {
            "Crash_Detect_Status": switch_bit1[7],
            "Driver_Lock_Status": switch_bit1[6],
            "All_Door_Switch_Status": switch_bit1[5],
            "Driver_Door_Switch_Status": switch_bit1[4],
            "Passenger_Door_Switch_Status": switch_bit1[3],
            "Rear_Left_Door_Switch_Status": switch_bit1[2],
            "Rear_Right_Door_Switch_Status": switch_bit1[1],
            "Tailgate_Switch_Status": switch_bit1[0],
            "Hood_Switch_Status": switch_bit2[7]
        }

    def FoxPi_Lamp_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Lamp_Status to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x100B, "FoxPi_Lamp_Status")

        #Get the raw signal value from the response byte array.

        lamp_bit1 = [int(bit) for bit in bin(byte_data[0])[2:].zfill(8)]
        lamp_bit2 = [int(bit) for bit in bin(byte_data[1])[2:].zfill(8)]
        Column_Turn_lamp_sta = self.bits_to_int(lamp_bit1[6:8]) #2bit

        print(f"Column Turn lamp Switch Status: {Column_Turn_lamp_sta}")
        print(f"Column Dim Switch Status: {lamp_bit1[5]}")
        print(f"Column Pass Switch Status: {lamp_bit1[4]}")
        print(f"Position Lamp Status: {lamp_bit1[3]}")
        print(f"Low Beam Status: {lamp_bit1[2]}")
        print(f"High Beam Status: {lamp_bit1[1]}")
        print(f"Right Daytime Running Light Status {lamp_bit1[0]}")
        print(f"Left Daytime Running Light Status: {lamp_bit2[7]}")
        print(f"Left Turn Lamp Status: {lamp_bit2[6]}")
        print(f"Right Turn Lamp Status: {lamp_bit2[5]}")
        print(f"Brake Lamp Status: {lamp_bit2[4]}")
        print(f"Reverse Lamp Status: {lamp_bit2[3]}")
        print(f"Rear Fog Lamp Status: {lamp_bit2[2]}")

        return {
            "Column_Turn_Lamp_Switch_Status": Column_Turn_lamp_sta,
            "Column_Dim_Switch_Status": lamp_bit1[5],
            "Column_Pass_Switch_Status": lamp_bit1[4],
            "Position_Lamp_Status": lamp_bit1[3],
            "Low_Beam_Status": lamp_bit1[2],
            "High_Beam_Status": lamp_bit1[1],
            "Right_Daytime_Running_Light_Status": lamp_bit1[0],
            "Left_Daytime_Running_Light_Status": lamp_bit2[7],
            "Left_Turn_Lamp_Status": lamp_bit2[6],
            "Right_Turn_Lamp_Status": lamp_bit2[5],
            "Brake_Lamp_Status": lamp_bit2[4],
            "Reverse_Lamp_Status": lamp_bit2[3],
            "Rear_Fog_Lamp_Status": lamp_bit2[2]
        }

    def FoxPi_Lamp_Ctrl(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Lamp_Ctrl to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x100C, "FoxPi_Lamp_Ctrl")

        #Get the raw signal value from the response byte array.

        Lamp_ctrl_bit1 = [int(bit) for bit in bin(byte_data[0])[2:].zfill(8)]
        Lamp_ctrl_bit2 = [int(bit) for bit in bin(byte_data[1])[2:].zfill(8)]
        Lamp_ctrl_bit3 = [int(bit) for bit in bin(byte_data[2])[2:].zfill(8)]
        Control_area = self.bits_to_int(Lamp_ctrl_bit3[:3]) #3bit
        RGB_Color = byte_data[3]
        Bright = byte_data[4]
        Mode = byte_data[5]


        print(f"Position_Lamp_Control_Enable: {Lamp_ctrl_bit1[7]}")
        print(f"Position_Lamp: {Lamp_ctrl_bit1[6]}")
        print(f"Low_Beam_Control_Enable: {Lamp_ctrl_bit1[5]}")
        print(f"Low_Beam: {Lamp_ctrl_bit1[4]}")
        print(f"High_Beam_Control_Enable: {Lamp_ctrl_bit1[3]}")
        print(f"High_Beam: {Lamp_ctrl_bit1[2]}")
        print(f"Right_Daytime_Running_Light_Control_Enable: {Lamp_ctrl_bit1[1]}")
        print(f"Right_Daytime_Running_Light: {Lamp_ctrl_bit1[0]}")

        print(f"Left_Daytime_Running_Light_Control_Enable: {Lamp_ctrl_bit2[7]}")
        print(f"Left_Daytime_Running_Light: {Lamp_ctrl_bit2[6]}")
        print(f"Left_TurnLamp_Control_Enable: {Lamp_ctrl_bit2[5]}")
        print(f"Left_TurnLamp: {Lamp_ctrl_bit2[4]}")
        print(f"Right_TurnLamp_Control_Enable: {Lamp_ctrl_bit2[3]}")
        print(f"Right_TurnLamp: {Lamp_ctrl_bit2[2]}")
        print(f"Brake_Lamp_Control_Enable: {Lamp_ctrl_bit2[1]}")
        print(f"Brake_Lamp: {Lamp_ctrl_bit2[0]}")

        print(f"Reverse_Lamp_Control_Enable: {Lamp_ctrl_bit3[7]}")
        print(f"Reverse_Lamp: {Lamp_ctrl_bit3[6]}")
        print(f"Rear_Fog_Lamp_Control_Enable: {Lamp_ctrl_bit3[5]}")
        print(f"Rear_Fog_Lamp: {Lamp_ctrl_bit3[4]}")
        print(f"Amblight_Control_Enable: {Lamp_ctrl_bit3[3]}")
        print(f"Control area: {Control_area}")
        print(f"RGB_Color: \033[91mFF\033[0m" if RGB_Color==255 else f"RGB_Color: {RGB_Color}")
        print(f"Bright: \033[91mFF\033[0m" if Bright==255 else f"Bright: {Bright}")
        print(f"Mode: \033[91mFF\033[0m" if Mode==255 else f"Mode: {Mode}")

        FF = "\033[91mFF\033[0m"

        return {
            "Position_Lamp_Control_Enable": Lamp_ctrl_bit1[7],
            "Position_Lamp": Lamp_ctrl_bit1[6],
            "Low_Beam_Control_Enable": Lamp_ctrl_bit1[5],
            "Low_Beam": Lamp_ctrl_bit1[4],
            "High_Beam_Control_Enable": Lamp_ctrl_bit1[3],
            "High_Beam": Lamp_ctrl_bit1[2],
            "Right_Daytime_Running_Light_Control_Enable": Lamp_ctrl_bit1[1],
            "Right_Daytime_Running_Light": Lamp_ctrl_bit1[0],

            "Left_Daytime_Running_Light_Control_Enable": Lamp_ctrl_bit2[7],
            "Left_Daytime_Running_Light": Lamp_ctrl_bit2[6],
            "Left_TurnLamp_Control_Enable": Lamp_ctrl_bit2[5],
            "Left_TurnLamp": Lamp_ctrl_bit2[4],
            "Right_TurnLamp_Control_Enable": Lamp_ctrl_bit2[3],
            "Right_TurnLamp": Lamp_ctrl_bit2[2],
            "Brake_Lamp_Control_Enable": Lamp_ctrl_bit2[1],
            "Brake_Lamp": Lamp_ctrl_bit2[0],

            "Reverse_Lamp_Control_Enable": Lamp_ctrl_bit3[7],
            "Reverse_Lamp": Lamp_ctrl_bit3[6],
            "Rear_Fog_Lamp_Control_Enable": Lamp_ctrl_bit3[5],
            "Rear_Fog_Lamp": Lamp_ctrl_bit3[4],
            "Amblight_Control_Enable": Lamp_ctrl_bit3[3],
            "Control_Area": Control_area,

            "RGB_Color": FF if RGB_Color == 255 else RGB_Color,
            "Bright": FF if Bright == 255 else Bright,
            "Mode": FF if Mode == 255 else Mode
        }

    def FoxPi_Battery_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Battery_Status to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x100D, "FoxPi_Battery_Status")
        
        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        LVBattDet12V = byte_data[0]*0.1 #1s
        HVBattSOC = byte_data[1]*0.4 #1s
        CellTempAvg = byte_data[2]-40 #1s
        battery_bit4 = [int(bit) for bit in bin(byte_data[3])[2:].zfill(8)]

        print(f"LVBattDet12V: {LVBattDet12V} V")
        print(f"HVBattSOC: {HVBattSOC} %")
        print(f"CellTempAvg: {CellTempAvg} Deg^C")
        print(f"HVBContactorSta: {battery_bit4[1]}")
        print(f"HVBattErr: {battery_bit4[0]}")

        return {
            "LVBattDet12V": LVBattDet12V,         # V
            "HVBattSOC": HVBattSOC,               # %
            "CellTempAvg": CellTempAvg,           # °C
            "HVBContactorSta": battery_bit4[1],
            "HVBattErr": battery_bit4[0]
        }

    def FoxPi_TPMS_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_TPMS_Status to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x100E, "FoxPi_TPMS_Status")

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        LF_Wheel_Pressure = byte_data[0]*0.25+7.26
        RF_Wheel_Pressure = byte_data[1]*0.25+7.26
        LR_Wheel_Pressure = byte_data[2]*0.25+7.26
        RR_Wheel_Pressure = byte_data[3]*0.25+7.26
        LF_Wheel_Temperature = byte_data[4]-40
        RF_Wheel_Temperature = byte_data[5]-40
        LR_Wheel_Temperature = byte_data[6]-40
        RR_Wheel_Temperature = byte_data[7]-40
        LF_Low_Pressure_Threshold = byte_data[8]*0.25+7.26
        RF_Low_Pressure_Threshold = byte_data[9]*0.25+7.26
        LR_Low_Pressure_Threshold = byte_data[10]*0.25+7.26
        RR_Low_Pressure_Threshold = byte_data[11]*0.25+7.26
        TPMS_bit13 = [int(bit) for bit in bin(byte_data[12])[2:].zfill(8)]
        TPMSWarnindi = self.bits_to_int(TPMS_bit13[6:8]) #2bit

        print(f"LF_Wheel_Pressure: {LF_Wheel_Pressure} psi")
        print(f"RF_Wheel_Pressure: {RF_Wheel_Pressure} psi")
        print(f"LR_Wheel_Pressure: {LR_Wheel_Pressure} psi")
        print(f"RR_Wheel_Pressure: {RR_Wheel_Pressure} psi")
        print(f"LF_Wheel_Temperature: {LF_Wheel_Temperature} Deg^C")
        print(f"RF_Wheel_Temperature: {RF_Wheel_Temperature} Deg^C")
        print(f"LR_Wheel_Temperature: {LR_Wheel_Temperature} Deg^C")
        print(f"RR_Wheel_Temperature: {RR_Wheel_Temperature} Deg^C")
        print(f"LF_Low_Pressure_Threshold: {LF_Low_Pressure_Threshold} psi")
        print(f"RF_Low_Pressure_Threshold: {RF_Low_Pressure_Threshold} psi")
        print(f"LR_Low_Pressure_Threshold: {LR_Low_Pressure_Threshold} psi")
        print(f"RR_Low_Pressure_Threshold: {RR_Low_Pressure_Threshold} psi")
        print(f"TPMSWarnindi: {TPMSWarnindi}")

        return {
            "LF_Wheel_Pressure": LF_Wheel_Pressure,
            "RF_Wheel_Pressure": RF_Wheel_Pressure,
            "LR_Wheel_Pressure": LR_Wheel_Pressure,
            "RR_Wheel_Pressure": RR_Wheel_Pressure,
            "LF_Wheel_Temperature": LF_Wheel_Temperature,
            "RF_Wheel_Temperature": RF_Wheel_Temperature,
            "LR_Wheel_Temperature": LR_Wheel_Temperature,
            "RR_Wheel_Temperature": RR_Wheel_Temperature,
            "LF_Low_Pressure_Threshold": LF_Low_Pressure_Threshold,
            "RF_Low_Pressure_Threshold": RF_Low_Pressure_Threshold,
            "LR_Low_Pressure_Threshold": LR_Low_Pressure_Threshold,
            "RR_Low_Pressure_Threshold": RR_Low_Pressure_Threshold,
            "TPMSWarnindi": TPMSWarnindi
        }

    def FoxPi_Pedal_position(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Pedal_position to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x100F,"FoxPi_Pedal_position")

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        ActAPSPosn = byte_data[0]*0.392
        BrkPedalPos = self.bytes_to_int(byte_data[1:3])*0.4

        print(f"ActAPSPosn: {ActAPSPosn} %")
        print(f"BrkPedalPos: {BrkPedalPos} %")

        return {
            "ActAPSPosn": ActAPSPosn,
            "BrkPedalPos": BrkPedalPos
        }

    def FoxPi_Motor_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Motor_Status to read DID 0x1002 and decode the response byte data into a dict
        
        byte_data = self.read(0x1010,"FoxPi_Motor_Status")

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        Rr_TqSource = byte_data[0]
        Rr_TMTqReq_toNidec = self.bytes_to_int(byte_data[1:3])-530
        Rr_EDURealTMTq_Nidec = self.bytes_to_int(byte_data[3:5])-1023
        Rr_MotorAvailTq_Nidec = self.bytes_to_int(byte_data[5:7])-1023
        Rr_RegenAvailTq_Nidec = self.bytes_to_int(byte_data[7:9])-1023
        Rr_TMSpd_Nidec = self.bytes_to_int(byte_data[9:11])-32767

        print(f"Rr_TqSource: {Rr_TqSource}")
        print(f"Rr_TMTqReq_toNidec: {Rr_TMTqReq_toNidec} Nm")
        print(f"Rr_EDURealTMTq_Nidec: {Rr_EDURealTMTq_Nidec} Nm")
        print(f"Rr_MotorAvailTq_Nidec: {Rr_MotorAvailTq_Nidec} Nm")
        print(f"Rr_RegenAvailTq_Nidec: {Rr_RegenAvailTq_Nidec} Nm")
        print(f"Rr_TMSpd_Nidec: {Rr_TMSpd_Nidec} rpm")

        return {
            "Rr_TqSource": Rr_TqSource,
            "Rr_TMTqReq_toNidec": Rr_TMTqReq_toNidec,           # Nm
            "Rr_EDURealTMTq_Nidec": Rr_EDURealTMTq_Nidec,       # Nm
            "Rr_MotorAvailTq_Nidec": Rr_MotorAvailTq_Nidec,     # Nm
            "Rr_RegenAvailTq_Nidec": Rr_RegenAvailTq_Nidec,     # Nm
            "Rr_TMSpd_Nidec": Rr_TMSpd_Nidec                    # rpm
        }

    def FoxPi_Shifter_allow(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Shifter_allow to read DID 0x1002 and decode the response byte data into a dict
        
        byte_data = self.read(0x1011,"FoxPi_Shifter_allow")

        #Get the raw signal value from the response byte array.

        VTQD_ExternalTqAllow_flg = byte_data[0] #1s
        VTQD_ExtShftAllow_flg = byte_data[1] #1s
        VTQD_ExtDoorAllow_flg = byte_data[2] #1s

        print(f"VTQD_ExternalTqAllow_flg: {VTQD_ExternalTqAllow_flg}")
        print(f"VTQD_ExtShftAllow_flg: {VTQD_ExtShftAllow_flg}")
        print(f"VTQD_ExtDoorAllow_flg: {VTQD_ExtDoorAllow_flg}")

        return {
            "VTQD_ExternalTqAllow_flg": VTQD_ExternalTqAllow_flg,
            "VTQD_ExtShftAllow_flg": VTQD_ExtShftAllow_flg,
            "VTQD_ExtDoorAllow_flg": VTQD_ExtDoorAllow_flg
        }

    def FoxPi_Ctrl_Enable_Switch(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Ctrl_Enable_Switch to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x1012,"FoxPi_Ctrl_Enable_Switch")
        
        #Get the raw signal value from the response byte array.

        Ctrl_bit1 = [int(bit) for bit in bin(byte_data[0])[2:].zfill(8)]
        Ctrl_Enable_Switch = Ctrl_bit1[7]

        print(f"Ctrl_Enable_Switch: \033[91mFF\033[0m"if byte_data[0]==255 else f"Ctrl_Enable_Switch: {Ctrl_Enable_Switch}")

        FF= "\033[91mFF\033[0m"

        return{
            "Ctrl_Enable_Switch": FF if byte_data[0]==255 else Ctrl_Enable_Switch
        }



print(f"{datetime.datetime.now()}: Connecting to vehicle at {DOIP_SERVER_IP} with logical address {DoIP_LOGICAL_ADDRESS}") # print the DOIP_SERVER_IP,DoIP_LOGICAL_ADDRESS and the current time
doip_client = DoIPClient(DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS, protocol_version=3) #creat a DoIP object (IP, Logical Address and DoIP protocol version 3)
uds_connection = DoIPClientUDSConnector(doip_client) #Use the previously created doip_client to construct a connection object for UDS (diagnostic services).
assert uds_connection.is_open #Verify whether the UDS connection has been successfully established
with Client(uds_connection, request_timeout=4, config=get_uds_client()) as client: #Execute it within a context manager so that the connection is automatically closed when finished.
    Foxpi = FoxPiReadDID(client)
    #Foxpi.FoxPi_Driving_Ctrl() 
    #Foxpi.FoxPi_Motion_Status()
    #Foxpi.FoxPi_Brake_Status()
    #Foxpi.FoxPi_WheelSpeed()
    #Foxpi.FoxPi_EPS_Status()
    Foxpi.FoxPi_Button_Status()
    #Foxpi.FoxPi_USS_Distance()
    #Foxpi.FoxPi_USS_Fault_Status()
    #Foxpi.FoxPi_PTG_USS_SW()
    #Foxpi.FoxPi_Switch_Status()
    #Foxpi.FoxPi_Lamp_Status()
    #Foxpi.FoxPi_Lamp_Ctrl()
    #Foxpi.FoxPi_Battery_Status()
    #Foxpi.FoxPi_TPMS_Status()
    #Foxpi.FoxPi_Pedal_position()
    #Foxpi.FoxPi_Motor_Status()
    #Foxpi.FoxPi_Shifter_allow()
    #Foxpi.FoxPi_Ctrl_Enable_Switch()
