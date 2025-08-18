# Foxtronpi-pyclient

This is an example python project to control the FoxtronEV's car model FoxtronPi(D31x) under project FoxtronPI with python-doipclient and python-udsoncan.

## 📁 Project Contents

| File Name | Description |
|----------------|------------------------------|
| `FoxPi_read.py`  | Read vehicle signal status(e.g. vehicle speed, lights, battary, motor, etc.) |
| `FoxPi_write.py` | Control vehicle signals（e.g. acceleration, target speed, lights, gear shifting）    |
| `README.md`     | Project documentation                  |
| `pyproject.toml` | Package requirements |

---

## <img src="https://img.icons8.com/color/48/windows-10.png" width="24"/> <img src="https://img.icons8.com/color/48/linux.png" width="24"/> Recommendation — Insatll WSL before development 
When working in a Windows environment, we recommend installing WSL first, as it will make subsequent Python development more convenient.

### 1. Install WSL+ubuntu-22.04
Open the windows CMD and type in the command
```bash
wsl --install -d Ubuntu-22.04
```
The system will automatically download and install some Linux kernel components.

Next, you’ll see an installation progress bar.

Once it finishes, a prompt will appear asking you to enter a username and password.

Note: When entering your password, nothing will appear in the terminal as you type — this is normal behavior.
So, don’t worry if it looks like nothing is being entered, and avoid pressing keys repeatedly!

`Once the username and password are entered, the setup is complete.`

### 2. Update Ubuntu
```bash
sudo apt update
sudo apt upgrade
```

### 3. How to launch WSL after exiting the installer or restarting your computer
Open the CMD and type in the `wsl` command.
```bash
wsl
```

## <img src="https://img.icons8.com/color/30/python.png" width="28"/> Create the Python Virtual Environment 
### Why do we need to create a Python Virtual Environment? 
A Python Virtual Environment helps isolate dependencies and prevents the global development environment from becoming messy when working on multiple projects.

1. Install Python3 and Venv(If not already installed)
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

##  <img src="https://img.icons8.com/fluency/28/maintenance.png" width="24"/> Installation and setup the system requirements packages
### 1. Clone the repository
First,Open the CMD and type in the `wsl`.

Then, enter the following command after WSL starts:
```bash
git clone --branch my-feature-branch https://github.com/XIAO-JUN-ZE/foxtronpi-pyclient.git
```

### 2. Enter the project folder
```bash
cd foxtronpi-pyclient
```

### 3. Create a virtual environment folder called Pi(You may choose a different name)
```bash
python3 -m venv Pi
```

### 4. Activate the virtual environment
```bash
source Pi/bin/activate
```

### 5. Install the package requirements
```bash
pip install .
```

## <img src="https://img.icons8.com/fluency/28/console.png" width="22"/> Execution Method 

### Read the status of vehicle signals
```bash
python3 FoxPi_read.py
```

### Write the vehicle Control signals
```bash
python3 FoxPi_write.py
```

## <img src="https://img.icons8.com/fluent/24/visual-studio-code-2019.png" width="24"/> Visual Studio Code development environment 
Open VS code to develop Python code if you want, but make sure you are inside the `foxtronpi-pyclient` folder.
```bash
code .
```
