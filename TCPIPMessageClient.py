import paho.mqtt.client as paho

class TCPIPMessageClient:
  def __init__(self, console_log_function, debug_log_function):
    self.__client = paho.Client()
    self.__console_log = console_log_function
    self.__debug_log = debug_log_function

  def __on_message(self, client, user_data, message):
    self.__receive_count += 1
    self.__debug_log("[TCPIPMessageClient.__on_message()] Message received [receive count: {}]".format(self.__receive_count))
    self.__our_on_message_function(message.payload.decode("ascii").strip())

  def __on_connect(self, client, user_data, flags, rc):
    self.__console_log("Connected to Internet MQTT messaging server")
    self.__client.subscribe(self.__queue_name, qos = 0)

  def __on_disconnect(self, client, user_data, rc):
    self.__console_log("Disconnected from Internet MQTT messaging server, will auto-reconnect")

  def connect(self, messaging_hostname, messaging_port):
    try:
      self.__client.connect(messaging_hostname, messaging_port)
      return True
    except:
      return False

  def subscribe(self, queue_name, on_message_function):
    self.__receive_count = 0

    self.__queue_name = queue_name
    self.__client.on_message = self.__on_message
    self.__client.on_connect = self.__on_connect
    self.__client.on_disconnect = self.__on_disconnect
    self.__our_on_message_function = on_message_function
    self.__client.loop_start()

  def send_message(self, queue_name, message):
    self.__client.publish(queue_name, message, qos = 0)