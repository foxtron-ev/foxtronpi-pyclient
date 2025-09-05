# foxpi_ui_pyqt.py — FoxPi DID Control Panel (PyQt5)
# Usage:
#   1) pip install pyqt5
#   2) Ensure your project can import doipclient, udsoncan, FoxPi_write
#   3) python foxpi_ui_pyqt.py
#   4) Click "Connect" first, then select DID, choose whether to use default values, then click "Run"

import sys
from typing import List, Any, Dict

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFormLayout, QLineEdit, QCheckBox, QTextEdit, QMessageBox,
    QSizePolicy, QScrollArea, QFrame
)

# === External modules ===
# These may fail to import if dependencies are not installed.
# In that case, the UI will show an import warning.
try:
    from doipclient import DoIPClient
    from doipclient.connectors import DoIPClientUDSConnector
    from udsoncan.client import Client
    from common import get_uds_client
    from client_config import DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS
    from FoxPi_write import FoxPiWriteDID
    from FoxPi_read import FoxPiReadDID
except Exception as e:
    DoIPClient = DoIPClientUDSConnector = Client = FoxPiWriteDID = object  # type: ignore
    DOIP_SERVER_IP = "0.0.0.0"
    DoIP_LOGICAL_ADDRESS = 0x0000
    IMPORT_ERROR = e
else:
    IMPORT_ERROR = None


def to_number(s: str): # Convert a string to an int or float
    s = s.strip()
    if s == "":
        raise ValueError("Empty string is not a number")
    if ("." in s) or ("e" in s.lower()):
        return float(s)
    return int(s)


class UDSWorker(QThread): # Declare a class that inherits from QThread
    done = pyqtSignal(object) # Declare a signal that will be emitted when the task is done, with an object parameter
    failed = pyqtSignal(str) # Declare a signal that will be emitted when the task fails, with a string parameter

    def __init__(self, WriteDID, ReadDID, wid: int, func, params: List[str], defaults: List[Any], tick_box: bool, inputs: List[str]):
        super().__init__()
        self.WriteDID = WriteDID # FoxPiWriteDID instance
        self.ReadDID = ReadDID # FoxPiReadDID instance
        self.wid = wid # The DID number to write
        self.func = func # The function to call (e.g. FoxPi_Driving_Ctrl)
        self.params = params # Parameter names (e.g. ["AccReq", "TargetSpdReq", ...])
        self.defaults = defaults # Default values for the parameters
        self.tick_box = tick_box # Whether to use default values or user inputs
        self.inputs = inputs # User input values as strings(ex:["1", "20", "-10"])

    def run(self):
        try:
            if self.params: # check the DID whether it requires parameters
                if self.tick_box or not self.inputs: # if have chosen to use default values or no user inputs
                    user_input = self.defaults
                else:
                    user_input = [to_number(x) for x in self.inputs] # convert user input strings to numbers
                result = self.func(user_input)
            else: # if the DID is empty(means DID parameters required)
                if self.defaults:
                    result = self.func(self.defaults)
                else:
                    result = self.func()
            self.done.emit(result) # emit the result to the main thread when done
        except Exception as e:
            self.failed.emit(str(e)) # emit the error message to the main thread when failed


class FoxPiUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FoxPi DID Control Panel") # setup UI window title
        self.resize(900, 650) # setup UI window size
        self.WriteDID = None #This wil be set to FoxPiWriteDID instance after connection. None is not connected state
        self.ReadDID = None
        self.config: Dict[int, Dict[str, Any]] = {} #create empty config dict
        self._build_ui() # call the _build_ui to establish the UI 

    def _build_ui(self):
        root = QVBoxLayout(self) #create the Vertical Layout object

        top = QHBoxLayout() #create the Horizontal Layout object
        self.btn_connect = QPushButton("Connect") #create the connection button,and the text inside the" "will be displayed on the button.
        self.btn_disconnect = QPushButton("Disconnect") #create the Disconnection button, and the text inside the " "  will be displayed on the button.
        self.btn_disconnect.setEnabled(False) #lock the disconnection button if not connected FD.
        top.addWidget(self.btn_connect) #put the connection button into the horizontal layout.
        top.addWidget(self.btn_disconnect) #put the disconnection button into the horizontal layout.
        top.addStretch() # insert a stretchable space that will push the following widgets to the right side of the layout.

        self.combo_did = QComboBox() # QComboBox() is a dropdown list widget.
        self.combo_did.setEnabled(False) #lock the dropdown list if not connected FD.
        self.combo_RWchoose = QComboBox()
        self.combo_RWchoose.addItems(["Write", "Read"]) 
        self.combo_RWchoose.setCurrentIndex(0) #set the default value to "Write"
        self.combo_RWchoose.setEnabled(False)
        top.addWidget(QLabel("Read or Write:")) #Qlable is a text display widget.
        top.addWidget(self.combo_RWchoose) #put the dropdown list into the horizontal layout.
        top.addWidget(QLabel("Select DID:")) #Qlable is a text display widget.
        top.addWidget(self.combo_did) #put the dropdown list into the horizontal layout.
        root.addLayout(top) #put the horizontal layout into the vertical layout.

        self.form_area = QScrollArea() #create a scroll area widget to contain a lot of columns.
        self.form_area.setWidgetResizable(True) # make the scroll area widget(column) resizable.
        self.form_wrap = QWidget() # create a container this can hold other widgets.
        self.form = QFormLayout(self.form_wrap) #QFormLayout() is a Layout configurator: label put on the left, feild put on the right.
        self.form.setLabelAlignment(Qt.AlignRight) # set the left label alignment to right.
        self.form_area.setWidget(self.form_wrap) # put the form_wrap container into the scroll area widget
        root.addWidget(self.form_area) #put the form_area into the vertical layout.

        flags = QHBoxLayout() #create the Horizontal Layout object
        self.chk_use_default = QCheckBox("Use Default Values") #create a checkbox widget
        self.chk_use_default.setChecked(True) #set the checkbox to be checked by default
        self.btn_fill_defaults = QPushButton("Fill Defaults") #create a Fill Defaults button
        self.btn_clear = QPushButton("Clear Fields") #create a Clear Fields button
        flags.addWidget(self.chk_use_default)
        flags.addStretch()
        flags.addWidget(self.btn_fill_defaults)
        flags.addWidget(self.btn_clear)
        root.addLayout(flags)

        run_row = QHBoxLayout() #create the Horizontal Layout object
        self.btn_run = QPushButton("Run Write DID")  #create the RUN button
        self.btn_run.setEnabled(False) #lock the Run button if not connected FD
        run_row.addWidget(self.btn_run)
        run_row.addStretch()
        root.addLayout(run_row)

        root.addWidget(self._hline()) # add a horizontal line to separate the log area from the above widgets.
        self.log = QTextEdit() # QTextEdit() is a multi-line text editing widget.
        self.log.setReadOnly(True) # set the text editing widget to be read-only
        self.log.setPlaceholderText("Connection status, calls and results will be shown here…") # print the placeholder text when the log is empty
        root.addWidget(self.log)

        self.btn_connect.clicked.connect(self.on_connect) # connect the signal to the slot
        self.btn_disconnect.clicked.connect(self.on_disconnect) # disconnect the signal to the slot
        self.combo_did.currentIndexChanged.connect(self.on_did_changed) # when the selected item in the combo box changes, call the on_did_changed function
        self.combo_RWchoose.currentIndexChanged.connect(self.on_mode_changed)
        self.chk_use_default.stateChanged.connect(self.on_use_default_changed) # when the state of the checkbox changes, call the on_use_default_changed function
        self.btn_fill_defaults.clicked.connect(self.on_fill_defaults) # when the Fill Defaults button is clicked, call the on_fill_defaults function
        self.btn_clear.clicked.connect(self.on_clear_fields) # when the Clear Fields button is clicked, call the on_clear_fields function
        self.btn_run.clicked.connect(self.on_run) # when the Run button is clicked, call the on_run function

        if IMPORT_ERROR:
            self.append_log(f"Import warning: {IMPORT_ERROR}")

    def _hline(self):
        line = QFrame() # QFrame() can be create a blank box
        line.setFrameShape(QFrame.HLine) # The setFrameShape() function sets the shape of the frame, and QFrame.HLine represents a horizontal line.
        line.setFrameShadow(QFrame.Sunken) # The setFrameShadow() function sets the shadow style of the frame, and QFrame.Sunken represents a sunken shadow effect.
        return line

    def on_connect(self):
        try:
            self.append_log("Attempting to establish DoIP/UDS connection…")
            doip_client = DoIPClient(DOIP_SERVER_IP, DoIP_LOGICAL_ADDRESS, protocol_version=3)
            uds_connection = DoIPClientUDSConnector(doip_client)
            assert uds_connection.is_open, "UDS connection failed"
            uds_client = Client(uds_connection, request_timeout=4, config=get_uds_client())
            uds_client.open() # open the UDS client connection (like with Client(.....) as client: )
            self.WriteDID = FoxPiWriteDID(uds_client)
            self.ReadDID = FoxPiReadDID(uds_client)
            self.append_log("Connected")

            self.write_config = self._build_write_config(self.WriteDID)
            self.read_config = self._build_read_config(self.ReadDID)
            self.config = self.write_config
            self.populate_did_combo()
            self.btn_connect.setEnabled(False)    #--|
            self.btn_disconnect.setEnabled(True)  #  | update the Connect(can't press)/Disconnect(can press) button status
            self.combo_did.setEnabled(True)       #  | update the DID dropdown list(can press) / run button status(can press)
            self.btn_run.setEnabled(True)         #--|
            self.combo_RWchoose.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed", str(e)) # QMessageBox.critical() is a pop-up window to show the error message
            self.append_log(f"Connection Failed: {e}") # append the error message to the log area

    def on_disconnect(self):
        try:
            if self.WriteDID and hasattr(self.WriteDID, "client"): # check if the WriteDID object exists(Non None) and has a client attribute
                try:
                    self.WriteDID.client.close() #close the UDS client connection
                except Exception as e:
                    self.append_log("\033[91mError while closing UDS client: {e}[0m m/s^2")
                    pass
            self.WriteDID = None
            self.combo_did.clear() #clear the DID dropdown list
            self.form_clear() #
            self.btn_connect.setEnabled(True)     #--|
            self.btn_disconnect.setEnabled(False) #  | update the disconnect(can't press)/connect(can press) button status
            self.combo_did.setEnabled(False)      #  | update the DID dropdown list(can't press) / run button status(can't press)
            self.btn_run.setEnabled(False)        #--|
            self.append_log("Disconnected")
        except Exception as e:
            self.append_log(f"Error while disconnecting: {e}")

    def _build_write_config(self, foxpi) -> Dict[int, Dict[str, Any]]:
        WID_map = {
            1: foxpi.FoxPi_Driving_Ctrl,
            2: foxpi.FoxPi_Lamp_Ctrl,
            3: foxpi.Driving_Ctrl_toFF,
            4: foxpi.FoxPi_Ctrl_Enable_Switch,
        }
        WID_param = {
            1: [
                "AccReq","AccReq_A","TargetSpdReq","TargetSpdReq_A","Angle_Target_Valid","Angle_Target_Req",
                "Angle_Target","Torque_Target_Valid","Torque_Target_Req","Torque_Target","VINP_APSVMCReqA_flg",
                "VINP_APSStaSystem_enum","VINP_APSShiftPosnReq_enum","VINP_APSSpeedCMD_kph"
            ],
            2: [
                "Position_Lamp_Control_Enable","Position_Lamp","Low_Beam_Control_Enable","Low_Beam",
                "High_Beam_Control_Enable","High_Beam","Right_Daytime_Running_Light_Control_Enable",
                "Right_Daytime_Running_Light","Left_Daytime_Running_Light_Control_Enable","Left_Daytime_Running_Light",
                "Left_TurnLamp_Control_Enable","Left_TurnLamp","Right_TurnLamp_Control_Enable","Right_TurnLamp",
                "Brake_Lamp_Control_Enable","Brake_Lamp","Reverse_Lamp_Control_Enable","Reverse_Lamp",
                "Rear_Fog_Lamp_Control_Enable","Rear_Fog_Lamp","Amblight_Control_Enable","Control area",
                "RGB 64 Color","Bright adjustment","Breathing and Alert Mode"
            ],
            3: [],
            4: ["Ctrl_Enable_Switch"],
        }
        default_value = {
            1: [-10, 1, 255.875, 1, 1, 1, -900, 1, 1, -10, 1, 4, 7, 20],
            2: [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,7,63,100,7],
            3: [],
            4: [0]
        }
        cfg = {}
        for i, func in WID_map.items():
            cfg[i] = {
                "func": func, # The function to call (e.g. foxpi.FoxPi_Driving_Ctrl)
                "name": func.__name__, # The name of the function (e.g. "FoxPi_Driving_Ctrl")
                "params": WID_param.get(i, []), # Parameter names (e.g. ["AccReq", "TargetSpdReq", ...])
                "defaults": default_value.get(i, []), # Default values for the parameters(e.g. [-10, 1, 255.875, 1, 1, 1, -900, 1, 1, -10, 1, 4, 7, 20])
            }
        return cfg
    
    def _build_read_config(self, Foxpi) -> Dict[int, Dict[str, Any]]:
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
        cfg_r = {}
        for i, func in RID_map.items():
            cfg_r[i] = {
                "func": func, # The function to call (e.g. foxpi.FoxPi_Driving_Ctrl)
                "name": func.__name__, # The name of the function (e.g. "FoxPi_Driving_Ctrl")
                "params": [], # Parameter names (e.g. ["AccReq", "TargetSpdReq", ...])
                "defaults": [], # Default values for the parameters(e.g. [-10, 1, 255.875, 1, 1, 1, -900, 1, 1, -10, 1, 4, 7, 20])
            }
        return cfg_r

    def populate_did_combo(self): # Populate the DID dropdown list with the config data
        self.combo_did.blockSignals(True) # block the signal to prevent triggering on_did_changed when populating the combo box
        self.combo_did.clear() # clear the combo box 
        for i in sorted(self.config):
            self.combo_did.addItem(f"{self.config[i]['name']}", i) # add items to the combo box with display text (addItem(text, userdata) userdata can be retrieved by currentData())
        self.combo_did.blockSignals(False) # unblock the signal
        
        if self.combo_did.count() > 0: # if combo box has items, select the first item and trigger on_did_changed
            self.combo_did.setCurrentIndex(0) # select the first item
            self.on_did_changed() # manually trigger on_did_changed for the first item

    def on_did_changed(self): # Triggered when the selected DID changes
        wid = self.combo_did.currentData() # get the selected number(e.g. 1, 2, 3, 4)
        mode = self.combo_RWchoose.currentText()
        if wid is None: # if no item is selected, do nothing
            return
        self.form_clear() # clear the form layout
        params = self.config[wid]["params"] # wid=1 e.g. ["AccReq", "TargetSpdReq", ...]
        defaults = self.config[wid]["defaults"] # wid=1 e.g. [-10, 1, 255.875, 1, 1, 1, -900, 1, 1, -10, 1, 4, 7, 20]
        if params:
            for i, p in enumerate(params): # i = index, p = parameter name
                le = QLineEdit() # create a line edit widget for user input
                le.setPlaceholderText(f"{p}") # set the placeholder text to the parameter name
                if i < len(defaults): # if there is a default value for this parameter, set it to the line edit
                    le.setText(str(defaults[i])) # set the default value to the line edit
                le.setEnabled(not self.chk_use_default.isChecked()) # enable/disable the line edit based on the checkbox state
                self.form.addRow(QLabel(p + ":"), le) # add a row to the form layout (left label, right QLineEdit)
        else:
            if mode == "Read":
                self.form.addRow(QLabel("Press Run Read DID button to read values...")) # if DID no needs parameters, show this message
            else:
                self.form.addRow(QLabel("This DID requires no parameters.")) # if DID no needs parameters, show this message
    
    def show_readDid(self, data: Dict[str, Any], editable: bool = False):
        self.form_clear()
        for k in data.keys():
            v = data[k]
            le = QLineEdit()
            le.setText(str(v))
            le.setReadOnly(True)
            le.setStyleSheet("color: blue; background-color: #f0f0f0;")
            le.setEnabled(False)
            self.form.addRow(QLabel(k + ":"), le)

    def on_mode_changed(self):
        mode = self.combo_RWchoose.currentText()
        if mode == "Write":
            self.config = self.write_config
            self.btn_run.setText("Run Write DID")
            self.chk_use_default.setEnabled(True)
            self.btn_fill_defaults.setEnabled(True)
            self.btn_clear.setEnabled(True)
        else:
            self.config = self.read_config
            self.btn_run.setText("Run Read DID")
            self.chk_use_default.setChecked(True)
            self.chk_use_default.setEnabled(False)
            self.btn_fill_defaults.setEnabled(False)
            self.btn_clear.setEnabled(False)
            self.form_clear()
        self.populate_did_combo()

    def form_clear(self):
        while self.form.rowCount(): # rowCount() returns the number of rows in the form layout
            self.form.removeRow(0) # remove the first row until all rows are removed

    def on_use_default_changed(self, state):
        editable = (state != Qt.Checked) # if checkbox is checked, editable = False; if unchecked, editable = True
        for i in range(self.form.rowCount()): # iterate over all rows in the form layout
            field = self.form.itemAt(i, QFormLayout.FieldRole) # QFormLayout.FieldRole gets the right widget (QLineEdit)
            if field is not None and field.widget() and isinstance(field.widget(), QLineEdit):# field is not None, field has a widget, and the widget is a QLineEdit                
                field.widget().setEnabled(editable) # enable/disable the QLineEdit based on the checkbox state

    def on_fill_defaults(self):
        wid = self.combo_did.currentData()
        if wid is None:
            return
        defaults = self.config[wid]["defaults"] # wid=1 e.g. [-10, 1, 255.875, 1, 1, 1, -900, 1, 1, -10, 1, 4, 7, 20]
        idx_val = 0
        for i in range(self.form.rowCount()):
            field = self.form.itemAt(i, QFormLayout.FieldRole) # QFormLayout.FieldRole gets the right widget (QLineEdit)
            if field is not None and isinstance(field.widget(), QLineEdit): # field is not None, field has a widget, and the widget is a QLineEdit
                text = str(defaults[idx_val]) if idx_val < len(defaults) else "" # get the default value or empty string if out of range
                field.widget().setText(text) # set the default value to the QLineEdit
                idx_val += 1

    def on_clear_fields(self):
        for i in range(self.form.rowCount()):
            field = self.form.itemAt(i, QFormLayout.FieldRole)
            if field is not None and isinstance(field.widget(), QLineEdit):
                field.widget().clear() # clear the text in the QLineEdit

    def on_run(self):
        if not self.WriteDID: # check whether connected
            QMessageBox.warning(self, "Not Connected", "Please connect first")
            return
        
        mode = self.combo_RWchoose.currentText()
        wid = self.combo_did.currentData()
        cfg = self.config.get(wid)
        if not cfg:
            return
        
        func = cfg["func"]
        params = cfg["params"]
        defaults = cfg["defaults"]
        tick_box = self.chk_use_default.isChecked()

        inputs: List[str] = []
        if mode =="Write" and params and not tick_box:
            for i in range(self.form.rowCount()):
                field = self.form.itemAt(i, QFormLayout.FieldRole)
                if field is not None and isinstance(field.widget(), QLineEdit):
                    inputs.append(field.widget().text())
            self.append_log(f"Running: {cfg['name']}, use_defaults={tick_box}, inputs={inputs}")
        else:
            self.append_log(f"Running: {cfg['name']}")

        
        self.btn_run.setEnabled(False) # disable the Run button to prevent the user multiple clicks

        self.worker = UDSWorker(self.WriteDID, self.ReadDID, wid, func, params, defaults, tick_box, inputs) # create a UDSWorker thread to run the function
        self.worker.done.connect(self.on_run_done) # connect the done signal to the on_run_done slot
        self.worker.failed.connect(self.on_run_failed) # connect the failed signal to the on_run_failed slot
        self.worker.start()

    def on_run_done(self, result):
        self.btn_run.setEnabled(True) # re-enable the Run button
        mode = self.combo_RWchoose.currentText()
        if mode == "Read" and isinstance(result, dict):
            self.show_readDid(result)
            self.append_log(f"Read complete, displayed {len(result)} fields.")
        else:
            self.append_log(f"Write complete, result: {result}")

    def on_run_failed(self, msg: str):
        self.btn_run.setEnabled(True) # re-enable the Run button
        self.append_log(f"Run failed: {msg}")
        QMessageBox.critical(self, "Run Failed", msg) # show the error message in a pop-up window

    def append_log(self, text: str):
        self.log.append(text)
        self.log.ensureCursorVisible() # When you add new text,the cursor will move to the end


if __name__ == "__main__":
    app = QApplication(sys.argv) # create the QApplication object, which is required for any PyQt application
    ui = FoxPiUI() 
    ui.show() # show the UI window
    sys.exit(app.exec_()) # start the Qt event loop and exit the application when the loop ends
