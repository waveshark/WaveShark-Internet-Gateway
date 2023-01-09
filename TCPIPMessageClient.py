import paho.mqtt.client as paho

class TCPIPMessageClient:
  def __init__(self):
    self.__client = paho.Client()

  def __on_message(self, client, user_data, message):
    self.__receive_count += 1
    self.__our_on_message_function(message.payload.decode("ascii").strip())

  def connect(self, messaging_hostname, messaging_port):
    try:
      self.__client.connect(messaging_hostname, messaging_port)
      return True
    except:
      return False

  def subscribe(self, queue_name, on_message_function):
    self.__receive_count = 0

    self.__client.on_message = self.__on_message
    self.__our_on_message_function = on_message_function
    self.__client.subscribe(queue_name, qos = 0)
    self.__client.loop_start()

  def send_message(self, queue_name, message):
    self.__client.publish(queue_name, message, qos = 0)