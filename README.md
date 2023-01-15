# WaveShark Internet Gateway

A simple "Internet Gateway" for WaveShark written in Python.

Uses end-to-end encryption and an Internet MQTT message store to pass messages between two WaveShark networks.

Partially meant to inspire other WaveShark users to write their own software to perform various functions using their WaveShark devices (dead drop, safety check-in list, barter point, etc).

## Documentation

See the [WaveShark Internet Gateway User Manual](https://www.waveshark.net/pages/downloads)

## Built-in help
Use the -h or --help argument to display basic help information

## Usage (Windows, stand-alone .EXE)

* git clone https://github.com/waveshark/WaveShark-Internet-Gateway
* cd WaveShark-Internet-Gateway\Builds
* Run latest stand-alone .EXE e.g. ws-internet-gateway-v1-0-1.exe

## Usage (Windows, Python)

* git clone https://github.com/waveshark/WaveShark-Internet-Gateway
* cd ..
* python -m venv venv
* cd WaveShark-Internet-Gateway
* ..\venv\Scripts\activate.bat
* python -m pip install -r requirements.txt
* python ws-internet-gateway.py

NOTE: You may need to substitute "python3" for "python"

## Usage (Linux, Python)

* git clone https://github.com/waveshark/WaveShark-Internet-Gateway
* cd ..
* python -m venv venv
* cd WaveShark-Internet-Gateway
* source ../venv/bin/activate
* python -m pip install -r requirements.txt
* python ws-internet-gateway.py

NOTE: You may need to substitute "python3" for "python"