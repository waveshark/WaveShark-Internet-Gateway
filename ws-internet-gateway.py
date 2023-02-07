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

INTERNET_TCPIP_MQTT_DEFAULT_ENCRYPTION_KEY = "aaaaaaaaaaaaaaaa"
INTERNET_TCPIP_MQTT_DEFAULT_ENCRYPTION_IV  = "bbbbbbbbbbbbbbbb"

VERSION = "1.0.3"
COPYRIGHT_YEAR = 2023

OPERATION_MODE_NORMAL               = 1
OPERATION_MODE_INTERNET_LISTEN_ONLY = 2

# Parse command-line arguments
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("topic", help = "Internet MQTT messaging server topic, example: mFiFocNe")
arg_parser.add_argument("-k", "--key", help = "Internet MQTT message encryption key (exactly 16 characters), example: TmAAYuFzCkuPxBXu", default = INTERNET_TCPIP_MQTT_DEFAULT_ENCRYPTION_KEY)
arg_parser.add_argument("-i", "--iv", help = "Internet MQTT message encryption IV (exactly 16 characters), example: GTGbbsTfViwIoOEI", default = INTERNET_TCPIP_MQTT_DEFAULT_ENCRYPTION_IV)
arg_parser.add_argument("-l", "--logfile", help = "Log filename")
arg_parser.add_argument("-p", "--port", help = "WaveShark Communicator port")
arg_parser.add_argument("-H", "--tcpip_hostname", help = "Internet MQTT messaging hostname", default = INTERNET_TCPIP_MQTT_DEFAULT_HOSTNAME)
arg_parser.add_argument("-P", "--tcpip_port", help = "Internet MQTT messaging port", default = INTERNET_TCPIP_MQTT_DEFAULT_PORT, type = int)
arg_parser.add_argument("-a", "--announce", help = "WaveShark announcement interval in seconds, 0 = disable announcements", default = 600, type = int)
arg_parser.add_argument("-A", "--all", help = "Repeat all WaveShark messages, not just those directed at the Gateway", action = "store_true")
arg_parser.add_argument("-m", "--mode", help = "Operation mode", default = 1, type = int)
arg_parser.add_argument("-d", "--debug", help = "Enable debug output", action = "store_true")
args = arg_parser.parse_args()

# Required arguments or optional arguments with defaults
topic                     = "my/{}".format(args.topic)
encryption_key            = args.key
encryption_iv             = args.iv
tcpip_hostname            = args.tcpip_hostname
tcpip_port                = args.tcpip_port
announce_interval_seconds = args.announce
operation_mode            = args.mode

# "encryption_key" validation
if len(encryption_key) != 16:
  sys.exit("Encryption key must be exactly 16 characters")

# "encryption_iv" validation
if len(encryption_iv) != 16:
  sys.exit("Encryption IV must be exactly 16 characters")

# "operation_mode" validation
if operation_mode != OPERATION_MODE_NORMAL and operation_mode != OPERATION_MODE_INTERNET_LISTEN_ONLY:
  sys.exit("Operation mode must be {} (normal) or {} (Internet MQTT listener)".format(OPERATION_MODE_NORMAL, OPERATION_MODE_INTERNET_LISTEN_ONLY))

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

# Optional "all" argument
repeat_all = False
if args.all:
  print("Repeating all WaveShark messages, not just those directed at the Gateway")
  repeat_all = True

# Optional "debug" argument
debug_mode = False
if args.debug:
  debug_mode = True

def console_log(message, debug = False):
  timestamped_message = ">>> [{}] ".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
  if debug:
    timestamped_message += "[DEBUG] "
  timestamped_message += message
  print(timestamped_message)
  if log_file:
    log_file.write(timestamped_message + "\n")
    log_file.flush()

def debug_log(message):
  if debug_mode:
    console_log(message, True)

# Look for attached WaveShark Communicators
waveSharkSerialClient = WaveSharkSerialClient(console_log, debug_log)
waveshark_ports = waveSharkSerialClient.getAttachedWaveSharkCommunicators()

# No WaveShark Communicators attached to this computer?
if operation_mode == OPERATION_MODE_NORMAL and len(waveshark_ports) == 0:
  sys.exit("ERROR: Did not find any available WaveShark Communicators attached to this computer")

# Display list of WaveShark Communicators attached to this computer
print("Found the following available WaveShark Communicators attached to this computer:")
for ws_port in waveshark_ports:
  print("[WaveShark Communicator name: {}] [Port: {}]".format(ws_port["deviceName"], ws_port["port"]))
print("")

# More than one WaveShark Communicator attached to this computer and no port argument provided?
if operation_mode == OPERATION_MODE_NORMAL and not waveshark_port and len(waveshark_ports) > 1:
  sys.exit("More than one WaveShark Communicator is available on this computer.  You must specify which one to connect to using the -p or --port argument.")

