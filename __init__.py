# encoding: utf-8
"""
xmlconfig for Python

Created by Jared Hancock on 2011-02-05.
Copyright (c) 2011 klopen Enterprises. All rights reserved.
"""

# Copyright (c) 2011, Jared Hancock
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

import sys, os
import re
import urllib2
from xml.sax import saxutils, handler, make_parser
from decimal import Decimal

LOCAL_NAMESPACE="__local"
    
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
        self.constants = {}
        self.parent = parent
        self.parsers = []
        self._content = ""
        self._parser = parser
        self.type = name
        if attrs is not None: self.parse_options(attrs)
        if parser is not None: self.push_parser(parser, namespace)
        if namespace is not None and "namespace" not in self._options:
            self._options["namespace"] = namespace
        self.on_update = EventHook()
        self.on_added = EventHook()
        
    def push_parser(self, parser, namespace=None):
        self.parsers.append((parser,namespace))
        
    def pop_parser(self):
        self.parsers.pop()
        
    @property
    def parser(self):
        if len(self.parsers) == 0:
            return self.parent.parser
        return self.parsers[-1][0]
        
    @property
    def parser_namespace(self):
        if len(self.parsers) == 0:
            return self.parent.parser_namespace
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
        
    def has_option(self, name):
        return name in self._options

    def startElement(self, name, attrs):
        if not name in self.content_types:
            # Only enter into <constant> elements (or other registered
            # supported content types)
            return
        # Keep namespace list simple
        new_element = self.content_types[name](name=name, attrs=attrs,
            parent=self, namespace=self.parser_namespace)
        if new_element.namespace in self.constants:
            new_element = self.constants[new_element.namespace]
        else:
            self.constants[new_element.namespace] = new_element
        self.parser.setContentHandler(new_element)
        
    def endElement(self, name):
        if name in self.content_types:
            self.pop_parser()
        
    @property
    def namespaces(self):
        return self.constants.keys()
        
    @property
    def root(self):
        if self.parent is None:
            return self
        return self.parent.root
        
    def lookup(self, key, namespace=LOCAL_NAMESPACE):
        # XXX A regex would make more sense here
        split = key.split(self.namespace_separator, 1)
        if len(split) == 2:
            # XXX override given namespace?
            namespace=split[0]
            key=split[1]
        else:
            key=split[0]
        if namespace == "env":
            # Special lookup for environment variables
            return os.environ[key]
        # XXX self.constants should be a hashtable
        return self.constants[namespace].lookup(key)

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
        self.constants[namespace].link_to(newname)
                
    @property
    def namespace(self):
        if 'namespace' in self._options:
            return self.option('namespace')
        else:
            return self.parent.namespace

class XMLConfig(XMLConfigParser):
    default_options = {
        'autoload-folder-name':     'config'
    }

    def __init__(self, name):
        self._files = {}
        self._links = {}
        # Stuff from XMLConfigParser
        self.parsers = []
        self.constants = {}
        self.parent = None
        self.name = name

    def autoload(self, base_url="file:"):
        # Look for a file with [self.name]*.xml in current folder, then 
        # current folder and up to three parent folders inside a folder
        # named config
        # XXX wildcards will only work for local filesystem (not http:)
        try:
            self.load(base_url + self.name + ".xml")
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
        load = False
        try:
            content = urllib2.urlopen(url)
        except ValueError:
            url = "file:" + url
            content = urllib2.urlopen(url)
        if url in self._files:
            # Don't load if the file is alread loaded under a difference
            # namespace
            if self._files[url]['namespace'] != namespace:
                # Already loaded this file, so just create a link to another
                # namespace
                self._links[self._files[url]['namespace']] = namespace
                load = False
            #
            # XXX Check if 'last-modified' in headers
            # Reload if the file has been modified
            elif self._files[url]['headers']['last-modified'] \
                    != content.headers.dict['last-modified']:
                load = True
        #
        # If file has never been loaded, it should be loaded (duh)
        else:
            load=True
            
        if load:
            self._files[url] = {
                'namespace':    namespace, 
                'headers':      content.headers.dict.copy()
            }
            parser = make_parser()
            self.push_parser(parser, namespace)
            parser.setContentHandler(self)
            parser.parse(content)
            self.pop_parser()
        content.close()

        for dst, src in self._links.iteritems():
            try:
                self.link_namespace(src, dst)
                # XXX Only do this once
            except:
                # The target namespace hasn't been parsed yet
                pass

    def __getitem__(self, name):
        return self.lookup(name)

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def __iter__(self):
        for namespace, constants in self.constants.iteritems():
            for key, x in constants.iteritems():
                yield x

