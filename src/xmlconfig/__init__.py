# encoding: utf-8
"""
xmlconfig for Python

Copyright (c) 2011 klopen Enterprises. All rights reserved.
"""

import os, re, sys, codecs
from xml.sax import handler, make_parser
from decimal import Decimal

LOCAL_NAMESPACE="__local"
    
__configs={}
def getConfig(name=""):
    if name not in __configs:
        __configs[name] = XmlConfig(name)
    return __configs[name]

# Rectify differences between Python 2 and Python3k
# - urllib2 / urllib.request
# Allow unit test modules to override the definition of urlopen
if 'nose' in sys.modules:
    from testImport import urlopen
if sys.version_info >= (3,0):
    if 'urlopen' not in globals():
        from urllib.request import urlopen
    from urllib.parse import urlparse, urljoin, urlunparse
else:
    if 'urlopen' not in globals():
        from urllib2 import urlopen
    from urlparse import urlparse, urljoin, urlunparse
    
class Options(dict):
    def __init__(self, defaults={}):
        self.update(defaults)
        self.process()

    def process(self):
        # Support options combined into an "options" attribute in
        # a css style
        if 'options' in self:
            for x in self['options'].split(';'):
                kv = x.strip().split(":",1)
                if len(kv) == 2:
                    self[kv[0]] = kv[1]
                else:
                    # If no colon, assume a "set" boolean option
                    self[kv[0]] = True
            del self['options']

    @property
    def options_string(self):
        ret= []
        for k,v in self.items():
            if v in (None, True):
                ret.append(k)
            else:
                ret.append("{0}:{1}".format(k,v))
        return ";".join(ret)
        
    def merge(self, attrs):
        if type(attrs) is dict:
            self.update(attrs)
        else:
            for name in attrs.getNames():
                self[name] = attrs[name]
        self.process()
                    
class XmlConfigParser(handler.ContentHandler, object):
    content_types = {}
    default_options = {}
    required_options = []
    forbidden_options = []
    
    namespace_separator = ":"

    def __init__(self, name=None, attrs=None, parser=None, parent=None, 
            namespace=None):
        self.parent = parent
        self._content = ""
        self._options = Options(self.default_options)
        self.type = name
        if attrs is not None: self.parse_options(attrs)
        if namespace is not None and not self.has_option("namespace"):
            self.options["namespace"] = namespace
        self.on_update = EventHook()
        self.on_added = EventHook()
        
    @property
    def parser(self):
        return self.parent.parser

    def endElement(self, name):
        if self.parser is not None:
            self.parser.setContentHandler(self.parent)
        
    def parse_options(self, attrs):
        self._options.merge(attrs)
        
        # XXX: Required options
        for name in self.required_options:
            if not self.has_option(name):
                raise ValueError("{0}: {1} required".format(self.type, name))
                
        # XXX: Forbidden options
        for name in self.forbidden_options:
            if self.has_option(name):
                raise ValueError("{0}: '{1}' option is forbidden".format(
                    self.type, name))
                
    @property
    def options(self):
        return self._options
        
    def has_option(self, name):
        return name in self._options
        
    @property
    def root(self):
        if self.parent is None:
            return self
        return self.parent.root
                        
    @classmethod
    def register_child(handler, name):
        def register(clas):
            # XXX: clas should be a subclass of Constants
            handler.content_types[name] = clas
            return clas
        return register
       
    @property
    def namespace(self):
        if self.has_option('namespace'):
            return self.options['namespace']
        else:
            return self.parent.namespace

