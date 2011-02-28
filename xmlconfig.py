#!/usr/bin/env python
# encoding: utf-8
"""
xmlconfig.py

Created by Jared Hancock on 2011-02-05.
Copyright (c) 2011 __MyCompanyName__. All rights reserved.
"""

import sys
import re
import urllib2
from xml.sax import saxutils, handler, make_parser
from decimal import Decimal

# TODO:
# Support wish-list
# - Using a name for a config doc (ie. getConfig(name))
# x list/dict support
# x choose block support
# x namespaces
# x references, nested references
# x binary content
# x ecrypted content
# - locking/unlocking documents with <cryptic> elements
# - schema & validation script
# - support password (key) for encrypted stuff
# x imports (circular reference auto-correct)
# x import changing local namespace or foreign document
# ? references to non-imported namespaces
# - auto loading
# - auto updating (when file is modified)
# - event notification of updates
# - retrieve elements from config file with fall-back default value
# - installer (distutils)
# - installer creates unique host-key for en-/decryption
# - write support (perhaps to be used with (un)locking)

LOCAL_NAMESPACE="__local"

class XMLConfig(object):
    
    def __init__(self, name):
        self._config_parser = XMLConfigParser()
        self._files = {}
        self._links = {}
        self.name = name
        
    def autoload(self, base_url="file:"):
        # Look for a file with [self.name]*.xml in current folder, then 
        # current folder and up to three parent folders inside a folder
        # named config
        # XXX wildcards will only work for local filesystem (not http:)
        try:
            self.load(base_url + self.name + ".xml", namespace=self.name)
        except:
            raise
        
    @property
    def is_loaded(self):
        """
        Returns True if the configuration document has been found, loaded,
        and successfully processed
        """
        pass
    
    def load(self, url, namespace=LOCAL_NAMESPACE):
        # Keep track of loaded files to ward off circular dependencies
        try:
            content = urllib2.urlopen(url)
        except ValueError:
            url = "file:" + url
            content = urllib2.urlopen(url)
        if url in self._files:
            # Already loaded this file, so just create a link to another
            # namespace
            self._links[self._files[url]] = namespace
        else:
            self._files[url] = namespace
            parser = make_parser()
            self._config_parser.push_parser(parser, namespace)
            parser.setContentHandler(self._config_parser)
            parser.parse(content)
        content.close()
            
        for dst, src in self._links.iteritems():
            try:
                self._config_parser.link_namespace(src, dst)
                # XXX Only do this once
            except:
                # The target namespace hasn't been parsed yet
                pass
        
    def __getitem__(self, name):
        return self._config_parser.lookup(name)
        
    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default
            
    def __iter__(self):
        for x in self._config_parser.constants:
            for y in x:
                yield x[y]
    
__configs={}
def getConfig(name=""):
    if name not in __configs:
        __configs[name] = XMLConfig(name)
    return __configs[name]

class XMLConfigParser(handler.ContentHandler, object):
    content_types = {}
    default_options = {}
    required_options = []
    forbidden_options = []
    
    namespace_separator = ":"

    def __init__(self, name=None, attrs=None, parser=None, parent=None, 
            namespace=None):
        self.constants = []
        self.parent = parent
        self.parsers = []
        self._content = ""
        self.type = name
        if attrs is not None: self.parse_options(attrs)
        if parser is not None: self.push_parser(parser, namespace)
        if namespace is not None and "namespace" not in self._options:
            self._options["namespace"] = namespace
        
    def push_parser(self, parser, namespace=None):
        self.parsers.append((parser,namespace))
        
    def pop_parser(self):
        self.parsers.pop()
        
    @property
    def parser(self):
        return self.parsers[-1][0]
        
    @property
    def parser_namespace(self):
        return self.parsers[-1][1]

    def parse_options(self, attrs):
        self._options = self.default_options.copy()
        for name in attrs.getNames():
            self._options[name] = attrs[name]

        # XXX: Required options
        for name in self.required_options:
            if name not in self._options:
                raise ValueError("{0}: {1} required".format(self.type, name))
                
        # XXX: Forbidden options
        for name in self.forbidden_options:
            if name in self._options:
                raise ValueError("{0}: '{1}' option is forbidden".format(
                    self.type, name))
                
    # XXX: Should be a verb
    def option(self, name):
        return self._options[name]

    def startElement(self, name, attrs):
        if not name in self.content_types:
            # Only enter into <constant> elements (or other registered
            # supported content types)
            return
        self.constants.append(self.content_types[name](name=name, attrs=attrs,
            parent=self, parser=self.parser, namespace=self.parser_namespace))
        self.parser.setContentHandler(self.constants[-1])
        
    def endElement(self, name):
        self.pop_parser()
        
    @property
    def namespaces(self):
        return [x.namespace for x in self.constants]
        
    @property
    def root(self):
        if self.parent is None:
            return self
        return self.parent.root
        
    def lookup(self, key, namespace=""):
        # XXX self.constants should be a hashtable
        split = key.split(self.namespace_separator, 1)
        for x in self.constants:
            if len(split) == 2 and len(split[1]):
                if x.namespace == split[0]:
                    return x.lookup(split[1])
            elif x.namespace in (LOCAL_NAMESPACE, namespace): 
                try:
                    return x.lookup(split[0])
                except:
                    pass
        raise KeyError("{0}: Cannot lookup reference".format(key))
                
    @classmethod
    def register_child(handler, name):
        def register(clas):
            # XXX: clas should be a subclass of Constants
            handler.content_types[name] = clas
            return clas
        return register
        
    # The parser doesn't have a namespace. If an element looks to this
    # as the parent looking for a namespace, then one must not have been
    # defined for the child, so return the default namespace
    namespace = LOCAL_NAMESPACE
        
    def link_namespace(self, namespace, newname):
        for x in self.constants:
            if x.namespace == namespace:
                x.link_to(newname)
                
    @property
    def namespace(self):
        if 'namespace' in self._options:
            return self.option('namespace')
        else:
            return self.parent.namespace