@XMLConfig.register_child("constants")
class Constants(XMLConfigParser, dict):

    content_types = {}
    default_options = {
        "src":          None
    }
    namespace_separator = "."
    
    def __init__(self, **kwargs):
        super(Constants, self).__init__(**kwargs)
        # Forbid 'env' namespace
        if self.option("namespace") == "env":
            raise ValueError("Cannot re-declare magic namespace 'env'")
        if self.option("src") is not None:
            # Load in constants
            getConfig(self.parent.name).load(self.option("src"), self.namespace)
        
    def startElement(self, name, attrs):
        # Manages the handler for this element's content
        # if there is a child, then the element belongs to it
        new_constant = self.content_types[name](name=name, 
            attrs=attrs, parent=self, namespace=self.parser_namespace)
        if new_constant.key in self:
            new_constant = self[new_constant.key]
            new_constant.clear()
        else:
            self[new_constant.key] = new_constant
        self.parser.setContentHandler(new_constant)
        
    def endElement(self, name):
        self.parser.setContentHandler(self.parent)
        
    def lookup(self, key):
        if hasattr(self, '_link'):
            return self.parent.lookup("{0}:{1}".format(self._link, key))
        splitkey = key.split(self.namespace_separator, 1)
        if splitkey[0] in self:
            if len(splitkey) == 2:
                return self[splitkey[0]].lookup(splitkey[1])
            return self[splitkey[0]]
        raise KeyError("{0}: Cannot find constant".format(key))
            
    def link_to(self, namespace):
        """
        Used to avert circular dependencies. If a file is loaded that sources
        a second file which sources the first file, a link will be placed to
        link the declared namespace in the second file for the import of the
        first file. Since the first file has already been loaded, it should
        not be loaded a second time. If the namespace was declared different
        from the namespace declared natively in the first file, a link 
        between the two namespaces will suffice.
        
        This is confusing to describe, but it isn't a problem that will be
        rarely triggered. 
        XXX Insert an example
        """
        self._link = namespace

@Constants.register_child("string")
class SimpleConstant(XMLConfigParser):
    
    content_types={}
    content_processors=[]
    
    default_options = {
        "delimiter":            ",",        # List item delimiter
        "encoding":             None,       # Content encoding (ie. base64)
        "preserve-whitespace":  False,      # Keep all whitespace in an element
        "type":                 "str",      # Type of items in a list
        "ordered":              False,      # Maintain order of a section
        "src":                  None,       # Where content is located
        "resolve-references":   True        # Resolve %(key) references
    }

    required_options = ["key"]
    forbidden_options = ["namespace"]
    
    def __init__(self, **kwargs):
        super(SimpleConstant, self).__init__(**kwargs)
        self.children =[]

    def startElement(self, name, attrs):
        if not name in self.content_types:
            raise ValueError("{0}: Invalid content".format(name))
        self.children.append(self.content_types[name](name=name, 
            attrs=attrs, parent=self))
        self.parser.setContentHandler(self.children[-1])
        
    def endElement(self, name):
        if hasattr(self, '_prev_content') \
                and self._content != self._prev_content:
            print "{0}: Changed".format(self.key)
            self.on_update.fire()
            self.parent.on_update.fire(self.key)
        self.parser.setContentHandler(self.parent)
        
    def characters(self, what):
        self._content += what
        
    def clear(self):
        "Prep for reloading"
        self._prev_content = self._content
        self._content = ""

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
            
            for proc in self.content_processors:
                T=proc.process(self, self._content)
                if T is not None:
                    self._content=T

            #
            # Cache result
            self._content_settled=True
        return self._content
        
    @classmethod
    def register_processor(cls, processor):
        for i,x in enumerate(cls.content_processors):
            if x.order > processor.order:
                cls.content_processors.insert(i, processor())
                break
        else:
            cls.content_processors.append(processor())
        
    def __repr__(self):
        return self.__unicode__()
        
    def __unicode__(self):
        return unicode(self.value)
        
class ContentProcessor(object):
    order=10
    def process(self, constant, content):
        raise NotImplementedError()
    
# XXX support not caching the value read from the URL
@SimpleConstant.register_processor
class ContentLoader(ContentProcessor):
    order=20
    def process(self, constant, content):
        if constant.option("src") is not None:
            try:
                fp = urllib2.urlopen(constant.option("src"))
            except ValueError, ex:
                # Invalid url
                raise
            else:
                return fp.read()
            
@SimpleConstant.register_processor
class WhitespaceStripper(ContentProcessor):
    order=30
    def process(self, constant, content):
        if not constant.option("preserve-whitespace"):
            return content.strip()
            
@SimpleConstant.register_processor
class WhitespaceStripper(ContentProcessor):
    order=40
    def process(self, constant, content):
        if constant.option("encoding") is not None:
            return content.decode(constant.option("encoding"))
            
@SimpleConstant.register_processor
class ReferenceResolver(ContentProcessor):
    order=90
    reference_regex = re.compile(r'%\(([^%)]+)\)')
    
    def process(self, constant, content):
        if constant.option("resolve-references"):
            return self.resolve_references(content, constant)
            
    def resolve_references(self, what, constant):
        while True:
            m=self.reference_regex.search(what)
            if m is None: break
            # XXX This is pretty ugly
            what = what[0:m.start()] \
                + unicode(constant.root.lookup(m.group(1), 
                    constant.parent.namespace)) \
                + what[m.end():]
        return what
            
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
    
@Constants.register_child("section")
class SectionConstant(Constants):
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

@SimpleConstant.register_child("choose")
class ChooseHandler(SimpleConstant):
    required_options=[]
    default_options={}
    forbidden_options=["key"]
    
    import socket
    # XXX Either move vars all the way up to the XMLConfig class
    #     or provide some interface to get the add_var method into
    #     the XMLConfig class
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
    
# Load extensions
from .plugins import crypto

# EventHook class curtousey of Michael Foord,
# http://www.voidspace.org.uk/python/weblog/arch%5Fd7%5F2007%5F02%5F03.shtml#e616
class EventHook(object):
    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__handlers.remove(handler)
        return self

    def fire(self, *args, **keywargs):
        for handler in self.__handlers:
            handler(*args, **keywargs)