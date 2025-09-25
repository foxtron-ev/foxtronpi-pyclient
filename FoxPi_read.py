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


        Acc = self.bytes_to_int(byte_data[:3])*0.05-15 #3s,*Factor-offset
        Acc_A = byte_data[3] #1S
        Spd = self.bytes_to_int(byte_data[4:7])*0.125 #3s
        Spd_A = byte_data[7] #1S

        Angle_V = byte_data[8] #1S
        Angle_Req = byte_data[9] #1s
        Angle = self.bytes_to_int(byte_data[10:14])*0.1-900 #4s,*Factor-offset
        Torque_V = byte_data[14] #1S
        Torque_Req = byte_data[15] #1s
        Torque = self.bytes_to_int(byte_data[16:19])*0.01-10 #4s,*Factor-offset

        #APS_byte= decimal_values[18]
        APS_bit= bin(byte_data[19])[2:].zfill(8) #[2:]cut off the '0b' prefix,.zfill(8) guarantees 8 bits
        bit_list= [int(bit) for bit in APS_bit] # Convert the binary string to a list of integers

        APS_flg = bit_list[7] #1bit
        APS_Sta = self.bits_to_int(bit_list[4:7]) #Convert the bits to an integer
        APS_Shift = self.bits_to_int(bit_list[0:4]) #Convert the bits to an integer
        APS_Spd = byte_data[20]*0.125 #1S
               

         # FF mechanism: if the value is FF, output 'FF' directly
        return {
            "Acc": "FF" if all(b==255 for b in byte_data[:3]) else Acc,
            "Acc_A": "FF" if Acc_A==255 else Acc_A,
            "Spd": "FF" if all(b==255 for b in byte_data[4:7]) else Spd,
            "Spd_A": "FF" if Spd_A==255 else Spd_A,
            "Angle_V": "FF" if Angle_V==255 else Angle_V,
            "Angle_Req": "FF" if Angle_Req==255 else Angle_Req,
            "Angle": "FF" if all(b==255 for b in byte_data[10:13]) else Angle,
            "Torque_V": "FF" if Torque_V==255 else Torque_V,
            "Torque_Req": "FF" if Torque_Req==255 else Torque_Req,
            "Torque": "FF" if all(b==255 for b in byte_data[15:18]) else Torque,
            "APS_flg": "FF" if bit_list == [1]*8 else APS_flg,
            "APS_Sta": "FF" if bit_list == [1]*8 else APS_Sta,
            "APS_Shift": "FF" if bit_list == [1]*8 else APS_Shift,
            "APS_Spd": "FF" if byte_data[20]==255 else APS_Spd
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

        return {
            "VehicleSpeed": VehicleSpeed,       # km/h
            "LongAcc": LongAccel,             # G's
            "LongAcc_V": LongAccel_V,
            "LatAcc": LatAccel,               # G's
            "LatAcc_V": LatAccel_V,
            "YawRate": YawRate,                 # Deg/s
            "YawRate_V": YawRate_V
        }

    def FoxPi_Brake_Status(self) -> Dict[str, Union[int, float, str]]: #Define FoxPi_Brake_Status to read DID 0x1002 and decode the response byte data into a dict

        byte_data =self.read(0x1003,"FoxPi_Brake_Status") #read DID

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        Break_Sw = byte_data[0] #1s
        Break_Sw_V= byte_data[1] #1s
        MCPressure_raw = self.bytes_to_int(byte_data[2:5])*0.1-9.7
        MCPressure = Decimal(str(MCPressure_raw)).quantize(Decimal('0.1'), rounding=ROUND_DOWN) #decimal quantization to 1 decimal place, rounding down
        MCPressure_V = byte_data[5] #1s
        PBA_Act = byte_data[6] #1s
        PBA_Flt = byte_data[7] #1s
        ABS_Act = byte_data[8] #1s
        ABS_Flt = byte_data[9] #1s
        EBD_Act = byte_data[10] #1s
        EBD_Flt = byte_data[11] #1s
        ACC_Avail = byte_data[12] #1s


        return {
            "Break_Sw": Break_Sw,
            "Break_Sw_V": Break_Sw_V,
            "MCPressure": MCPressure,
            "MCPressure_V": MCPressure_V,
            "PBA_Act": PBA_Act,
            "PBA_Flt": PBA_Flt,
            "ABS_Act": ABS_Act,
            "ABS_Flt": ABS_Flt,
            "EBD_Act": EBD_Act,
            "EBD_Flt": EBD_Flt,
            "ACC_Avail": ACC_Avail
        }

    def FoxPi_WheelSpeed(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_WheelSpeed to read DID 0x1002 and decode the response byte data into a dict

        byte_data =self.read(0x1004,"FoxPi_WheelSpeed_Status")

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        RR_whlSpeed = self.bytes_to_int(byte_data[:3])*0.0625
        RR_whlSpeed_V = byte_data[3] #1S
        LR_whlSpeed = self.bytes_to_int(byte_data[4:7])*0.0625
        LR_whlSpeed_V = byte_data[7] #1S
        RF_whlSpeed = self.bytes_to_int(byte_data[8:11])*0.0625
        RF_whlSpeed_V = byte_data[11] #1S
        LF_whlSpeed = self.bytes_to_int(byte_data[12:15])*0.0625
        LF_whlSpeed_V = byte_data[15]


        return {
            "RR_WhlSpeed": Decimal(str(RR_whlSpeed)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN),
            "RR_WhlSpeed_V": RR_whlSpeed_V,
            "LR_WhlSpeed": Decimal(str(LR_whlSpeed)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN),
            "LR_WhlSpeed_V": LR_whlSpeed_V,
            "RF_WhlSpeed": Decimal(str(RF_whlSpeed)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN),
            "RF_WhlSpeed_V": RF_whlSpeed_V,
            "LF_WhlSpeed": Decimal(str(LF_whlSpeed)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN),
            "LF_WhlSpeed_V": LF_whlSpeed_V
        }

    def FoxPi_EPS_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_EPS_Status to read DID 0x1002 and decode the response byte data into a dict
        
        byte_data =self.read(0x1005,"FoxPi_EPS_Status")

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        SAS_Angle = self.bytes_to_int(byte_data[:4])*0.1-900
        SAS_V = byte_data[4]
        SAS_CAL = byte_data[5]
        EPS_AOI_Ctrl = byte_data[6]
        EPS_Flt = byte_data[7]
        EPS_TOI_Act = byte_data[8]
        EPS_TOI_Avail = byte_data[9]
        EPS_TOI_Flt = byte_data[10]

        return {
            "SAS_Angle": Decimal(str(SAS_Angle)).quantize(Decimal('0.1'), rounding=ROUND_DOWN),
            "SAS_V": SAS_V,
            "SAS_CAL": SAS_CAL,
            "EPS_AOI_Ctrl": EPS_AOI_Ctrl,
            "EPS_Flt": EPS_Flt,
            "EPS_TOI_Act": EPS_TOI_Act,
            "EPS_TOI_Avail": EPS_TOI_Avail,
            "EPS_TOI_Flt": EPS_TOI_Flt
        }

    def FoxPi_Button_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Button_Status to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x1006, "FoxPi_Button_Status")

        #Get the raw signal value from the response byte array.
        
        SWC1 = bin(byte_data[0])[2:].zfill(8)
        SWC2 = bin(byte_data[1])[2:].zfill(8)
        SWC1_bit = [int(bit) for bit in SWC1]
        SWC2_bit = [int(bit) for bit in SWC2]

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

    def FoxPi_Switch_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Switch_Status to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x100A, "FoxPi_Switch_Status")
        #Get the raw signal value from the response byte array.

        switch_bit1 = [int(bit) for bit in bin(byte_data[0])[2:].zfill(8)]
        switch_bit2 = [int(bit) for bit in bin(byte_data[1])[2:].zfill(8)]

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

            "RGB_Color": "FF" if RGB_Color == 255 else RGB_Color,
            "Bright": "FF" if Bright == 255 else Bright,
            "Mode": "FF" if Mode == 255 else Mode
        }

    def FoxPi_Battery_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Battery_Status to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x100D, "FoxPi_Battery_Status")
        
        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        LVBatt12V = byte_data[0]*0.1 #1s
        HVBattSOC = byte_data[1]*0.4 #1s
        HVBattTemp = byte_data[2]-40 #1s
        battery_bit4 = [int(bit) for bit in bin(byte_data[3])[2:].zfill(8)]


        return {
            "LVBatt12V": LVBatt12V,         # V
            "HVBattSOC": HVBattSOC,               # %
            "HVBattTemp": HVBattTemp,           # °C
            "HVBattContactorSta": battery_bit4[1],
            "HVBattErr": battery_bit4[0]
        }

    def FoxPi_Pedal_position(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Pedal_position to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x100F,"FoxPi_Pedal_position")

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        AccelPedalPos = byte_data[0]*0.392
        BrkPedalPos = self.bytes_to_int(byte_data[1:3])*0.4

        return {
            "AccelPedalPos": Decimal(str(AccelPedalPos)).quantize(Decimal('0.001'), rounding=ROUND_DOWN),
            "BrakePedalPos": Decimal(str(BrkPedalPos)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        }

    def FoxPi_Motor_Status(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Motor_Status to read DID 0x1002 and decode the response byte data into a dict
        
        byte_data = self.read(0x1010,"FoxPi_Motor_Status")

        #Get the raw signal value from the response byte array, then compute the physical value using: physical = raw * factor + offset. 
        #The offset may be a negative value, so we'll use subtraction in the calculation
        #if there is no offset(=0) or factor, it is not included in the calculation.

        TqSource = byte_data[0]
        TMTqReq = self.bytes_to_int(byte_data[1:3])-530
        RealTMTq = self.bytes_to_int(byte_data[3:5])-1023
        MotorAvailTq = self.bytes_to_int(byte_data[5:7])-1023
        RegenAvailTq = self.bytes_to_int(byte_data[7:9])-1023
        TMSpd = self.bytes_to_int(byte_data[9:11])-32767

        return {
            "TqSource": TqSource,
            "TMTqReq ": TMTqReq ,           # Nm
            "RealTMTq": RealTMTq,       # Nm
            "MotorAvailTq": MotorAvailTq,     # Nm
            "RegenAvailTq": RegenAvailTq,     # Nm
            "TMSpd": TMSpd                    # rpm
        }

    def FoxPi_Shifter_allow(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Shifter_allow to read DID 0x1002 and decode the response byte data into a dict
        
        byte_data = self.read(0x1011,"FoxPi_Shifter_allow")

        #Get the raw signal value from the response byte array.

        ExtTqAllow_flg = byte_data[0] #1s
        ExtShftAllow_flg = byte_data[1] #1s
        ExtDoorAllow_flg = byte_data[2] #1s


        return {
            "ExtTqAllow_flg": ExtTqAllow_flg,
            "ExtShftAllow_flg": ExtShftAllow_flg,
            "ExtDoorAllow_flg": ExtDoorAllow_flg
        }

    def FoxPi_Ctrl_Enable_Switch(self) -> Dict[str, Union[int, float, str]]:#Define FoxPi_Ctrl_Enable_Switch to read DID 0x1002 and decode the response byte data into a dict

        byte_data = self.read(0x1012,"FoxPi_Ctrl_Enable_Switch")
        
        #Get the raw signal value from the response byte array.

        Ctrl_bit1 = [int(bit) for bit in bin(byte_data[0])[2:].zfill(8)]
        Ctrl_Enable_Switch = Ctrl_bit1[7]

        return{
            "Ctrl_Enable_Switch": "FF" if byte_data[0]==255 else Ctrl_Enable_Switch
        }
