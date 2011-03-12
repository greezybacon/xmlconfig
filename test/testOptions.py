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

# ------------------->> encodings <<----------------------
def testFloatBase64Encoded():
    from xmlconfig import getConfig, LOCAL_NAMESPACE
    from core import stringIOWrapper
    from decimal import Decimal
    conf=getConfig()
    conf.parse(stringIOWrapper(
    u"""<?xml version="1.0" encoding="utf-8"?>
    <config>
        <constants>
            <float key="long_pi" encoding="base64">
                My4xNDE1OTI2NTM1ODk3OTMyMzg0NjI2NDMzODMyNzk1MDI4ODQxOTcxNjkzOTkz
                NzUxMDU4MjA5NzQ5NDQ1OTIzMDc4MTY0MDYyODYyMDg5OTg2MjgwMzQ4MjUzNDIx
                MTcwNjc5ODIxNDgwODY1MTMyODIzMDY2NDcwOTM4NDQ2MDk1NTA1ODIyMzE3MjUz
                NTk0MDgxMjg0ODExMTc0NTAyODQxMDI3MDE5Mzg1MjExMDU1NTk2NDQ2MjI5NDg5
                NTQ5MzAzODE5NjQ0Mjg4MTA5NzU2NjU5MzM0NDYxMjg0NzU2NDgyMzM3ODY3ODMx
                NjUyNzEyMDE5MDkxNDU2NDg1NjY5MjM0NjAzNDg2MTA0NTQzMjY2NDgyMTMzOTM2
                MDcyNjAyNDkxNDEyNzM3MjQ1ODcwMDY2MDYzMTU1ODgxNzQ4ODE1MjA5MjA5NjI4
                MjkyNTQwOTE3MTUzNjQzNjc4OTI1OTAzNjAwMTEzMzA1MzA1NDg4MjA0NjY1MjEz
                ODQxNDY5NTE5NDE1MTE2MDkK
            </float>
        </constants>
    </config>
    """), LOCAL_NAMESPACE)
    assert conf.get("long_pi") == Decimal('3.14159265358979323846264338327950288'
        '41971693993751058209749445923078164062862089986280348253421170679821480'
        '86513282306647093844609550582231725359408128481117450284102701938521105'
        '55964462294895493038196442881097566593344612847564823378678316527120190'
        '91456485669234603486104543266482133936072602491412737245870066063155881'
        '74881520920962829254091715364367892590360011330530548820466521384146951'
        '941511609')
    
