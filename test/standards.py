from xmlconfig import getConfig

c=getConfig("config")
c.autoload()
for n in c:
    print(n.namespace, ":", n.key, ":", n)
