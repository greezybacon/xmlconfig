# encoding: utf-8

import sys
# Prefer over installed version
sys.path.append(sys.path.insert(0,"../src"))


def stringIOWrapper(what):
    from io import StringIO
    f=StringIO()
    f.write(what)
    f.seek(0)
    return f

# ---------------- Test loading -----------------
def getConfigFile1():
    return stringIOWrapper(u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="key1">string</string>
        </constants>
    </config>
    """)

def testLoad():
    "Auto prepend file: to the open url"
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    conf=getConfig("")
    conf.parse(getConfigFile1(), LOCAL_NAMESPACE)
    assert conf.get("key1") is not None

def testGetDefault():
    "XMLConfig::get should return the default if the key is not found"
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    conf=getConfig()
    conf.parse(getConfigFile1(), LOCAL_NAMESPACE)
    assert conf.get("key1") == "string"
    assert conf.get("key2","default") == "default"
