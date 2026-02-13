import os
from cryptography.fernet import Fernet
from project.settings import CRYPTO_SECRET_KEY

key = CRYPTO_SECRET_KEY.encode() 
cipher_suite = Fernet(key)

def encrypt_data(data):
    if isinstance(data, str):
        data = data.encode()
    encrypted_data = cipher_suite.encrypt(data)
    return encrypted_data

def decrypt_data(encrypted_data):
    decrypted_data = cipher_suite.decrypt(encrypted_data)
    return decrypted_data.decode()