@XMLConfigParser.register_child("constants")
class Constants(XMLConfigParser, dict):

    content_types = {}
    default_options = {
        "src":          None
    }
    namespace_separator = "."
    
    def __init__(self, **kwargs):
        super(Constants, self).__init__(**kwargs)
        if self.option("src") is not None:
            # Load in constants
            getConfig().load(self.option("src"), self.namespace)

    def startElement(self, name, attrs):
        # Manages the handler for this element's content
        # if there is a child, then the element belongs to it
        self.constants.append(self.content_types[name](name=name, 
            attrs=attrs, parent=self, parser=self.parser,
            namespace=self.parser_namespace))
        self.parser.setContentHandler(self.constants[-1])
        
    def endElement(self, name):
        # Transistion to internal dictionary
        for x in self.constants:
            self[x.key]=x
        self.constants = self
        self.parser.setContentHandler(self.parent)
        
    def lookup(self, key):
        if hasattr(self, '_link'):
            return self.parent.lookup("{0}:{1}".format(self._link, key))
        splitkey = key.split(self.namespace_separator, 1)
        if splitkey[0] in self:
            if len(splitkey) == 2:
                return self[splitkey[0]].lookup(splitkey[1])
            return self[splitkey[0]]
        raise KeyError("{0}: Cannot find constant, {1}".format(key,[x for x in self]))
            
    def link_to(self, namespace):
        self._link = namespace

@Constants.register_child("string")
class SimpleConstant(XMLConfigParser):
    
    content_types={}
    
    default_options = {
        "delimiter":            ",",
        "encoding":             None,
        "preserve-whitespace":  False,
        "type":                 "str",
        "ordered":              False,
        "src":                  None,
        "resolve-references":   True
    }

    required_options = ["key"]
    forbidden_options = ["namespace"]
    
    reference_regex = re.compile(r'%\(([^%)]+)\)')

    def __init__(self, **kwargs):
        super(SimpleConstant, self).__init__(**kwargs)
        self.children =[]

    def startElement(self, name, attrs):
        if not name in self.content_types:
            raise ValueError("{0}: Invalid content".format(name))
        self.children.append(self.content_types[name](name=name, 
            attrs=attrs, parent=self, parser=self.parser))
        self.parser.setContentHandler(self.children[-1])
        
    def endElement(self, name):
        self.parser.setContentHandler(self.parent)
        
    def characters(self, what):
        self._content += what

    @property
    def value(self):
        # XXX For some more security, it might be nice to provide an
        #     option to not store the value in memory
        if not hasattr(self, '_value'):
            self._value = self.parseValue()

        return self._value
        
    @property
    def key(self):
        return self.option('key')

    def parseValue(self):
        # noop for str
        return self.content
        
    @property
    def content(self):
        if not hasattr(self,"_content_settled") or not self._content_settled:
            if len(self.children) > 0:
                # XXX: How to handle multiple children ?
                return self.children[0].content
            #
            # Load basic content
            if self.option("src") is not None:
                T=self.import_content(self.option("src"))
            else:
                T=self._content
            # 
            # Strip whitespace
            if not self.option("preserve-whitespace"):
                T=T.strip()
            #
            # Decode
            # XXX Allow for custom decoding to consider wheter or not data
            # XXX should be encoded
            if self.option("encoding") is not None:
                T=self.decode(T, self.option("encoding"))
            #
            # Resolve references
            if self.option("resolve-references"):
                T = self.resolve_references(T)
            #
            # Cache result
            self._content=T
            self._content_settled=True
        return self._content
        
    def decode(self, what, how):
        "Allow for custom decoding (decryption)"
        # Simple for most types
        return what.decode(how)
             
    def resolve_references(self, what):
        while True:
            m=self.reference_regex.search(what)
            if m is None: break
            what = what[0:m.start()] + unicode(self.root.lookup(m.group(1),
                   self.parent.namespace)) + what[m.end():]
        return what
        
    def import_content(self, url):
        try:
            fp = urllib2.urlopen(url)
        except ValueError, ex:
            # Invalid url
            raise
        else:
            return fp.read()
        
    def __repr__(self):
        return self.__unicode__()
        
    def __unicode__(self):
        return unicode(self.value)

