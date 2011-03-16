import sys
sys.path.append(sys.path.insert(0,"../src"))

# ------------- Test basic types ---------------
def testTypeString():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="str">string</string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("str") == "string"
    assert type(conf.get("str")) is str

def testTypeInt():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <int key="int">299792458</int>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("int") == 299792458
    assert type(conf.get("int")) is int

def testTypeFloat():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <float key="float">3.14159265359</float>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)

    # Float element returns Decimal-s for precision
    from decimal import Decimal
    assert conf.get("float") == Decimal('3.14159265359')
    assert type(conf.get("float")) is Decimal

def testTypeFloatExponent():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <float key="avagadro">6.023E+23</float>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    from decimal import Decimal
    print conf.get("avagadro")
    assert conf.get("avagadro") == Decimal('6.023E+23')

    # Float element returns Decimal-s for precision
    from decimal import Decimal
    assert conf.get("float") == Decimal('3.14159265359')
def testTypeBool():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <bool key="bool1">False</bool>
            <bool key="bool2">True</bool>
            <bool key="bool3">1</bool>
            <bool key="bool4">0</bool>
            <bool key="bool5"></bool>
            <bool key="bool6">Non-empty string</bool>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("bool1") is False
    assert conf.get("bool2") is True
    assert conf.get("bool3") is True
    assert conf.get("bool4") is False
    assert conf.get("bool5") is False
    assert conf.get("bool6") is True

def testTypeList():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <list key="list">1,2,3,4,5</list>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    # Default type for list items is str
    assert conf.get("list") == ["1","2","3","4","5"]
    assert type(conf.get("list")) is list
    
def testTypeDict():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <section key="dict">
                <string key="item1">item1</string>
                <int key="item2">1000</int>
            </section>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert 'item1' in conf.get("dict")
    assert 'item2' in conf.get("dict")
    # XXX This interface isn't really nice -- lose the .value
    assert conf.get("dict")["item1"].value == "item1"
    assert conf["dict"]["item2"].value == 1000
    assert type(conf.get("dict").get("item1").value) is str
    assert type(conf["dict"].get("item2").value) is int

def testNestedDict():
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
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert "internal_dict" in conf.get("dict_in_dict")
    assert "inside" in conf.get("dict_in_dict").get("internal_dict")
    assert conf.get("dict_in_dict.internal_dict.inside") == \
        "Inside a dict inside a dict"

def testTypeChoose():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="default">
                <choose>
                    <default>default</default>
                    <when test="1==0">when</when>
                </choose>
            </string>
            <string key="chosen">
                <choose>
                    <default>default</default>
                    <when test="1==1">when</when>
                </choose>
            </string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("default") == "default"
    assert type(conf.get("default")) is str
    assert conf.get("chosen") == "when"
    assert type(conf.get("chosen")) is str

from nose.tools import raises

@raises(NameError)
def testChooseImportOs():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="please_break">
                <choose>
                    <default/>
                    <when test="__import__('os').getuid() != 0">broken</when>
                </choose>
            </string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("please_break") == ""

# XXX Add binary constant

def testTypeEncrypted():
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
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("password") == "password"

