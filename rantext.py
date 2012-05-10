from random import choice
from copy import copy

import module


class Module(module.Module):
    """ Retrieve a random line from a text file. Can be directed at individuals. """
    def register_commands(self):
        self.commands = []

        self.sources = {}

        for source in self.conf.get('rantext_sources'):
            filename = self.conf.get('content_dir')+source+'.txt'
            file = open(filename)
            line_list = []
            for line in file:
                line_list.append(line)
            self.sources[source] = line_list

        for source in self.sources:
            everyone_func = lambda message, args: self.rantext(message, args)
            everyone_func.__doc__ = '$<comchar>%s\n>%s' % (source, choice(self.sources[source]))

            targetted_func = lambda message, args: self.rantext(message, args)

            self.commands.append((source, everyone_func))
            self.commands.append(('%s <nick>' % source, targetted_func))

    def rantext(self, message, args):
        source = self.sources[args['_command'].split(' ')[0]]
        line = choice(source)

        if 'nick' in args:
            line = '%s: %s' % (args['nick'], line)

        self.irc.privmsg(message.source, line)
