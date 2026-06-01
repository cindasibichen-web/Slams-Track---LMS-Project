import base64
import json
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256



private_key = RSA.import_key(open("private.pem").read())
rsa_cipher = PKCS1_OAEP.new(private_key , hashAlgo=SHA256)

def rsa_decrypt_key(encrypted_key):
    return rsa_cipher.decrypt(base64.b64decode(encrypted_key))

def aes_decrypt(cipher, nonce, tag, aes_key):
    aes = AES.new(aes_key, AES.MODE_GCM, nonce=base64.b64decode(nonce))
    plain = aes.decrypt_and_verify(
        base64.b64decode(cipher),
        base64.b64decode(tag)
    )
    return plain.decode()

def decrypt_request_payload(request):
    """
    Extracts encrypted payload (JSON only) and returns decrypted dict.
    Image in multipart is NOT encrypted.
    """
    encrypted_key = request.data.get("encrypted_key")
    cipher = request.data.get("cipher")
    nonce = request.data.get("nonce")
    tag = request.data.get("tag")

    if not all([encrypted_key, cipher, nonce, tag]):
        return None

    try:
        aes_key = rsa_decrypt_key(encrypted_key)
        decrypted_json = aes_decrypt(cipher, nonce, tag, aes_key)
        return json.loads(decrypted_json)

    except Exception as e:
        print("Decryption Error:", str(e))
        return None
    
    
    