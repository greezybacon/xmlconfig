# encoding: utf-8

"""
Command line interface for xmlconfig. It provides an extensible set of 
commands for validating documents, as well as locking and unlocking 
the content of encrypted elements.
"""

class CliCommand(object):
    __command__ = ""
    __registry__ = {}
    # XXX Support a help interface with optparse

    run = NotImplemented

    @classmethod
    def register(cls, command):
        cls.__registry__[command.__command__] = command

    @classmethod
    def get(cls, command):
        return cls.__registry__[command]

from xmlconfig.plugins import *
import sys
def cli_main():
    args = sys.argv[1:]
    # Look up the command
    try:
        cmd = CliCommand.get(args[0])
        cmd().run(*args[1:])
    except:
        raise
        print("{0}: Invalid command. Use --help for help"
            .format(args[0]))