class XmlConfig(XmlConfigParser):
    default_options = {
        'autoload-folder-name':     'config'
    }

    def __init__(self, name):
        self._files = {}
        self.links = {}
        self.documents = {}
        self.parent = None
        self.name = name
        # Events
        self.on_load = EventHook()

    def autoload(self, base_url="file:"):
        # Look for a file with [self.name]*.xml in current folder, then 
        # current folder and up to three parent folders inside a folder
        # named config
        # XXX wildcards will only work for local filesystem (not http:)
        try:
            self.load(base_url + self.name + ".xml")
        except:
            raise

    # XXX: Move to XmlConfigDocument interface

    def load(self, url, namespace=LOCAL_NAMESPACE, for_import=False):
        # Keep track of loaded files to ward off circular dependencies. If
        # a file is requested to be loaded that is already, and it has not
        # been modified since loading, don't load it.
        load = False
        # Get normalized, real location of url
        url = self.get_real_location(url, for_import)
        # Go ahead and open the url now so that we can check the time of
        # last update (for reloading)
        content = urlopen(url)
        if len(self._files) == 0:
            # This is the first document loaded. Remember it for future
            # reloading and importing, etc.
            self._original_url = url
        if url in self._files:
            # Don't load if the file is already loaded under a difference
            # namespace
            if self._files[url]['namespace'] != namespace:
                # Already loaded this file, so just create a link to another
                # namespace. This will allow two documents to import the same
                # document into different namespaces. Doing so without links
                # would create unnecessary imports and potential circular
                # dependency issues
                self.links[namespace] = self._files[url]['namespace']
                load = False
            #
            # XXX Check if 'last-modified' in headers
            # Reload if the file has been modified
            elif self._files[url]['headers']['last-modified'] \
                    != content.headers['last-modified']:
                load = True
        #
        # If file has never been loaded, it should be loaded (duh)
        else:
            load=True
            
        if load:
            self.on_load.fire(url, namespace)
            self._files[url] = {
                'namespace':    namespace, 
                'headers':      dict(content.headers.items())
            }
            self.parse(content, namespace)
        content.close()

    def get_real_location(self, url, for_import=False):
        # XXX: Support url as a urllib.request.Request instance as well
        #      as a string.
        # If this is an import, then mangle the url if necessary to match
        # the (relative) path of the originally-loaded document. For instance,
        # if a config file named config.xml sources a second config file
        # named config2.xml, and the first one is loded for a different path
        # as 'path/to/config.xml', when the second document is loaded, it
        # should be loaded as 'path/to/config2.xml'. In otherwords, we need
        # to transfer the leading path from the original document to the
        # one being imported. This will also be required for element content
        # sourcing as well.
        if for_import:
            # Prepend the path of the originally loaded document onto the
            # file to be loaded. Whether the new path is relative or 
            # absolute, urljoin will take care of it
            parts = urlparse(url)
            new_url = urljoin(self._original_url, parts.path)
        else:
            # Normalize the URL for consistent caching. Assume it's a file 
            # if no protocol was specified in the url. This will help ensure
            # that if the file is to be sourced later under a equivalent but
            # different URL, that it will still match this file in the URL
            # cache below.
            parts = urlparse(url)
            new_url = urlunparse((parts.scheme or 'file', parts.netloc, 
                parts.path, parts.params, parts.query, parts.fragment))
        # Fix a python bug(?): if the path didn't start with a leading 
        # slash, the urlunparse (and urlunsplit too) are nice enough
        # to put one in (for file: scheme at least)
        if not url.startswith('/'):
            return new_url.replace("file:///","file:")
        else:
            return new_url

    def parse(self, open_file, namespace):
        if namespace in self.documents:
            doc = self.documents[namespace]
        else:
            doc = self.documents[namespace] = XmlConfigDocument(
                namespace=namespace, parent=self)
        doc.parse(open_file)

    def __getitem__(self, name):
        return self.lookup(name)

    def get(self, name, default=None):
        try:
            return self[name].value
        except KeyError:
            return default

    def lookup(self, key, namespace=LOCAL_NAMESPACE):
        # XXX A regex would make more sense here
        split = key.split(self.namespace_separator, 1)
        if len(split) == 2:
            # XXX override given namespace?
            namespace=split[0]
            key=split[1]

        # Magic namespaces
        if namespace == "env":
            # Special lookup for environment variables
            return os.environ[key]

        # Namespace links
        if namespace in self.links:
            namespace = self.links[namespace]

        for ns, doc in self.documents.items():
            try:
                return doc.lookup(key, namespace)
            except KeyError:
                pass

        raise KeyError("{0}:{1}: Cannot lookup reference".format(namespace,key))

    def __iter__(self):
        for namespace, doc in self.documents.items():
            for x in doc:
                for key, y in x.items():
                    yield y

