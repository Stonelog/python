import base64

from Crypto.Hash import SHA
from Crypto.PublicKey import RSA as rsa
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Util.number import ceil_div
from Crypto.Util.number import size
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5

from constants import PUBLIC_KEY
from constants import PRIVATE_KEY


def encrypt(plaintext_str, version="1"):
    """Encrypt the string
    :param plaintext_str: Strings that need to be encrypted, type str
    :param version: Version number of the encryption algorithm, type str
    :return: Encrypted string, type str
    """
    encrypt_str = ""
    if "0" == version:
        encrypt_str = base64.b64encode(plaintext_str)
    elif "1" == version:
        rsa_util = RSAProcess(PUBLIC_KEY, PRIVATE_KEY)
        encrypt_str = rsa_util.rsa_long_encrypt(plaintext_str)

    # TODO Handle other encryption algorithms

    return "${}${}".format(version, encrypt_str) if encrypt_str else encrypt_str


def decrypt(encrypted_str):
    """Decrypt an encrypted string
    :param encrypted_str: Encrypted string, type str
    :return: Decrypted string, type str
    """
    if not encrypted_str:
        return ""

    version = "0"
    if len(encrypted_str.split("$", 2)) > 2:
        version = encrypted_str.split("$", 2)[1]
        encrypted_str = encrypted_str.split("$", 2)[2]
    decrypt_str = ""
    if "0" == version:
        decrypt_str = base64.b64decode(encrypted_str)
    elif "1" == version:
        rsa_util = RSAProcess(PUBLIC_KEY, PRIVATE_KEY)
        decrypt_str = rsa_util.rsa_long_decrypt(encrypted_str)

    # TODO Handle other decryption algorithms

    return decrypt_str


class RSAProcess(object):

    def __init__(self, public_key, private_key):
        self.public_key = public_key
        self.private_key = private_key

    def rsa_long_encrypt(self, plaintext_str):
        """Encrypt the string
        :param plaintext_str: Strings that need to be encrypted, type str
        :return: Encrypted string, type str
        """
        _msg = plaintext_str.encode('utf-8')
        length = len(_msg)
        # 1024/8 - 11=117, 1024 bits key
        # 2048/8 - 11=245, 2048 bits key
        mod_bits = size(rsa.importKey(self.public_key).n)
        default_length = ceil_div(mod_bits, 8) - 11
        # Public key encryption
        public_obj = PKCS1_v1_5.new(rsa.importKey(self.public_key))
        # Fragment encryption is not required
        if length < default_length:
            return base64.b64encode("".join(public_obj.encrypt(_msg)))
        # Fragment encryption
        offset = 0
        res = []
        while length - offset > 0:
            if length - offset > default_length:
                res.append(public_obj.encrypt(_msg[offset:offset + default_length]))
            else:
                res.append(public_obj.encrypt(_msg[offset:]))
            offset += default_length
        return base64.b64encode("".join(res))

    def rsa_long_decrypt(self, encrypted_str):
        """Decrypt an encrypted string
        :param encrypted_str: Encrypted string, type str
        :return: Decrypted string, type str
        """
        _msg = base64.b64decode(encrypted_str)
        length = len(_msg)
        # 1024/8=128, 1024 bits key
        # 2048/8=256, 2048 bits key
        mod_bits = size(rsa.importKey(self.private_key).n)
        default_length = ceil_div(mod_bits, 8)
        # Private key to decrypt
        private_obj = PKCS1_v1_5.new(rsa.importKey(self.private_key))
        # Fragment decryption is not required
        if length < default_length:
            return "".join(private_obj.decrypt(_msg, 'xyz'))
        # Fragment decryption
        offset = 0
        res = []
        while length - offset > 0:
            if length - offset > default_length:
                res.append(private_obj.decrypt(_msg[offset:offset + default_length], 'xyz'))
            else:
                res.append(private_obj.decrypt(_msg[offset:], 'xyz'))
            offset += default_length
        return "".join(res)

    def signature(self, message):
        """Generate the signature string with the private key
        :param message: A string that needs to be signed, type str
        :return: The signed string, type str
        """
        signer = Signature_pkcs1_v1_5.new(rsa.importKey(self.private_key))
        digest = SHA.new()
        digest.update(message)
        sign = signer.sign(digest)
        signature = base64.b64encode(sign)
        return signature

    def verify(self, message, signature):
        """A string that is verified by a public key and a signed string
        :param message: A string that needs to be verified, type str
        :param signature: The signed string, type str
        :return: boolean
        """
        try:
            decode_signature = base64.b64decode(signature)
            verifier = Signature_pkcs1_v1_5.new(rsa.importKey(self.public_key))
            digest = SHA.new()
            digest.update(message)
            is_verify = verifier.verify(digest, decode_signature)
        except Exception:
            is_verify = False
        return is_verify


if __name__ == '__main__':
    # 2048 bits key
    # http://tools.jb51.net/password/rsa_encode
    msg = "H134" * 3
    rsa_process = RSAProcess(PUBLIC_KEY, PRIVATE_KEY)
    _encrypt_str = rsa_process.rsa_long_encrypt(msg)
    plaintext = rsa_process.rsa_long_decrypt(_encrypt_str)
    print("encrypt_str: %s" % _encrypt_str)
    print("plaintext: %s" % plaintext)

    print("{} bits keys, PUBLIC_KEY ".format(size(rsa.importKey(PUBLIC_KEY).n)))
    print("{} bits keys, PRIVATE_KEY ".format(size(rsa.importKey(PRIVATE_KEY).n)))

    msg = 'test message'
    ret = rsa_process.signature(msg)
    print(ret)
    print(rsa_process.verify(msg, ret))
