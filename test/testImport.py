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
class MockUrlContent(StringIO):
    def __init__(self, content):
        super(MockUrlContent, self).__init__(content)
        self.headers = {
            'last-modified': time()
        }

    def close(self):
        pass
    
class MockUrlCache(dict):
    def __setitem__(self, name, content):
        super(MockUrlCache, self).__setitem__(name, MockUrlContent(content))

    def __getitem__(self, name):
        if name in self:
            return super(MockUrlCache, self).__getitem__(name)
        raise ValueError("{0}: Cannot find file content")

Urls = MockUrlCache()

def testImportContent():
    "Cannot import content from a file"
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    Urls.clear()
    Urls["file:file.txt"] = "Content embedded in a file"
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="import" src="file:file.txt"/>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("import") == "Content embedded in a file"

def testImportConfig():
    "Cannot import another config file"
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    Urls.clear()
    Urls["file:config2.xml"] = \
    """<?xml version="1.0"?>
    <config>
        <constants>
            <string key="key22">This was imported from config2.xml</string>
        </constants>
    </config>
    """
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants namespace="import" src="file:config2.xml"/>
        <constants>
            <string key="imported">%(import:key22)</string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("imported") == "This was imported from config2.xml"

def testCircularImport():
    "Property detect circluar importing"
    from xmlconfig import getConfig
    Urls.clear()
    Urls["file:config2.xml"] = \
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
    Urls["file:config.xml"] = \
    """<?xml version="1.0" encoding="utf-8"?>
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