@Constants.register_child("int")
@Constants.register_child("long")
class IntegerConstant(SimpleConstant):
    def parseValue(self):
        return int(self.content)
        
@Constants.register_child("binary")
class BinaryConstant(SimpleConstant):
    def parseValue(self):
        return buffer(self.content)

@Constants.register_child("boolean")    
class BooleanConstant(SimpleConstant):
    def parseValue(self):
        try:
            # Handle numeric content
            return bool(int(self.content))
        except:
            # Handle 'true'/'false' content
            if self.content.lower() in ["false"]:
                return False
            # Handle character content
            else:
                return bool(self.content)
    
@Constants.register_child("dict")
class DictConstant(Constants):
    @property
    def key(self):
        return self.option("key")
            
@Constants.register_child("decimal")
@Constants.register_child("float")
class DecimalConstant(SimpleConstant):
    def parseValue(self):
        return Decimal(self.content)
    
@Constants.register_child("list")
class ListConstant(SimpleConstant):
    required_options=["delimiter","type"]
    type_funcs = {
        "str": str,
        "int": int,
        "long": long,
        "float": Decimal,
        "boolean": bool
    }
    def parseValue(self):
        T = list(self.content.split(
            self.option("delimiter")))
        for i, x in enumerate(T):
            # Convert to declared type
            if not self.option("preserve-whitespace"):
                x=x.strip()
            T[i] = self.type_funcs[self.option('type')](x)
        return T 
   
from blowfish import Blowfish 
import hashlib, hmac
@Constants.register_child("cryptic")
class EncryptedConstant(SimpleConstant):
    default_options = SimpleConstant.default_options.copy()
    default_options.update({
        'salt':         'KGS!@#$%'
    })
    def decode(self, what, how):
        # Key is an SHA1 hmac hash of the key attribute of the loaded 
        # document, the salt of this element, and the namespace
        # XXX Implement password of this config document
        key = hmac.new(buffer(self.key), self.option('salt') + self.namespace,
            hashlib.sha1).digest()
        return Blowfish(key).decrypt(what.decode(how))

@SimpleConstant.register_child("choose")
class ChooseHandler(SimpleConstant):
    required_options=[]
    default_options={}
    forbidden_options=["key"]
    
    import socket
    vars = {
        "hostname": socket.gethostname()
    }
    
    # XXX Enforce required child 'default'
    
    @property
    def content(self):
        # Run when blocks
        for x in self.children:
            if isinstance(x, ChooseDefault):
                self._default = x
            elif isinstance(x, ChooseWhen):
                # Eval the test element (safely)
                try:
                    if eval(self.resolve_references(x.option("test")), 
                            {}, self.vars):
                        self.selected = x
                        break
                except:
                    continue
        else:
            # None of the when elements matched. Use the default
            self.selected = self._default
        return self.selected.content

@ChooseHandler.register_child("default")
class ChooseDefault(SimpleConstant):
    required_options=[]
    forbidden_options=["key"]
    
@ChooseHandler.register_child("when")
class ChooseWhen(SimpleConstant):
    required_options=["test"]
    forbidden_options=["key"]

if __name__ == '__main__':
	c=getConfig()
	c.load("file:config.xml")
	for n in c:
	    print n.namespace, ":", n.key, ":", n