class XmlConfigDocument(XmlConfigParser):
    """
    Simple encapsulation of a config document. This will represent each 
    document that is requested to be loaded or imported.
    """
    def __init__(self, **kwargs):
        super(XmlConfigDocument, self).__init__(self, **kwargs)
        self.constants = {}
        self.default_namespace = kwargs['namespace']

    def startElement(self, name, attrs):
        if not name in self.content_types:
            # Only enter into <constant> elements (or other registered
            # supported content types)
            return
        # Keep namespace list simple
        new_element = self.content_types[name](name=name, attrs=attrs,
            parent=self, namespace=self.default_namespace)
        if new_element.namespace in self.constants:
            new_element = self.constants[new_element.namespace]
        else:
            self.constants[new_element.namespace] = new_element
        self._parser.setContentHandler(new_element)
        
    @property
    def parser(self):
        return self._parser

    def parse(self, open_file):
        self._parser = make_parser()
        self._parser.setContentHandler(self)
        self._parser.parse(open_file)

    @property
    def namespace(self):
        return self.default_namespace
       
    @property
    def namespaces(self):
        return list(self.constants.keys())
                
    def lookup(self, key, namespace):
        return self.constants[namespace].lookup(key)

    def __iter__(self):
        return iter(self.constants.values())

@XmlConfig.register_child("constants")
class Constants(XmlConfigParser, dict):

    content_types = {}
    default_options = {
        "src":          None
    }
    namespace_separator = "."
    
    def __init__(self, **kwargs):
        super(Constants, self).__init__(**kwargs)
        # Forbid 'env' namespace
        if self.has_option("namespace") and self.options["namespace"] == "env":
            raise ValueError("Cannot re-declare magic namespace 'env'")
        if self.options["src"] is not None:
            # Load in constants
            getConfig(self.root.name).load(self.options["src"], 
                self.namespace, for_import=True)
        
    def startElement(self, name, attrs):
        # Manages the handler for this element's content
        # if there is a child, then the element belongs to it
        new_constant = self.content_types[name](name=name, 
            attrs=attrs, parent=self, namespace=self.namespace)
        if new_constant.key in self:
            new_constant = self[new_constant.key]
            new_constant.clear()
            new_constant.options.merge(new_constant.default_options)
            new_constant.options.merge(attrs)
        else:
            self[new_constant.key] = new_constant
        self.parser.setContentHandler(new_constant)
        
    def lookup(self, key):
        splitkey = key.split(self.namespace_separator, 1)
        if splitkey[0] in self:
            if len(splitkey) == 2:
                return self[splitkey[0]].lookup(splitkey[1])
            return self[splitkey[0]]
        raise KeyError("{0}: Cannot find constant".format(key))
            