# More than one WaveShark Communicator attached to this computer but port argument provided does not match any valid port name?
if operation_mode == OPERATION_MODE_NORMAL and len(waveshark_ports) > 1:
  valid_port_provided = False
  for p in waveshark_ports:
    if p["port"].lower() == waveshark_port.lower():
      valid_port_provided = True
      break
  if len(waveshark_ports) > 1 and not valid_port_provided:
    sys.exit("There is no WaveShark Communicator available on port [{}]".format(waveshark_port))

# Only one WaveShark Communicator attached to this computer?
if operation_mode == OPERATION_MODE_NORMAL and len(waveshark_ports) == 1:
  waveshark_port = waveshark_ports[0]["port"]
  print("NOTE: Only one WaveShark Communicator attached to this computer, forced port to [{}]".format(waveshark_port))

# If we made it here then:
# 1. There is either only one WaveShark Communicator attached to this computer OR
# 2. There is more than one WaveShark Communicator attached to this computer and a valid port argument was provided
# 3. We are operating in Internet MQTT listener mode

print("WaveShark Internet Gateway v{}\r\nCopyright {} WaveShark\r\n".format(VERSION, COPYRIGHT_YEAR))

# Connect to selected WaveShark Communicator
connection_info = None
if operation_mode == OPERATION_MODE_NORMAL:
  # Try to connect to WaveShark Communicator
  connection_info = waveSharkSerialClient.tryConnect(waveshark_port)

  # Did we connect?
  if connection_info:
    print("Connected to WaveShark Communicator with device name [{}] on port [{}]".format(connection_info["deviceName"], connection_info["port"]))
  else:
    sys.exit("Error connecting to WaveShark Communicator on port [{}]".format(waveshark_port))

console_log("WaveShark Internet Gateway starting")

# Initialize AES encryption
console_log("Initializing encryption")
aesEncryption = AESEncryption(encryption_key, encryption_iv)

# Connect to Internet messaging system
tcpipMessageClient = TCPIPMessageClient(console_log, debug_log)
console_log("Connecting to Internet MQTT messaging system [Hostname: {}] [Port: {}]".format(tcpip_hostname, tcpip_port))
if tcpipMessageClient.connect(tcpip_hostname, tcpip_port) == True:
  console_log("Connected to Internet MQTT messaging system")
else:
  sys.exit("Failed to connect to Internet MQTT message service")

# Configure device for gateway operation
if operation_mode == OPERATION_MODE_NORMAL:
  console_log("Configuring WaveShark Communicator for Internet Gateway operation")
  waveSharkSerialClient.writeToSerial("/SEROUT FIELDTEST", 3)

# Grab a copy of our device name
deviceName = None
if operation_mode == OPERATION_MODE_NORMAL:
  deviceName = connection_info["deviceName"]

# For receiving Internet messages
def on_message(ciphertext):
  # Try to decrypt message
  plaintext = None
  try:
    plaintext = aesEncryption.decrypt_message(ciphertext)
  except:
    pass

  # Well-formed message after decryption?
  if plaintext != None:
    if "[via " not in plaintext:
      plaintext = None

  # Decryption successful?
  if plaintext == None:
    console_log("Unable to decrypt message, likely cause is wrong encryption key and/or wrong encryption Initialization Vector (IV)")
    return

  # Ignore my own messages
  if ("[via {}]".format(deviceName)).lower() in plaintext.lower():
    return

  # Display message
  console_log("Received via Internet: {}".format(plaintext))

  # Repeat to WaveShark Communicator
  if operation_mode == OPERATION_MODE_NORMAL:
    waveSharkSerialClient.writeToSerial(plaintext)

# Subscribe to incoming Internet messages
console_log("Subscribing to incoming Internet messages [Topic: {}]".format(topic)) 
tcpipMessageClient.subscribe(topic, on_message)

# For sending periodic gatway announcements
nextAnnounce = datetime.now()

# Main loop
while True:
  if operation_mode == OPERATION_MODE_NORMAL:
    s = ""
    try:
      # Received WaveShark Communicator message?
      s = waveSharkSerialClient.readLineFromSerial()
      if re.match(r'^\[RSS: ', s):
        console_log("Via WaveShark: [{}]".format(s))
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

        # "Repeat all" mode?
        elif repeat_all:
          console_log("Repeating all WaveShark messages [<{}> {}]".format(message_from, message_body))

          # Encrypt message
          post = "[via {}] <{}> {}".format(deviceName, message_from, message_body)
          ciphertext = aesEncryption.encrypt_message(post)

          # Send message
          tcpipMessageClient.send_message(topic, ciphertext)

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

    except:
      console_log("Caught exception in main loop: [Context: {}]".format(s))

  # Slow down main loop a bit
  time.sleep(0.01)