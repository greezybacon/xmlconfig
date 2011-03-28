# encoding: utf-8

"""
Validation mechanisms for xmlconfig. Basically consists of a command-line
tools for now
"""

from xml.sax import make_parser
from xml.sax.handler import ErrorHandler
from xml.sax.xmlreader import Locator
from xmlconfig import getConfig, urlopen, EventHook, SimpleConstant
from xmlconfig.cli import CliCommand
import os

class Validator(object):
    checks = []

    def __init__(self):
        self.on_error = EventHook()
        self.on_warning = EventHook()

    def validate(self, url):
        config = getConfig()
        # Use the on_load event, because, if the document imports other
        # documents, we want to validate them all. (XXX Do we really?)
        config.on_load += self.validate_file
        try:
            config.load(url)
        except:
            # We should catch the errors in one or more of the validation
            # checks. (Fingers crossed.)
            pass

    def validate_file(self, url):
        try:
            content = urlopen(url)
        except ValueError as ex:
            self.on_error.fire(ex)
        else:
            for check in self.checks:
                content.seek(0)
                x = check(content)
                # Plumb the check events to the local events
                x.on_error += self.on_error.fire
                x.on_warning += self.on_warning.fire
            content.close()

    @classmethod
    def register(cls, check):
        cls.checks.append(check)

class ValidationCheck(object):
    def __init__(self, document):
        self.document = document
        self.on_warning = EventHook()
        self.on_error = EventHook()

    def check(self):
        """
        Validation function that fires the on_error and on_warning events.
        If no events are fired, then the document is quietly confirmed
        to be valid.
        """
        pass

class ValidationError(Exception):
    pass

@Validator.register
class WellFormedness(ValidationCheck, ErrorHandler):
    """
    Simple check for document well-formedness. This check will be delegated
    to the built-in Python xml parser
    """
    def check(self):
        p = make_parser()
        self.locator = Locator()
        p.setDocumentLocator(self.locator)
        p.setErrorHandler(self)
        p.parse(self.document)
        return iter(self. error_list)

    def error(self, exception):
        self.on_error.fire(exception)

    fatal_error = error

    def warning(self, exception):
        self.on_warning.fire(exception)

@Validator.register
class CheckReferences(ValidationCheck):
    reference_regex = SimpleConstant.reference_regex

@CliCommand.register
class ValidateConfigFile(CliCommand):
    __command__ = "validate"
    __help__ = "Validate structure and contents of a xmlconfig document"

    def __init__(self, *args, **kw):
        super(ValidateConfigFile, self).__init__(*args, **kw)
        self.errors=0
        self.warnings=0
    
    def run(self, options, *args):
        if not os.path.exists(args[0]):
            raise ValueError("{0}: Config file does not exist".format(args[0]))

        val = Validator()
        val.on_error += self.emit_error
        val.on_warning += self.emit_warning
        val.validate("file:" + args[0])

        print("Valiation finished with {0} errors and {1} warnings"
            .format(self.errors, self.warnings))

    def emit_warning(self, exception):
        self.warnings += 1

    def emit_error(self, exception):
        self.errors += 1
