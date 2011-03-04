from .blowfish import Blowfish 
from xmlconfig import ContentProcessor, SimpleConstant
import hashlib, hmac

@SimpleConstant.register_processor
class EncryptedContent(ContentProcessor):
    order=80
    def process(self, constant, content):
        if constant.has_option("salt"):
            # Key is an SHA1 hmac hash of the key attribute of the loaded 
            # document, the salt of this element, and the namespace
            # XXX Implement password of this config document
            key = hmac.new(buffer(constant.key), constant.option('salt') 
                + constant.namespace, hashlib.sha1).digest()
            return Blowfish(key).decrypt(content)