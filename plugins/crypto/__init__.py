# encoding: utf-8

# Copyright (c) 2011, Jared Hancock, klopen Enterprises
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of klopen enterprises nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL KLOPEN ENTERPRISES BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from .blowfish import Blowfish 
from xmlconfig import ContentProcessor, SimpleConstant
import hashlib, hmac, sys

# XXX I thought you only had to do stuff like this in Perl!
if sys.version_info < (3,0):
    builtin_bytes = bytes
    # Remove encoding parameters required in py3k
    def bytes(string, *args, **kwargs):
        return builtin_bytes(string)
        
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
