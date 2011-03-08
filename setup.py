#!/usr/bin/python
# (c) 2011 klopen Enterprises.  See LICENSE.txt file for details

from distutils.core import setup

setup(
    name="xmlconfig",
    license="BSD",
    version="0.1.0",
    description="xml-based configuration parser for Python",
    author="Jared Hancock",
    author_email="gravydish@gmail.com",
    url="http://code.google.com/p/xmlconfig/",
    packages=["xmlconfig","xmlconfig.plugins","xmlconfig.plugins.crypto"],
    package_dir={"xmlconfig": "src/xmlconfig"},
    scripts=["bin/xmlconfig"],
    long_description="""xmlconfig is a feature rich configuration parser 
    for the Python programming language providing a more flexable approach
    to configuring daemon-based software. It provides complex configuration
    options such as conditional elements, encrypted elements, distributed 
    configuration, strong typing, and extensibility.""",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "License :: OSI Aproved :: BSD License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.2",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries",
        "Topic :: Text Processing :: Markup :: XML"
    ]
)
