# encoding: utf-8

import sys
sys.path.append(sys.path.insert(0,"../src"))

def urlopen(*args, **kwargs):
    # Only parse one arg: the url
    return Urls[args[0]]

# Provide a simple hashtable to contain the content of the urls and 
# provide a mock object similar to what will be returned from the
# real urlopen() function calls
from io import StringIO
from time import time
import re
from nose.tools import with_setup
class MockUrlContent(StringIO):
    def __init__(self, content):
        super(MockUrlContent, self).__init__(content)
        self.headers = {
            'last-modified': time()
        }

    def close(self):
        pass
    
scheme_re = re.compile(r'file:(/+)?')
class MockUrlCache(dict):
    def __setitem__(self, name, content):
        super(MockUrlCache, self).__setitem__(name, MockUrlContent(content))

    def __getitem__(self, name):
        if name in self:
            return super(MockUrlCache, self).__getitem__(name)
        # Strip off 'file:[///]' from url
        elif name.startswith('file:'):
            try:
                name= scheme_re.sub('', name)
                return super(MockUrlCache, self).__getitem__(name)
            except:
                # Fall through
                pass
        # urlopen raises ValueError if unable to load content (not KeyError)
        raise ValueError("{0}: Cannot find file content".format(name))

Urls = MockUrlCache()

def clear_configs():
    pass

@with_setup(clear_configs)
def testImportContent():
    "Cannot import content from a file"
    from xmlconfig import getConfig
    Urls.clear()
    Urls["file:file.txt"] = "Content embedded in a file"
    Urls["config.xml"] = \
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="import" src="file:file.txt"/>
        </constants>
    </config>
    """
    conf=getConfig()
    conf.load("config.xml")
    assert conf.get("import") == "Content embedded in a file"

@with_setup(clear_configs)
def testImportConfig():
    "Cannot import another config file"
    from xmlconfig import getConfig
    Urls.clear()
    Urls["config2.xml"] = \
    """<?xml version="1.0"?>
    <config>
        <constants>
            <string key="key22">This was imported from config2.xml</string>
        </constants>
    </config>
    """
    Urls["config.xml"] = \
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants namespace="import" src="file:config2.xml"/>
        <constants>
            <string key="imported">%(import:key22)</string>
        </constants>
    </config>
    """
    conf=getConfig()
    conf.load("config.xml")
    assert conf.get("imported") == "This was imported from config2.xml"

@with_setup(clear_configs)
def testCircularImport():
    "Property detect circluar importing"
    from xmlconfig import getConfig
    Urls.clear()
    Urls["config2.xml"] = \
    """<?xml version="1.0"?>
    <config>
        <constants namespace="circular" src="file:config.xml"/>        
        <constants>
            <string key="key22">This was imported from config2.xml</string>        
            <string key="foreign">
                Namespace changed in %(circular:key4.import)
            </string>
        </constants>
    </config>
    """
    Urls["config.xml"] = \
    """<?xml version="1.0"?>
    <config>
        <constants namespace="import" src="file:config2.xml"/>
        <constants>
            <section key="key4">
                <string key="key5">value2</string>
                <string key="import">%(import:key22)</string>
            </section>
        </constants>
    </config>
    """
    conf=getConfig()
    conf.load("config.xml")
    assert conf.get("import:foreign") == \
        "Namespace changed in This was imported from config2.xml"

@with_setup(clear_configs)
def testRelativeImport():
    """Transfer leading absolute or relative path to the location of 
    documents imported"""
    from xmlconfig import getConfig
    Urls["../config/config2.xml"] = \
    """<?xml version="1.0"?>
    <config>
        <constants>
            <string key="key22">This was imported from config2.xml</string>
        </constants>
    </config>
    """
    Urls["../config/config.xml"] = \
    """<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants namespace="import" src="file:config2.xml"/>
        <constants>
            <string key="imported">%(import:key22)</string>
        </constants>
    </config>
    """
    conf=getConfig()
    conf.load("../config/config.xml")
    assert conf.get("imported") == "This was imported from config2.xml"
    
