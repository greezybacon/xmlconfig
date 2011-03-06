# encoding: utf-8

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
            # XXX Try and read encoding from XML document
            key = hmac.new(constant.key.encode(), 
                (constant.options['salt'] + constant.namespace).encode(), 
                hashlib.sha1).digest()
            return Blowfish(key).decrypt(content)

# Lock / Unlock support
from xml.dom.minidom import parse
import random
from base64 import standard_b64encode
from xmlconfig.cli import CliCommand

class ConstantLockUtility(CliCommand):
    __command__ = "lock"

    def run(self, *args):
        doc = parse("test/lockme.xml")
        # Look for <constant> elements
        for x, ns in self.findUnlockedElements(doc):
            print("key",x.getAttribute('key').encode())
            print("namespace",ns.encode())
            # Generate a 72-bit random salt
            salt = bytearray()
            for x in range(9):
                salt.append(random.randint(0,255))
            print("salt",standard_b64encode(bytes(salt)))
            
    def findConstantsElements(self, element):
        ret = []
        for node in element.childNodes:
            if node.nodeName == "constants":
                ret.append(node)
            elif node.hasChildNodes:
                ret.extend(self.findConstantsElements(node))
        return ret

    def findUnlockedElements(self, element):
        for ns in self.findConstantsElements(element):
            if ns.hasAttribute("namespace"):
                namespace = ns.getAttribute("namespace")
            else:
                namespace = "__local"
            for node in ns.childNodes:
                # Use Constants.content_types
                if node.nodeName in ("string"):
                    if not node.hasAttribute("key"):
                        continue
                    if node.hasAttribute("options"):
                        if "unlocked" in node.getAttribute("options"):
                            yield (node, namespace)

if __name__ == '__main__':
    ConstantLockUtility().run()
