import sys, os.path
sys.path.append(os.path.abspath("../.."))

from xmlconfig import getConfig

c=getConfig("config")
c.autoload()
for n in c:
    print(n.namespace, ":", n.key, ":", n)
