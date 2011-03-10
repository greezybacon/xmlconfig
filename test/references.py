# encoding: utf-8

import sys
sys.path.append(sys.path.insert(0,"../src"))

def testBasicReference():
    "References match %(name)"
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="ref">reference value</string>
            <string key="tramp">%(ref)</string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("tramp") == "reference value"

def testReferenceChangeType():
    """
    Type should be determined by the constant enclosing the reference, not
    the referencee
    """
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <int key="int-ref">42</int>
            <string key="tramp2">%(int-ref)</string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("tramp2") == "42"
    assert type(conf.get("tramp2")) is str

def testReferenceInvalid():
    "Invalid references should default to None"
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <int key="int-ref">42</int>
            <string key="tramp3">%(int ref)</string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("tramp3") is None

def testEnvironmentReference():
    "The magic 'env' namespace should refer to environment variables"
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    import os
    os.environ['test_var'] = 'xmlconfig is sweet'
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
           <string key="env">%(env:test_var)</string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("test_var") == "xmlconfig is sweet"

def testReferenceChars():
    "Incomplete references should not break"
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
           <string key="not-a-ref">%(int</string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("not-a-ref") == "%(int"