@Constants.register_child("string")
class SimpleConstant(XmlConfigParser):
    
    content_types={}
    content_processors=[]
    
    default_options = {
        "encoding":             None,       # Content encoding (ie. base64)
        "preserve-whitespace":  False,      # Keep all whitespace in an element
        "ordered":              False,      # Maintain order of a section
        "src":                  None,       # Where content is located
        "resolve-references":   True,       # Resolve %(key) references
        "no-cache":             False       # Don't cache content (used with src)
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
        super(SimpleConstant, self).endElement(name)
        if hasattr(self, '_prev_content') \
                and self._content != self._prev_content:
            self.on_update.fire()
            self.parent.on_update.fire(self.key)
        
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
        if self.options["no-cache"] or not hasattr(self, '_value'):
            self._value = self.parseValue()

        return self._value
        
    @property
    def key(self):
        return self.options['key']

    def parseValue(self):
        # noop for bytes
        return str(self.content)
        
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

            # Cache result (maybe)
            if not self.options["no-cache"]:
                self._content_settled=True
        return self._content

    reference_regex = re.compile(r'%\(([^%)]+)\)')
    def resolve_references(self, what):
        while True:
            m=self.reference_regex.search(what)
            if m is None: break
            # XXX This is pretty ugly
            what = what[0:m.start()] \
                + str(self.root.lookup(m.group(1), 
                    self.parent.namespace)) \
                + what[m.end():]
        return what

    @classmethod
    def register_processor(cls, after=None):
        def register(processor):
            for i,x in enumerate(cls.content_processors):
                if after is not None and isinstance(x, after):
                    cls.content_processors.insert(i+1, processor())
                    break
            else:
                cls.content_processors.append(processor())
            return processor
        return register
        
    def __repr__(self):
        return self.__unicode__()
        
    def __unicode__(self):
        return str(self.value)

class ContentProcessor(object):
    order=10
    def process(self, constant, content):
        raise NotImplementedError()
    
@SimpleConstant.register_processor()
class ContentLoader(ContentProcessor):
    def process(self, constant, content):
        if constant.options["src"] is not None:
            try:
                # Translate relative paths and such. We'll need to look up
                # the actual XmlConfig handling this constant. Its root
                # element will know the name originally passed into 
                # getConfig(name)
                url = getConfig(constant.root.name).get_real_location(
                    constant.options["src"], for_import=True)
                fp = urlopen(url)
            except ValueError:
                # Invalid url
                raise
            else:
                return fp.read()
            
@SimpleConstant.register_processor(after=ContentLoader)
class WhitespaceStripper(ContentProcessor):
    def process(self, constant, content):
        if not constant.options["preserve-whitespace"]:
            return content.strip()
            
@SimpleConstant.register_processor(after=WhitespaceStripper)
class ContentDecoder(ContentProcessor):
    def process(self, constant, content):
        if constant.options["encoding"] is not None:
            try:
                decoder = codecs.getdecoder(constant.options["encoding"])
            except LookupError:
                # Python bug(?): Try it with _codec
                decoder = codecs.getdecoder(constant.options["encoding"] + "_codec")
            # Don't convert to a string because it may be binary content.
            # It will be converted later if necessary
            return decoder(content.encode())[0]

@SimpleConstant.register_processor(after=ContentDecoder)
class Python3kStringCrap(ContentProcessor):
    def process(self, constant, content):
        # Up to this point we try and keep the data in a binary form if
        # we can. Now we'll try and convert it to a string, which will
        # be required to resolve-references
        if not constant.has_option('binary-content'):
            if type(content) is bytes:
                return content.decode()
            
@SimpleConstant.register_processor(after=Python3kStringCrap)
class ReferenceResolver(ContentProcessor):
    def process(self, constant, content):
        # Note: The resolve_references function cannot be moved here because
        #       it is necessary for some complex content types
        if constant.options["resolve-references"]:
            return constant.resolve_references(content)

@Constants.register_child("bytes")
class BinaryConstant(SimpleConstant):
    default_options = SimpleConstant.default_options.copy()
    default_options.update({
        "resolve-references":   False,
        "binary-content":       True
    })

    def parseValue(self):
        # noop
        return self.content

    def resolve_references(self, *args, **kwargs):
        raise NotImplementedError(
            "Cannot resolve references inside a binary constant")

@Constants.register_child("int")
class IntegerConstant(SimpleConstant):
    def parseValue(self):
        return int(self.content)
        
@Constants.register_child("boolean")    
@Constants.register_child("bool")    
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
        return self.options["key"]

    @property
    def value(self):
        return self
            
@Constants.register_child("decimal")
@Constants.register_child("float")
class DecimalConstant(SimpleConstant):
    def parseValue(self):
        return Decimal(self.content)
    
@Constants.register_child("list")
class ListConstant(SimpleConstant):
    default_options = SimpleConstant.default_options.copy()
    default_options.update({
        "delimiter":            ",",        # List item delimiter
        "type":                 "str"       # Type of items in a list
    })
    required_options=["delimiter","type"]
    type_funcs = {
        "str": str,
        "int": int,
        "long": int,
        "float": Decimal,
        "boolean": bool
    }
    def parseValue(self):
        T = list(self.content.split(
            self.options["delimiter"]))
        for i, x in enumerate(T):
            # Convert to declared type
            if not self.options["preserve-whitespace"]:
                x=x.strip()
            T[i] = self.type_funcs[self.options['type']](x)
        return T 

@SimpleConstant.register_child("choose")
class ChooseHandler(SimpleConstant):
    required_options=[]
    default_options={}
    forbidden_options=["key"]
    
    import socket
    # XXX Either move vars all the way up to the XmlConfig class
    #     or provide some interface to get the add_var method into
    #     the XmlConfig class
    vars = {
        "hostname": socket.gethostname()
    }
    builtins = {
        "__builtins__": {}
    }
    
    # XXX Enforce required child 'default'

    # XXX Define option for raising errors encountered in eval'ing <when>
    #     elements. (KeyError for lookups would apply too)
    
    @property
    def content(self):
        # Run when blocks
        for x in self.children:
            if isinstance(x, ChooseDefault):
                self._default = x
            elif isinstance(x, ChooseWhen):
                # Eval the test element (safely)
                try:
                    # Note that Python will add a __builtins__ element with
                    # the real builtins if one is not given
                    if eval(x.resolve_references(x.options["test"]), 
                            self.builtins, self.vars):
                        self.selected = x
                        break
                except NameError:
                    raise
                except:
                    pass
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
    
# EventHook class courtesy of Michael Foord,
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

# Load extensions
from .plugins import crypto
