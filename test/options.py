# encoding: utf-8

import sys
sys.path.append(sys.path.insert(0,"../src"))

def testWhitespace1():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="preserved" options="preserve-whitespace">
            </string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("preserved") == "\n            "

def testWhitespace2():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <string key="preserved2" preserve-whitespace="true">
            </string>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("preserved2") == "\n            "

def testSimpleDelimiter():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <list key="star-delimiter" delimiter="*">
            1*2*3*4
            </list>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert len(conf.get("star-delimiter")) == 4

def testDelimiterNoWhitespace():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <list key="no-ws-delimiter" delimiter=",">
            1,
            2,
            3,
            4
            </list>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert len(conf.get("no-ws-delimiter")) == 4
    assert conf.get("no-ws-delimiter")[1] == "2"

def testListPreserveWhitespace():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <list key="ws-delimiter" delimiter="," preserve-whitespace="true">
            1,
            2,
            3,
            4
            </list>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert len(conf.get("ws-delimiter")) == 4
    assert conf.get("ws-delimiter")[1] == "            2"

def testMultiCharDelimiter():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <list key="crazy-delimiter" delimiter="-==-">
            1-==-2-==-3-==-4
            </list>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert len(conf.get("crazy-delimiter")) == 4

