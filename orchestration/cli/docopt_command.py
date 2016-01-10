from __future__ import absolute_import
from __future__ import unicode_literals

import sys
from inspect import getdoc

from docopt import docopt
from docopt import DocoptExit

import logging
log = logging.getLogger(__name__)

def docopt_full_help(docstring, *args, **kwargs):
    try:
        return docopt(docstring, *args, **kwargs)
    except DocoptExit:
        raise SystemExit(docstring)


class DocoptCommand(object):
    def docopt_options(self):
        return {'options_first': True}

    def sys_dispatch(self):
        log.info("sys.argv")
        log.info(sys.argv)
        self.dispatch(sys.argv[1:], None)

    def nap_sys_dispatch(self, path, username, password):
#        log.info("sys.argv")
#        log.info(sys.argv)
        arg = ['up', '-d']
        self.nap_dispatch(arg, path, username, password, None)

    def dispatch(self, argv, global_options):
        self.perform_command(*self.parse(argv, global_options))

    def nap_dispatch(self, argv, path, username, password, global_options):
        self.nap_perform_command(*self.nap_parse(argv, global_options, path, username, password))

    def nap_parse(self, argv, global_options, path, username, password):
        options = docopt_full_help(getdoc(self), argv, **self.docopt_options())
        command = options['COMMAND']

        if command is None:
            raise SystemExit(getdoc(self))

        handler = self.get_handler(command)
        docstring = getdoc(handler)

        if docstring is None:
            raise NoSuchCommand(command, self)

        command_options = docopt_full_help(docstring, options['ARGS'], options_first=True)
        return options, handler, command_options, path, username, password

    def parse(self, argv, global_options):
        options = docopt_full_help(getdoc(self), argv, **self.docopt_options())
        command = options['COMMAND']

        if command is None:
            raise SystemExit(getdoc(self))

        handler = self.get_handler(command)
        docstring = getdoc(handler)

        if docstring is None:
            raise NoSuchCommand(command, self)

        command_options = docopt_full_help(docstring, options['ARGS'], options_first=True)
        return options, handler, command_options

    def get_handler(self, command):
        command = command.replace('-', '_')

        if not hasattr(self, command):
            raise NoSuchCommand(command, self)

        return getattr(self, command)


class NoSuchCommand(Exception):
    def __init__(self, command, supercommand):
        super(NoSuchCommand, self).__init__("No such command: %s" % command)

        self.command = command
        self.supercommand = supercommand
