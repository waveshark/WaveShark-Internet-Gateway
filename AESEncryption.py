from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from base64 import b64encode, b64decode

class AESEncryption:
  def __init__(self, encryption_key, encryption_iv):
    self.__encryption_key = bytes(encryption_key, "utf-8")
    self.__encryption_iv = bytes(encryption_iv, "utf-8")

  def encrypt_message(self, message_regular_string):
    cipher = AES.new(self.__encryption_key, AES.MODE_CBC, self.__encryption_iv)
    ciphertext = cipher.encrypt(pad(bytes(message_regular_string, "utf-8"), AES.block_size))
    ciphertext_b64 = b64encode(ciphertext).decode("utf-8")

    return ciphertext_b64

  def decrypt_message(self, ciphertext_b64_string):
    cipher = AES.new(self.__encryption_key, AES.MODE_CBC, self.__encryption_iv)
    ciphertext_bytes = b64decode(ciphertext_b64_string)
    plaintext_bytes_padded = cipher.decrypt(ciphertext_bytes)
    plaintext_bytes = unpad(plaintext_bytes_padded, AES.block_size)
    plaintext = plaintext_bytes.decode("utf-8")

    return plaintext