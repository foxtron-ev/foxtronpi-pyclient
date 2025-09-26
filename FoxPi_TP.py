# FoxPi_TP.py


class FoxPiTP:
      
    def __init__(self, client): # Initialization function; pass in the client parameter, which is the UDS communication object.
        self.client = client

    def TesterPresent(self): # Define a TesterPresent function to send a tester present request to the ECU.
        with self.client.suppress_positive_response():
            self.client.tester_present()