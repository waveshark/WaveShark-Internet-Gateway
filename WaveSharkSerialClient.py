import serial
import serial.tools.list_ports

class WaveSharkSerialClient:
  def __init__(self):
    self.__ser = None

  def __readLineFromSerial(self, ser):
    return ser.readline().decode("ascii").strip()

  def readLineFromSerial(self):
    return self.__readLineFromSerial(self.__ser)

  def __writeToSerial(self, ser, str, numLinesToEat = 1):
    ser.write(bytes("{}\r".format(str), "ascii"))
    for i in range(0, numLinesToEat):
      self.__readLineFromSerial(ser)

  def writeToSerial(self, str, numLinesToEat = 1):
    self.__writeToSerial(self.__ser, str, numLinesToEat)

  def getAttachedWaveSharkCommunicators(self):
    # Scan ports for WaveShark Communicators
    waveshark_ports = []
    for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
      if "CP210" in desc:
        try:
          ser = serial.Serial(baudrate = 115200, timeout = 1.0)
          ser.rts = False
          ser.dtr = False
          ser.port = port
          ser.open()
          self.__writeToSerial(ser, "/NAME")
          line = self.__readLineFromSerial(ser)
          if "sender name is [" in line:
            waveshark_ports.append({"deviceName": line.split("[")[1].split("]")[0], "port": port})
        except:
          pass

    return waveshark_ports

  def tryConnect(self, port):
    try:
      ser = serial.Serial(baudrate = 115200, timeout = 1.0)
      ser.rts = False
      ser.dtr = False
      ser.port = port
      ser.open()
      self.__writeToSerial(ser, "/NAME")
      line = self.__readLineFromSerial(ser)
      if "sender name is [" in line:
        sernder_name = line.split("[")[1].split("]")[0]
        self.__ser = ser
        return {"deviceName": sernder_name, "port": port}
    except:
      pass

    return None
