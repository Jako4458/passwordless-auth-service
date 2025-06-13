import hashlib
import hmac
import uuid
import secrets

def create_new_device_hmac():
    device_key, hmac_secret = secrets.token_hex(16), secrets.token_hex(16)
    hmac_signature = hmac.new(bytes.fromhex(hmac_secret), device_key.encode(), hashlib.sha256).hexdigest()
    return device_key, hmac_secret, hmac_signature

def check_device_hmac(device_key,hmac_secret, hmac_to_check):
    hmac_signature = hmac.new(bytes.fromhex(hmac_secret), device_key.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(hmac_signature, hmac_to_check)


def sha512_string(string, use_salt=True):
    salt = secrets.token_hex(16)

    if use_salt:
        return salt, hashlib.sha512(string.encode() + salt.encode()).hexdigest()
    else:
        return hashlib.sha512(string.encode()).hexdigest()

def check_hash(string, salt, hash_to_check):
    generated_hash = hashlib.sha512(string.encode() + salt.encode()).hexdigest()
    return generated_hash == hash_to_check
