from random import choice

import plugin


defaults = {
    'rantext_sources': [],
    'rantext_frames': {},
}


class Plugin(plugin.Plugin):
    """
    Retrieve a random line from a text file. Can be directed at individuals.
    """

    def register_commands(self):
        self.commands = []

        self.sources = {}

        for source in self.conf['rantext_sources']:
            filename = '%s/rantext/%s.txt' % (self.conf['content_dir'],
                                              source)
            file = open(filename, encoding="utf-8")
            line_list = []
            for line in file:
                line_list.append(line)
            self.sources[source] = line_list

        for source in self.sources:
            everyone_func = lambda message, args: self.rantext(message, args)
            everyone_func.__doc__ = '>%s' % choice(self.sources[source])

            targetted_func = lambda message, args: self.rantext(message, args)

            self.commands.append((source, everyone_func))
            self.commands.append(('%s <<nick>>' % source, targetted_func))

    def rantext(self, message, args):
        sourcename = args['_command'].split(' ')[0]
        source = self.sources[sourcename]
        line = choice(source)

        if sourcename in self.conf['rantext_frames']:
            line = self.conf['rantext_frames'][sourcename] % line

        if 'nick' in args:
            line = '%s: %s' % (args['nick'], line)

        self.irc.privmsg(message.source, line)
