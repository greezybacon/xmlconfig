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

class XMLConfig(handler.ContentHandler, object):
    content_types = {}
    default_options = {}
    required_options = []
    forbidden_options = []
    
    namespace_separator = ":"

    def __init__(self, name=None, attrs=None, parser=None, parent=None):
        self.constants = []
        self.parser = parser
        self.parent = parent
        self.content = ""
        self.type = name
        if attrs is not None: self.parse_options(attrs)

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
            # Ignore the <config> element, and ignore other, non <constant>
            # elements
            return
        self.constants.append(self.content_types[name](name, attrs,
            parent=self, parser=self.parser))
        self.parser.setContentHandler(self.constants[-1])
        
    def endDocument(self):
        for x in self.constants:
            print "Dumping namespace " + x.namespace
            for y in x:
                print "{0}: {1}".format(y, str(x[y]))
        
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
            elif x.namespace in ("__root", namespace): 
                try:
                    return x.lookup(split[0])
                except:
                    pass
        raise KeyError("{0}: Cannot lookup reference".format(key))
        
    @classmethod
    def register_type(handler, name):
        def register(clas):
            # XXX: clas should be a subclass of Constants
            handler.content_types[name] = clas
            return clas
        return register

@XMLConfig.register_type("constants")
class Constants(XMLConfig, dict):

    content_types = {}
    default_options = {
        "namespace":    "__root"
    }
    namespace_separator = "."

    def startElement(self, name, attrs):
        # Manages the handler for this element's content
        # if there is a child, then the element belongs to it
        self.constants.append(self.content_types[name](name, 
            attrs, parent=self, parser=self.parser))
        self.parser.setContentHandler(self.constants[-1])
        
    def endElement(self, name):
        # Transistion to internal dictionary
        for x in self.constants:
            self[x.key]=x
        self.constants = self
        self.parser.setContentHandler(self.parent)
        
    def lookup(self, key):
        # XXX self.constants should be a hashtable
        splitkey = key.split(self.namespace_separator, 1)
        if splitkey[0] in self:
            if len(splitkey) == 2:
                return self[splitkey[0]].lookup(splitkey[1])
            return self[splitkey[0]]
        raise KeyError("{0}: Cannot find constant".format(key))

    @property
    def namespace(self):
        if 'namespace' in self._options:
            return self.option('namespace')
        return self.parent.namespace

@Constants.register_type("string")
class SimpleConstant(XMLConfig):
    
    content_types={}
    
    default_options = {
        "delimiter":            ",",
        "preserve-whitespace":  False,
        "type":                 "str",
        "ordered":              False,
        "src":                  None,
        "resolve-references":   True
    }

    required_options = ["key"]
    forbidden_options = ["namespace"]
    
    reference_regex = re.compile(r'%\(([^%)]+)\)')

    def __init__(self, name=None, attrs=None, parser=None, parent=None):
        self.parser = parser
        self.parent = parent
        self._content = ""
        self.type=name
        self.children =[]
        if attrs is not None: self.parse_options(attrs)

    def startElement(self, name, attrs):
        if not name in self.content_types:
            raise ValueError("{0}: Invalid content".format(name))
        self.children.append(self.content_types[name](name, 
            attrs, parent=self, parser=self.parser))
        self.parser.setContentHandler(self.children[-1])
        
    def endElement(self, name):
        self.parser.setContentHandler(self.parent)
        
    def characters(self, what):
        self._content += what

    @property
    def value(self):
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
        if not hasattr(self,"_content_settled"):
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
            # Resolve references
            if self.option("resolve-references"):
                T = self.resolve_references(T)
            #
            # Cache result
            self._content=T
            self._content_settled=True
        return self._content
        
    @property
    def namespace(self):
        return self.parent.namespace
             
    def resolve_references(self, what):
        while True:
            m=self.reference_regex.search(what)
            if m is None: break
            what = what[0:m.start()] + unicode(self.root.lookup(m.group(1),
                   self.namespace)) + what[m.end():]
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

@Constants.register_type("int")
@Constants.register_type("long")
class IntegerConstant(SimpleConstant):
    def parseValue(self):
        return int(self.content)

@Constants.register_type("boolean")    
class BooleanConstant(SimpleConstant):
    def parseValue(self):
        try:
            return bool(int(self.content))
        except:
            if self.content.lower() in ["false"]:
                return False
            else:
                return bool(self.content)
    
@Constants.register_type("dict")
class DictConstant(Constants):
    @property
    def key(self):
        return self.option('key')
            
@Constants.register_type("decimal")
@Constants.register_type("float")
class DecimalConstant(SimpleConstant):
    def parseValue(self):
        return Decimal(self.content)
    
@Constants.register_type("list")
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
        for i in xrange(len(T)):
            # Convert to declared type
            T[i] = self.type_funcs[self.option('type')](T[i])
        return T   

@SimpleConstant.register_type("choose")
class ChooseHandler(SimpleConstant):
    required_options=[]
    default_options={}
    
    import socket
    vars = {
        "hostname": socket.gethostname()
    }
    
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

@ChooseHandler.register_type("default")
class ChooseDefault(SimpleConstant):
    required_options=[]
    
@ChooseHandler.register_type("when")
class ChooseWhen(SimpleConstant):
    required_options=["test"]

def main():
	parser = make_parser()
	parser.setContentHandler(XMLConfig(parser=parser))
	parser.parse("config.xml")

if __name__ == '__main__':
	main()