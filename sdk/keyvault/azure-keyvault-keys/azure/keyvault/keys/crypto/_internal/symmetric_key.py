# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
import uuid
import os
from .key import Key
from .algorithms.aes_cbc import Aes256Cbc, Aes192Cbc, Aes128Cbc
from .algorithms.aes_cbc_hmac import Aes256CbcHmacSha512, Aes192CbcHmacSha384, Aes128CbcHmacSha256
from .algorithms.aes_kw import AesKw256, AesKw192, AesKw128

key_size_128 = 128 >> 3
key_size_192 = 192 >> 3
key_size_256 = 256 >> 3
key_size_384 = 384 >> 3
key_size_512 = 512 >> 3

_default_key_size = key_size_256

_supported_key_sizes = [key_size_128, key_size_192, key_size_256, key_size_384, key_size_512]

_default_enc_alg_by_size = {
    key_size_128: Aes128Cbc.name(),
    key_size_192: Aes192Cbc.name(),
    key_size_256: Aes128CbcHmacSha256.name(),
    key_size_384: Aes192CbcHmacSha384.name(),
    key_size_512: Aes256CbcHmacSha512.name(),
}

_default_kw_alg_by_size = {
    key_size_128: AesKw128.name(),
    key_size_192: AesKw192.name(),
    key_size_256: AesKw256.name(),
    key_size_384: AesKw256.name(),
    key_size_512: AesKw256.name(),
}


class SymmetricKey(Key):
    def __init__(self, kid=None, key_bytes=None, key_size=None):
        super(SymmetricKey, self).__init__()

        self._kid = kid or str(uuid.uuid4())

        if not key_bytes:
            key_size = key_size or _default_key_size

            if key_size not in _supported_key_sizes:
                raise ValueError("The key size must be 128, 192, 256, 384 or 512 bits of data")

            key_bytes = os.urandom(key_size)

        if len(key_bytes) not in _supported_key_sizes:
            raise ValueError("The key size must be 128, 192, 256, 384 or 512 bits of data")

        self._key = key_bytes

        supported_encryption_algorithms = []
        supported_key_wrap_algorithms = []
        key_size = len(self._key)
        if key_size >= key_size_128:
            supported_encryption_algorithms.append(Aes128Cbc.name())
            supported_key_wrap_algorithms.append(AesKw128.name())
        if key_size >= key_size_192:
            supported_encryption_algorithms.append(Aes192Cbc.name())
            supported_key_wrap_algorithms.append(AesKw192.name())
        if key_size >= key_size_256:
            supported_encryption_algorithms.append(Aes256Cbc.name())
            supported_encryption_algorithms.append(Aes128CbcHmacSha256.name())
            supported_key_wrap_algorithms.append(AesKw256.name())
        if key_size >= key_size_384:
            supported_encryption_algorithms.append(Aes192CbcHmacSha384.name())
        if key_size >= key_size_512:
            supported_encryption_algorithms.append(Aes256CbcHmacSha512.name())
        self._supported_encryption_algorithms = frozenset(supported_encryption_algorithms)
        self._supported_key_wrap_algorithms = frozenset(supported_key_wrap_algorithms)

    def is_private_key(self):
        return True

    @classmethod
    def from_jwk(cls, jwk):
        return cls(kid=jwk.kid, key_bytes=jwk.k)

    @property
    def kid(self):
        return self._kid

    @property
    def default_encryption_algorithm(self):
        return _default_enc_alg_by_size[len(self._key)]

    @property
    def default_key_wrap_algorithm(self):
        return _default_kw_alg_by_size[len(self._key)]

    def encrypt(self, plain_text, iv, **kwargs):  # pylint:disable=arguments-differ
        algorithm = self._get_algorithm("encrypt", **kwargs)
        encryptor = algorithm.create_encryptor(key=self._key, iv=iv)
        return encryptor.transform(plain_text, **kwargs)

    def decrypt(self, cipher_text, iv, **kwargs):  # pylint:disable=arguments-differ
        algorithm = self._get_algorithm("decrypt", **kwargs)
        decryptor = algorithm.create_decryptor(key=self._key, iv=iv)
        return decryptor.transform(cipher_text, **kwargs)

    def wrap_key(self, key, **kwargs):
        algorithm = self._get_algorithm("wrapKey", **kwargs)
        encryptor = algorithm.create_encryptor(key=self._key)
        return encryptor.transform(key)

    def unwrap_key(self, encrypted_key, **kwargs):
        algorithm = self._get_algorithm("unwrapKey", **kwargs)
        decryptor = algorithm.create_decryptor(key=self._key)
        return decryptor.transform(encrypted_key)

    def sign(self, digest, **kwargs):
        raise NotImplementedError("Local signing isn't supported with symmetric keys")

    def verify(self, digest, signature, **kwargs):
        raise NotImplementedError("Local signature verification isn't supported with symmetric keys")
