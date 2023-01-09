import sys
from datetime import datetime, timedelta
import time
import re
import json
import argparse

from WaveSharkSerialClient import WaveSharkSerialClient
from AESEncryption import AESEncryption
from TCPIPMessageClient import TCPIPMessageClient

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
arg_parser.add_argument("topic", help = "Internet TCP/IP messaging server topic, example: mFiFocNe")
arg_parser.add_argument("key", help = "Internet TCP/IP message encryption key (16 characters), example: TmAAYuFzCkuPxBXu")
arg_parser.add_argument("iv", help = "Internet TCP/IP message encryption IV (16 characters), example: GTGbbsTfViwIoOEI")
arg_parser.add_argument("-l", "--logfile", help = "Log filename")
arg_parser.add_argument("-p", "--port", help = "WaveShark Communicator port")
arg_parser.add_argument("-a", "--announce", help = "WaveShark announcement interval in seconds, 0 = disable announcements", default = 600, type = int)
args = arg_parser.parse_args()

# Required arguments or optional arguments with defaults
topic                     = "my/{}".format(args.topic)
encryption_key            = args.key
encryption_iv             = args.iv
announce_interval_seconds = args.announce

# Optional "port" argument
port = None
if args.port:
  port = args.port

# More than one WaveShark Communicator attached to this computer and no port argument provided?
# TODO: Make WaveShark Communicator attachment optional
if not port and len(waveshark_ports) > 1:
  print("More than one WaveShark Communicator is attached to this computer.  You must specify which one to connect to using the -p or --port argument.")
  sys.exit()

# More than one WaveShark Communicator attached to this computer but port argument provided does not match any valid port name?
if len(waveshark_ports) > 1:
  valid_port_provided = False
  for p in waveshark_ports:
    if p["port"].lower() == port.lower():
      valid_port_provided = True
      break
if len(waveshark_ports) > 1 and not valid_port_provided:
  print("There is no WaveShark Communicator attached to port [{}]".format(port))
  sys.exit()

# Only one WaveShark Communicator attached to this computer?
if len(waveshark_ports) == 1:
  port = waveshark_ports[0]["port"]

# If we made it here then there is either only one WaveShark Communicator attached to this computer
# or there is more than one WaveShark Communicator attached to this computer and a valid port argument was provided
# TODO: This gets more nuance

print("WaveShark Internet Gateway starting\r\n")

# Connect to selected WaveShark Communicator
# TODO: Make this optional
connection_info = waveSharkSerialClient.tryConnect(port)

# Did we connect?
if connection_info:
  print("Connected to WaveShark Communicator with device name [{}] on port [{}]".format(connection_info["deviceName"], connection_info["port"]))
else:
  print("Error connecting to WaveShark Communicator on port [{}]".format(port))
  sys.exit()

# Initialize AES encryption
aesEncryption = AESEncryption(encryption_key, encryption_iv)

# Connect to TCP/IP messaging system
tcpipMessageClient = TCPIPMessageClient()
if tcpipMessageClient.connect() == True:
  print("Connected to TCP/IP message service")
else:
  sys.exit("Failed to connect to TCP/IP message service")

# Configure device for gateway operation
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
  print(">>> Received via Internet: {}".format(plaintext))

  # Repeat to WaveShark Communicator
  # TODO: Make this optional
  waveSharkSerialClient.writeToSerial(plaintext)

# Subscribe to incoming Internet messages
tcpipMessageClient.subscribe(topic, on_message)

# Configure WaveShark Communicator for operation
waveSharkSerialClient.writeToSerial("/SEROUT FIELDTEST", 3)

# For sending periodic gatway announcements
nextAnnounce = datetime.now()

# Main loop
while True:
  # Received WaveShark Communicator message?
  # TODO: Make this check optional
  s = waveSharkSerialClient.readLineFromSerial()
  if re.match(r'^\[RSS: ', s):
    print("\r\n>>> Via WaveShark: {}".format(s))
    message_from = s.split("<")[1].split(">")[0]
    message_body = s[slice(s.find(">") + 2, len(s))]
    # message_rss  = s.split("]")[0].split(" ")[1]
    # message_snr  = s.split("]")[1].split(" ")[2]

    # SEND command?
    if "{} SEND".format(deviceName).lower() in s.lower():
      print(">>> Got SEND command")
      tokens = message_body.strip().split(" ")
      del tokens[0]
      for i in range(0, len(deviceName.split(" "))):
        del tokens[0]
      post = (" ".join(tokens)).strip()
      print(">>> Received message to send [" + post + "]")
      if post != "":
        # Encrypt message
        post = "[via {}] <{}> {}".format(deviceName, message_from, post)
        ciphertext = aesEncryption.encrypt_message(post)

        # Send message
        tcpipMessageClient.send_message(topic, ciphertext)

        # Tell sender that message was sent
        waveSharkSerialClient.writeToSerial("{}, your message has been sent.".format(message_from))
      else:
        waveSharkSerialClient.writeToSerial("{}, what is your message?".format(message_from))

    # Unknown command?
    elif "{} ".format(deviceName).lower() in s.lower():
      print(">>> Got UNKNOWN command")
      waveSharkSerialClient.writeToSerial("{}, I don't understand what you mean. Say {} SEND and your message to send a message to my area. For example, {} SEND Hello World.".format(message_from, deviceName, deviceName))

  # Time to send announcement?
  secondsUntilAnnounce = (nextAnnounce - datetime.now()).total_seconds() if announce_interval_seconds != 0 else 1
  if secondsUntilAnnounce <= 0:
    nextAnnounce = datetime.now() + timedelta(seconds = announce_interval_seconds)
    print(">>> Sending announcement")
    waveSharkSerialClient.writeToSerial("Hello from the {} Internet Gateway! Say {} SEND <message> to send a message to my area.".format(deviceName, deviceName), 2)

  # Slow down main loop a bit
  time.sleep(0.01)