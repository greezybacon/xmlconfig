# encoding: utf-8

"""
Command line interface for xmlconfig. It provides an extensible set of 
commands for validating documents, as well as locking and unlocking 
the content of encrypted elements.
"""

class CliCommand(object):
    """
    Extensible command-line command designed around optparse. It allows for
    a list of exported options using the make_option() function from 
    optparse, and a custom usage in the help output. Subclasses should be
    decorated with the register() classmethod for plumbing. Registered
    subclasses will automatically be available via the 'xmlconfig' command-
    line script.

    The only required function for implementation is the run() method which
    will receive the parsed options and arguments. This method just needs 
    to do the work, because command-line arguments and options, including
    help output, have already been processed before the run() method 
    is invoked.
    """
    __command__ = ""
    __args__ = []
    __help__ = "(Undocumented)"
    __usage__ = "%prog {0} [options]"
    __registry__ = {}

    def run(self, options, *args): 
        raise NotImplementedError

    @classmethod
    def register(cls, command):
        cls.__registry__[command.__command__] = command

    @classmethod
    def get(cls, command):
        return cls.__registry__[command]

from xmlconfig.plugins import *
import xmlconfig.validate
from optparse import OptionParser
import sys
def cli_main():
    args = sys.argv[1:]
    # Look up the command
    try:
        cmd = CliCommand.get(args[0])
        op = OptionParser(option_list=cmd.__args__, usage=cmd.__usage__
            .format(args[0]))
        options, args = op.parse_args(args=args[1:])
        cmd().run(options, *args)
    except Exception:
        op = OptionParser(usage="%prog command [options]",
            epilog="For detailed help on individual commands, use the "
                   "--help option with the command")
        op.print_help()
        print("\nAvailable commands include:")
        for name, clas in CliCommand.__registry__.items():
            print("    % -12s %s" % (name, clas.__help__))
