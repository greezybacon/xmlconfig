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

def testForwardReference():
    "Reference a constant that has not yet been defined"
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="ref2">This is a forward %(key7)</string>
    
            <!-- This is a comment -->
            <string key="key7">reference</string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("ref2") == "This is a forward reference"

def testForwardForeignNamespace():
    "Reference a constant in a namespace that is defined later"
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="key8">This is a reference to a %(other:foreign) namespace</string>
        </constants>
        <constants namespace="other">
            <string key="foreign">foreign</string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("key8") == "This is a reference to a foreign namespace"
    assert conf.get("other:foreign") == "foreign"

def testEncryptedReference():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="password" options="salt:pYzSxGhzoc4H;encoding:base64">
                UhRy2pLYh6g=
            </string>
            
            <!-- This cryptic constant has an embedded reference to %(password),
                 so it tests the order of decoding, decryption, and reference
                 resolution -->
            <string key="encrypted-with-ref" salt="t3J6jETFKlsN" encoding="base64">
                dv5XkQCiUXW0EgL3uc0fUmsOA6+CK9G9S2pj+X+HgphMd/cPPNAtMw==
            </string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("encrypted-with-ref") == "Encrypted reference to password"

def testClearEncryptedReference():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="password" options="salt:pYzSxGhzoc4H;encoding:base64">
                UhRy2pLYh6g=
            </string>
            
            <string key="dsn">
                DSN=ODBC;UID=schema;PWD=%(password)
            </string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("dsn") == 'DSN=ODBC;UID=schema;PWD=password'

def testNestedDictReference():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <!-- Test for a nested dictionary -->
            <section key="dict_in_dict">
                <section key="internal_dict">
                    <string key="inside">Inside a dict inside a dict</string>
                </section>
            </section>
            
            <string key="nested_dict_ref">%(dict_in_dict.internal_dict.inside)</string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("nested_dict_ref") == "Inside a dict inside a dict"

def testSectionReference():
    "Reference an entire section"
    from xmlconfig import getConfig, LOCAL_NAMESPACE, SectionConstant
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <section key="key4">
                <string key="key5">value2</string>
            </section>
            <!-- Reference an entire section -->
            <section key="section_import">%(key4)</section>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    # XXX This really should be returned as a dict type
    assert type(conf.get("section_import")) is SectionConstant
