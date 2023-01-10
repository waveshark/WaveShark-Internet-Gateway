import sys
from datetime import datetime, timedelta
import time
import re
import json
import argparse

from WaveSharkSerialClient import WaveSharkSerialClient
from AESEncryption import AESEncryption
from TCPIPMessageClient import TCPIPMessageClient

INTERNET_TCPIP_MQTT_DEFAULT_HOSTNAME = "broker.mqttdashboard.com"
INTERNET_TCPIP_MQTT_DEFAULT_PORT     = 1883

VERSION = "0.0.1"
COPYRIGHT_YEAR = 2023

# Look for attached WaveShark Communicators
waveSharkSerialClient = WaveSharkSerialClient()
waveshark_ports = waveSharkSerialClient.getAttachedWaveSharkCommunicators()

# No WaveShark Communicators attached to this computer?
# TODO: Make WaveShark Communicator attachment optional
if len(waveshark_ports) == 0:
  print("ERROR: Did not find any WaveShark Communicators attached to this computer")
  sys.exit()

# Display list of WaveShark Communicators attached to this computer
print("Found the following WaveShark Communicators attached to this computer:")
for waveshark_port in waveshark_ports:
  print("[WaveShark Communicator name: {}] [Port: {}]".format(waveshark_port["deviceName"], waveshark_port["port"]))
print("")

# Parse command-line arguments
# arg_parser = argparse.ArgumentParser(usage = "%(prog)s -p|--port <WaveShark Communicator port>", description = "Send or receive messages")
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("topic", help = "Internet messaging server topic, example: mFiFocNe")
arg_parser.add_argument("key", help = "Internet message encryption key (16 characters), example: TmAAYuFzCkuPxBXu")
arg_parser.add_argument("iv", help = "Internet message encryption IV (16 characters), example: GTGbbsTfViwIoOEI")
arg_parser.add_argument("-l", "--logfile", help = "Log filename")
arg_parser.add_argument("-p", "--port", help = "WaveShark Communicator port")
arg_parser.add_argument("-H", "--tcpip_hostname", help = "Internet MQTT messaging hostname", default = INTERNET_TCPIP_MQTT_DEFAULT_HOSTNAME)
arg_parser.add_argument("-P", "--tcpip_port", help = "Internet MQTT messaging port", default = INTERNET_TCPIP_MQTT_DEFAULT_PORT)
arg_parser.add_argument("-a", "--announce", help = "WaveShark announcement interval in seconds, 0 = disable announcements", default = 600, type = int)
args = arg_parser.parse_args()

# Required arguments or optional arguments with defaults
topic                     = "my/{}".format(args.topic)
encryption_key            = args.key
encryption_iv             = args.iv
tcpip_hostname            = args.tcpip_hostname
tcpip_port                = args.tcpip_port
announce_interval_seconds = args.announce

# Optional "logfile" argument
log_file = None
if args.logfile:
  try:
    log_file = open(args.logfile, "a")
    print("Opened log file [{}]".format(args.logfile))
  except:
    sys.exit("Error opening log file [{}]".format(args.logfile))

# Optional "port" argument
waveshark_port = None
if args.port:
  waveshark_port = args.port

# More than one WaveShark Communicator attached to this computer and no port argument provided?
# TODO: Make WaveShark Communicator attachment optional
if not waveshark_port and len(waveshark_ports) > 1:
  sys.exit("More than one WaveShark Communicator is attached to this computer.  You must specify which one to connect to using the -p or --port argument.")

# More than one WaveShark Communicator attached to this computer but port argument provided does not match any valid port name?
if len(waveshark_ports) > 1:
  valid_port_provided = False
  for p in waveshark_ports:
    if p["port"].lower() == waveshark_port.lower():
      valid_port_provided = True
      break
if len(waveshark_ports) > 1 and not valid_port_provided:
  print("There is no WaveShark Communicator attached to port [{}]".format(waveshark_port))
  sys.exit()

# Only one WaveShark Communicator attached to this computer?
if len(waveshark_ports) == 1:
  waveshark_port = waveshark_ports[0]["port"]
  print("NOTE: Only one WaveShark Communicator attached to this computer, forced port to [{}]".format(waveshark_port))

# If we made it here then there is either only one WaveShark Communicator attached to this computer
# or there is more than one WaveShark Communicator attached to this computer and a valid port argument was provided
# TODO: This gets more nuance

print("\r\nWaveShark Internet Gateway v{}\r\nCopyright {} WaveShark\r\n".format(VERSION, COPYRIGHT_YEAR))

