import serial
import serial.tools.list_ports
import time

class WaveSharkSerialClient:
  def __init__(self, console_log_function, debug_log_function):
    self.__ser = None
    self.__console_log = console_log_function
    self.__debug_log = debug_log_function

  def __readLineFromSerial(self, ser):
    try:
      lineRead = ser.readline().decode("ascii").strip()
      if lineRead != "":
        self.__debug_log("[WaveSharkSerialClient.__readLineFromSerial()] Read line [{}]".format(lineRead))
      return lineRead
    except:
      self.__debug_log("[WaveSharkSerialClient.__readLineFromSerial()] Did not get a line from the serial port")
      return ""

  def readLineFromSerial(self):
    return self.__readLineFromSerial(self.__ser)

  def __writeToSerial(self, ser, str, numLinesToEat = 1):
    self.__debug_log("[WaveSharkSerialClient.__writeToSerial()] Writing to serial [{}]".format(str))
    ser.write(bytes("{}\r".format(str), "ascii"))
    for i in range(0, numLinesToEat):
      self.__debug_log("[WaveSharkSerialClient.__writeToSerial()] Eating line")
      self.__readLineFromSerial(ser)

  def writeToSerial(self, str, numLinesToEat = 1):
    self.__writeToSerial(self.__ser, str, numLinesToEat)

  # TODO: This method is a mess -- simplify code, combine logic with tryConnect()
  def getAttachedWaveSharkCommunicators(self):
    # Scan ports for WaveShark Communicators
    waveshark_ports = []
    for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
      self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Found device [port: {}] [desc: {}] [hwid: {}]".format(port, desc, hwid))
      if "CP210" in desc:
        self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] This is a CP210x device [port: {}]".format(port))
        try:
          self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Trying to connect to CP210x device [port: {}]".format(port))
          ser = serial.Serial(baudrate = 115200, timeout = 0.01)
          ser.rts = False
          ser.dtr = False
          ser.port = port
          self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Trying to open serial port [port: {}]".format(port))
          ser.open()
          self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Opened serial port [port: {}]".format(port))
          self.__writeToSerial(ser, "/NAME")
          for i in range(0, 100):
            self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Checking for READY prompt [port: {}]".format(port))
            line = self.__readLineFromSerial(ser)
            if "READY." in line:
              self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Got READY prompt [port: {}]".format(port))
              break
            if "sender name is" in line:
              self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Got device name instead of READY prompt (this is okay) [port: {}]".format(port))
              break
            line = self.__readLineFromSerial(ser)
            if "READY." in line:
              self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Got READY prompt [port: {}]".format(port))
              break
            if "sender name is" in line:
              self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Got device name instead of READY prompt (this is okay) [port: {}]".format(port))
              break
          for i in range(0, 20):
            self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Looking for device name [port: {}]".format(port))
            self.__writeToSerial(ser, "/NAME")
            line = self.__readLineFromSerial(ser)
            self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Got candidate device name line [line: {}] [port: {}]".format(line, port))
            if "sender name is [" in line:
              deviceName = line.split("[")[1].split("]")[0]
              waveshark_ports.append({"deviceName": deviceName, "port": port})
              self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Got device name [deviceName: {}] [port: {}]".format(deviceName, port))
              break
            line = self.__readLineFromSerial(ser)
            self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Got candidate device name line [line: {}] [port: {}]".format(line, port))
            if "sender name is [" in line:
              deviceName = line.split("[")[1].split("]")[0]
              waveshark_ports.append({"deviceName": deviceName, "port": port})
              self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Got device name [deviceName: {}] [port: {}]".format(deviceName, port))
              break
        except:
          self.__debug_log("[WaveSharkSerialClient.getAttachedWaveSharkCommunicators()] Entered exception handler while trying to connect (this might be okay) [port: {}]".format(port))
          pass

    return waveshark_ports

  # TODO: This method is a mess -- simplify code, combine logic with getAttachedWaveSharkCommunicators()
  def tryConnect(self, port):
    try:
      self.__debug_log("[WaveSharkSerialClient.tryConnect()] Trying to connect to WaveShark Communicator [port: {}]".format(port))
      ser = serial.Serial(baudrate = 115200, timeout = 0.01)
      ser.rts = False
      ser.dtr = False
      ser.port = port
      ser.open()
      self.__writeToSerial(ser, "/NAME")
      for i in range(0, 100):
        self.__debug_log("[WaveSharkSerialClient.tryConnect()] Checking for READY prompt [port: {}]".format(port))
        line = self.__readLineFromSerial(ser)
        if "READY." in line:
          self.__debug_log("[WaveSharkSerialClient.tryConnect()] Got READY prompt [port: {}]".format(port))
          break
        if "sender name is" in line:
          self.__debug_log("[WaveSharkSerialClient.tryConnect()] Got device name instead of READY prompt (this is okay) [port: {}]".format(port))
          break
        line = self.__readLineFromSerial(ser)
        if "READY." in line:
          self.__debug_log("[WaveSharkSerialClient.tryConnect()] Got READY prompt [port: {}]".format(port))
          break
        if "sender name is" in line:
          self.__debug_log("[WaveSharkSerialClient.tryConnect()] Got device name instead of READY prompt (this is okay) [port: {}]".format(port))
          break
      for i in range(0, 20):
        self.__debug_log("[WaveSharkSerialClient.tryConnect()] Looking for device name [port: {}]".format(port))
        self.__writeToSerial(ser, "/NAME")
        line = self.__readLineFromSerial(ser)
        self.__debug_log("[WaveSharkSerialClient.tryConnect()] Got candidate device name line [line: {}] [port: {}]".format(line, port))
        if "sender name is [" in line:
          deviceName = line.split("[")[1].split("]")[0]
          self.__ser = ser
          self.__debug_log("[WaveSharkSerialClient.tryConnect()] Got device name [deviceName: {}] [port: {}]".format(deviceName, port))
          return {"deviceName": deviceName, "port": port}
        line = self.__readLineFromSerial(ser)
        self.__debug_log("[WaveSharkSerialClient.tryConnect()] Got candidate device name line [line: {}] [port: {}]".format(line, port))
        if "sender name is [" in line:
          deviceName = line.split("[")[1].split("]")[0]
          self.__ser = ser
          self.__debug_log("[WaveSharkSerialClient.tryConnect()] Got device name [deviceName: {}] [port: {}]".format(deviceName, port))
          return {"deviceName": deviceName, "port": port}

    except:
      self.__debug_log("[WaveSharkSerialClient.tryConnect()] Entered exception handler while trying to connect (this might be okay) [port: {}]".format(port))
      pass

    self.__debug_log("[WaveSharkSerialClient.tryConnect()] Unable to connect [port: {}]".format(port))
    return None