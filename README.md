# WaveShark Internet Gateway

A simple "Internet Gateway" for WaveShark written in Python.

Uses end-to-end encryption and an Internet MQTT message store to pass messages between two WaveShark networks.

If only one WaveShark device is connected to your computer then this software will automatically choose that device.  Otherwise, it will provide a list of all WaveShark devices connected to your computer and allow you to choose one using the -p or --port argument.

Partially meant to inspire other WaveShark users to write their own software to perform various functions using their WaveShark devices (dead drop, safety check-in list, barter point, etc).

## Usage

* python3 -m venv venv
* venv\Scripts\activate.bat (on Windows)
* python3 -m pip install -r requirements.txt
* python3 ws-internet-gateway.py

## Alternative usage (python versus python3)

* python -m venv venv
* venv\Scripts\activate.bat (on Windows)
* python -m pip install -r requirements.txt
* python ws-internet-gateway.py