# Connect to selected WaveShark Communicator
# TODO: Make this optional
connection_info = waveSharkSerialClient.tryConnect(waveshark_port)

# Did we connect?
if connection_info:
  print("Connected to WaveShark Communicator with device name [{}] on port [{}]".format(connection_info["deviceName"], connection_info["port"]))
else:
  print("Error connecting to WaveShark Communicator on port [{}]".format(waveshark_port))
  sys.exit()

def console_log(message):
  timestamped_message = ">>> [{}] {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message)
  print(timestamped_message)
  if log_file:
    log_file.write(timestamped_message + "\r\n")
    log_file.flush()

console_log("WaveShark Internet Gateway starting")

# Initialize AES encryption
console_log("Initializing encryption")
aesEncryption = AESEncryption(encryption_key, encryption_iv)

# Connect to Internet messaging system
tcpipMessageClient = TCPIPMessageClient()
console_log("Connecting to Internet messaging system [Hostname: {}] [Port: {}]".format(tcpip_hostname, tcpip_port))
if tcpipMessageClient.connect(tcpip_hostname, tcpip_port) == True:
  console_log("Connected to Internet messaging system")
else:
  sys.exit("Failed to connect to Internet message service")

# Configure device for gateway operation
# TODO: Make this optional
console_log("Configuring WaveShark Communicator for Internet Gateway operation")
waveSharkSerialClient.writeToSerial("/SEROUT FIELDTEST", 3)

# Grab a copy of our device name
# TODO: We may not have a device name
deviceName = connection_info["deviceName"]

# For receiving Internet messages
def on_message(ciphertext):
  # Decrypt message
  plaintext = aesEncryption.decrypt_message(ciphertext)

  # Ignore my own messages
  if ("[via {}]".format(deviceName)).lower() in plaintext.lower():
    return

  # Display message
  console_log("Received via Internet: {}".format(plaintext))

  # Repeat to WaveShark Communicator
  # TODO: Make this optional
  waveSharkSerialClient.writeToSerial(plaintext)

# Subscribe to incoming Internet messages
console_log("Subscribing to incoming Internet messages [Topic: {}]".format(topic)) 
tcpipMessageClient.subscribe(topic, on_message)

# For sending periodic gatway announcements
nextAnnounce = datetime.now()

# Main loop
while True:
  # Received WaveShark Communicator message?
  # TODO: Make this check optional
  s = waveSharkSerialClient.readLineFromSerial()
  if re.match(r'^\[RSS: ', s):
    console_log("Via WaveShark: {}".format(s))
    message_from = s.split("<")[1].split(">")[0]
    message_body = s[slice(s.find(">") + 2, len(s))]
    # message_rss  = s.split("]")[0].split(" ")[1]
    # message_snr  = s.split("]")[1].split(" ")[2]

    # SEND command?
    if "{} SEND".format(deviceName).lower() in s.lower():
      console_log("Got SEND command")
      tokens = message_body.strip().split(" ")
      del tokens[0]
      for i in range(0, len(deviceName.split(" "))):
        del tokens[0]
      post = (" ".join(tokens)).strip()
      console_log("Received message to send [<{}> {}]".format(message_from, post))
      if post != "":
        # Encrypt message
        post = "[via {}] <{}> {}".format(deviceName, message_from, post)
        ciphertext = aesEncryption.encrypt_message(post)

        # Send message
        tcpipMessageClient.send_message(topic, ciphertext)

        # Tell sender that message was sent
        waveSharkSerialClient.writeToSerial("OK, {}.".format(message_from))
      else:
        waveSharkSerialClient.writeToSerial("{}, what is your message?".format(message_from))

    # Unknown command?
    elif "{} ".format(deviceName).lower() in s.lower() or message_body.lower() == deviceName.lower():
      console_log("Got UNKNOWN command")
      waveSharkSerialClient.writeToSerial("{}, I don't understand what you mean. Say {} SEND and your message to send a message to other WaveShark networks. For example, {} SEND Hello World.".format(message_from, deviceName, deviceName))

  # Time to send announcement?
  secondsUntilAnnounce = (nextAnnounce - datetime.now()).total_seconds() if announce_interval_seconds != 0 else 1
  if secondsUntilAnnounce <= 0:
    nextAnnounce = datetime.now() + timedelta(seconds = announce_interval_seconds)
    console_log("Sending announcement")
    waveSharkSerialClient.writeToSerial("Hello from the {} Internet Gateway! Say {} SEND <message> to send a message to other WaveShark networks.".format(deviceName, deviceName), 2)

  # Slow down main loop a bit
  time.sleep(0.01)