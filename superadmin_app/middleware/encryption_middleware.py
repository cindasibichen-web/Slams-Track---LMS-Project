import json
import base64
import os
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256, SHA1



# Load the frontend PUBLIC KEY (for encrypting AES key)
public_key = RSA.import_key(open("public.pem").read())
rsa_cipher_sha256 = PKCS1_OAEP.new(public_key , hashAlgo=SHA256)
rsa_cipher_sha1 = PKCS1_OAEP.new(public_key , hashAlgo=SHA1)


def aes_encrypt(plaintext: str):
    aes_key = os.urandom(32)     
    aes = AES.new(aes_key, AES.MODE_GCM)

    cipher_bytes, tag = aes.encrypt_and_digest(plaintext.encode())

    return {
        "aes_key": aes_key,
        "cipher": base64.b64encode(cipher_bytes).decode(),
        "nonce": base64.b64encode(aes.nonce).decode(),
        "tag": base64.b64encode(tag).decode()
    }


def encrypt_response_payload(data_obj, use_sha256=True):

    json_text = json.dumps(data_obj, default=str, separators=(",", ":"))
    aes_data = aes_encrypt(json_text)

    # AES key to encrypt
    aes_key = aes_data["aes_key"]

    # React uses SHA-256 → so default to SHA-256
    if use_sha256:
        encrypted_aes_key = rsa_cipher_sha256.encrypt(aes_key)
    else:
        encrypted_aes_key = rsa_cipher_sha1.encrypt(aes_key)

    return {
        "encrypted_key": base64.b64encode(encrypted_aes_key).decode(),
        "cipher": aes_data["cipher"],
        "nonce": aes_data["nonce"],
        "tag": aes_data["tag"],
    }

class ResponseEncryptionMiddleware(MiddlewareMixin):

    def process_response(self, request, response):

        if not getattr(response, "encrypt_payload", False):
            return response

        content_type = response.get("Content-Type", "")

        if not content_type.startswith("application/json"):
            return response

        try:

            if hasattr(response, "data"):
                original_data = response.data
            else:
                original_data = json.loads(response.content.decode())

            encrypted_payload = encrypt_response_payload(original_data)

            return JsonResponse(
                encrypted_payload,
                status=response.status_code,
                safe=True
            )

        except Exception as e:
            print("Response encryption error:", e)
            return response