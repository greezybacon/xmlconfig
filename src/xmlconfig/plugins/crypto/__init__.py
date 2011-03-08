# encoding: utf-8

# XXX Prefer pycrypto if available
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

# Lock / Unlock cli support
from xml.dom.minidom import parse, Text
import random, re
from base64 import standard_b64encode
from xmlconfig.cli import CliCommand
from xmlconfig import Options
import os.path

# XXX Upgrade this to argparse when we drop Python 2.6 support
from optparse import make_option

@CliCommand.register
class ConstantLockUtility(CliCommand):
    __command__ = "lock"
    __help__ = "Lock encrypted elements in a config file"
    __args__ = [
        make_option("-f","--file",metavar="FILE",dest="filename",
            action="store",help="File to be locked",default=""),
        make_option("-i","--in-place",dest="output",
            action="store_false",default=True,
            help="Overwrite input file with locked XML config rather than " \
                 "writing file to standard out")
    ]

    def run(self, options, *args):
        if not os.path.exists(options.filename):
            raise ValueError("{0}: Config file does not exist".format(args[0]))
        doc = parse(options.filename)
        # Look for <constant> elements
        for x, ns in self.findUnlockedElements(doc):
            key= x.getAttribute('key').encode()
            namespace= ns.encode()
            # Generate a 72-bit random salt
            salt = bytearray()
            for z in range(9):
                salt.append(random.randint(0,255))
            salt= bytes(salt)

            # Form the encryption key
            ekey = hmac.new(key, salt + namespace,
                hashlib.sha1).digest()

            # Get the element content
            content= ""
            for y in x.childNodes:
                if isinstance(y, Text):
                    # Perform the encryption
                    # Preserve leading and trailing whitespace
                    leading = re.search(r'^\s*', y.data).group(0)
                    trailing = re.search(r'\s*$', y.data).group(0)
                    y.data= leading + standard_b64encode(
                        # XXX This looks disgusting
                        Blowfish(ekey).encrypt(y.data.strip().encode())).decode() \
                        + trailing

            opt= Options({"options":x.getAttribute("options")})

            # Drop unlocked option
            del opt["unlocked"]
            
            # Add in new encryption options
            opt['salt'] = standard_b64encode(salt).decode()
            opt['locked'] = True

            # Add in encryption options to the element 'options' attribute
            x.setAttribute("options", opt.options_string)

        print(doc.toxml())
            
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
