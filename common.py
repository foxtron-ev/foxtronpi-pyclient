import logging
from typing import Any
from udsoncan.configs import default_client_config as config


def foxtron_security_algo(level, seed, params=None):
    """
    Security algorithm for FoxtronPI.
    This function is called by udsoncan to generate a key from a seed.
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    backend = default_backend()

    keys = {
        1: bytes.fromhex("A8AB5F37723AF4D22BBC7F47D80F8E39"), #foxtronPi security key 1
        3: bytes.fromhex("8DA76FA39411624E448D2403F8F34ED5"), #foxtronPi security key 5
        5: bytes.fromhex("74EDB045DCBBCF1FE553B53BCF464691"), #foxtronPi security key 5
    }

    if level not in keys:
        raise ValueError(f"Unsupported security level: {level}")

    cipher = Cipher(algorithms.AES(keys[level]), modes.ECB(), backend=backend) # Create an AES-128 ECB mode Cipher object using the corresponding level’s key.
    decryptor = cipher.decryptor() #Create a decryptor for decryption
    key = decryptor.update(seed) + decryptor.finalize() #Feed the seed data into the decryptor to perform AES-ECB decryption and obtain the resulting key.
    return key


def get_uds_client() -> dict[str, Any]:
    

    # Set udsoncan to not validate the length of DID data, as it can be variable.
    
    config["security_algo"] = foxtron_security_algo #security_algo use the foxtron_security_algo function
    config["data_identifiers"] = {
        0x0E04: "16s",  # FD system time YYYYmmddTHHMMSSZ,  16 bytes
        0xF090: "22s",  # FVT VIN
        0xF16F: "10s",  # CAN message map vesrion
        0xF181: "10s",  # Partition number
        0xF184: "10s",  # Application software fingerprint
        0xF187: "10s",  # Spare part number
        0xF190: "17s",  # VIN code
        0xF193: "10s",  # HW version
        0xF195: "10s",  # SW version

        #FoxPi, s=byte
        0x1001: "21s", # FoxPi_Driving_Ctrl
        0x1002: "13s", # FoxPi_Motion_Status
        0x1003: "13s", # FoxPi_Brake_Status
        0x1004: "16s", # FoxPi_WheelSpeed
        0x1005: "11s", # FoxPi_EPS_Status
        0x1006: "2s", # FoxPi_Button_Status
        0x1007: "20s", # FoxPi_USS_Distance
        0x1008: "2s", # FoxPi_USS_Fault_Status
        0x1009: "1s", # FoxPi_PTG_USS_SW
        0x100A: "2s", # FoxPi_Switch_Status
        0x100B: "2s", # FoxPi_Lamp_Status
        0x100C: "6s", # FoxPi_Lamp_Ctrl
        0x100D: "4s", # FoxPi_Battery_Status
        0x100E: "13s", # FoxPi_TPMS_Status
        0x100F: "3s", # FoxPi_Pedal_position
        0x1010: "11s", # FoxPi_Motor_Status
        0x1011: "3s", # FoxPi_Shifter_allow
        0x1012: "1s", # FoxPi_Ctrl_Enable_Switch
    }
    return config