from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import rsa
from base64 import b64encode, b64decode
import json
import random
import gzip

class ClientCrypto:
    """
    client-side crypto tool
    """
    def encrypt(self, data):
        """
        encrypt data

        Args:
            data: data in json format

        Returns:
            encrypted data in bytes format
        """
        if data["type"] == "req_login":
            return self.rsa_encrypt(json.dumps(data))
        elif data["type"] == "live_check":
            return json.dumps(data).encode()
        else:
            return self.aes_encrypt(json.dumps(data))
    
    def decrypt(self, data_spec, data):
        '''
        decrypt data

        Args:
            data_spec: to distinguish which encryption method is used
            data: data to be decrypted, in bytes format
        Returns:
            json
        '''
        if data_spec == "2":
            return json.loads(data.decode()) 
        else:
            data = self.aes_decrypt(data)
            data = json.loads(data)
            return data
        '''
        try:
            data = self.aes_decrypt(data)
            data = json.loads(data)
        except:
            with open("log.txt", "w") as f:
                if type(data) == bytes:
                    data = data.decode()
                f.write(data)
            raise Exception("clientModel error!")
        '''

    def new_rsa(self, pubkey):
        '''
        create rsa

        Args:
            pubkey: server's rsa public key
        '''
        self.rsa_public_key = pubkey

    def new_aes(self, mode):
        '''
        create aes

        Args:
            mode: aes encryption mode

        Returns:
            aes_key and aes_iv in string format
        '''
        self.aes_mode = mode
        self.aes_key = str(int(random.random()*1e16)).encode()
        self.aes_iv = str(int(random.random()*1e16)).encode()
        #填补至16的倍数
        if len(self.aes_key)%16 != 0 :
            self.aes_key = self.pad(self.aes_key)
        if len(self.aes_iv)%16 != 0 :
            self.aes_iv= self.pad(self.aes_iv)
        self.aes_cipher = AES.new(self.aes_key, self.aes_mode, self.aes_iv)
        return self.aes_key.decode(), self.aes_iv.decode()
    
    def pad(self, data):
        '''
        padding data till len of which reaches times of 16

        Args:
            data: bytes
        
        Returns:
            bytes
        '''
        return data + (16-(len(data)%16))*b' '
    
    def unpad(self, data):
        '''
        unpadding data

        Args:
            data: bytes
        
        Returns:
            bytes
        '''
        return data.strip()

    def rsa_encrypt(self, data):
        '''
        rsa encrypt data

        Args:
            data: string

        Returns:
            bytes
        '''

        '''
        for key in data.keys():
            if key != "type":
                data[key] = b64encode(rsa.encrypt(data[key].encode(), self.rsa_public_key)).decode()
        return json.dumps(data).encode()
        '''
        
        length = len(data.encode())

        crypto_bytes = b''
        for i in range(0, length, 117):
            bytes_seg = data.encode()[i:i + 117]
            crypto_bytes += rsa.encrypt(bytes_seg, self.rsa_public_key)

        return crypto_bytes
        
    def aes_encrypt(self, data):
        '''
        aes encrypt data

        Args:
            data: string

        Returns:
            bytes
        '''

        '''
        for key in data.keys():
            if key != "type":
                data[key] = b64encode(self.aes_cipher.encrypt(self.pad(data[key].encode()))).decode()
        return json.dumps(data).encode()
        '''
        return self.aes_cipher.encrypt(self.pad(data.encode()))
        
    def aes_decrypt(self, data):
        '''
        aes decrypt data

        Args:
            data: bytes

        Returns:
            string
        '''

        '''
        for key in data.keys():
            if key != "type":
                data[key] = self.unpad(self.aes_cipher.decrypt(b64decode(data[key]))).decode()
        return data
        '''
        return gzip.decompress(self.unpad(self.aes_cipher.decrypt(data))).decode()


class ServerCrypto:
    '''
    server-side crypto tool
    '''
    def encrypt(self, data_spec, data):
        '''
        encrypt data

        Args:
            data_spec: to decide which encrypt method to use
            data: json data to encrypt

        Returns:
            bytes
        '''
        data = json.dumps(data)
        if data_spec == "2":
            return data.encode()
        else:
            return self.aes_encrypt(data)
    
    def decrypt(self, data_spec, data):
        '''
        decrypt data

        Args:
            data_spec: which encrypt method used
            data: bytes to be decrypted
        
        Returns:
            json
        '''
        if data_spec == "0":
            return json.loads(self.rsa_decrypt(data))
        elif data_spec == "1":
            return json.loads(self.aes_decrypt(data))
        elif data_spec == "2":
            return json.loads(data.decode())

    def new_rsa(self, prikey):
        '''
        create rsa

        Args:
            prikey: server's rsa private key
        '''
        self.rsa_private_key = prikey

    def new_aes(self, mode, key, iv):
        '''
        create aes

        Args:
            mode: aes encryption mode
            key: aes key in bytes
            iv: aes initial vector in bytes
        '''
        self.aes_mode = mode
        self.aes_key = key
        self.aes_iv= iv
        self.aes_cipher = AES.new(self.aes_key, self.aes_mode, self.aes_iv)

    def pad(self, data):
        '''
        padding data till len of which reaches times of 16

        Args:
            data: bytes
        
        Returns:
            bytes
        '''
        return data + (16-(len(data)%16))*b' '
    
    def unpad(self, data):
        '''
        unpadding data

        Args:
            data: bytes
        
        Returns:
            bytes
        '''
        return data.strip()

    def rsa_decrypt(self, data):
        '''
        rsa decrypt data

        Args:
            data: bytes to be decrypted
        
        Returns:
            string
        '''

        '''
        for key in data.keys():
            if key != "type":
                data[key] = rsa.decrypt(b64decode(data[key]), self.rsa_private_key).decode()
        return data
        '''

        length = len(data)

        ret_str = ''
        for i in range(0, length, 128):
            bytes_seg = data[i:i+128]
            ret_str += rsa.decrypt(bytes_seg, self.rsa_private_key).decode()
        return ret_str
        
    def aes_encrypt(self, data):
        '''
        gzip compress data, then aes encrypt it

        Args:
            data: string data to be encrypted
        
        Returns:
            bytes
        '''

        '''
        for key in data.keys():
            if key != "type":
                data[key] = b64encode(self.aes_cipher.encrypt(self.pad(data[key].encode()))).decode()
        return json.dumps(data).encode()
        '''
        return self.aes_cipher.encrypt(self.pad(gzip.compress(data.encode())))
        
    def aes_decrypt(self, data):
        '''
        aes decrypt data

        Args:
            data: bytes to be decrypted
        
        Returns:
            string
        '''

        '''
        for key in data.keys():
            if key != "type":
                data[key] = self.unpad(self.aes_cipher.decrypt(b64decode(data[key]))).decode()
        return data
        '''
        return self.unpad(self.aes_cipher.decrypt(data)).decode()