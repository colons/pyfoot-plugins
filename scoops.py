import plugin
from urllib import request


class Plugin(plugin.Plugin):
    def register_commands(self):
        self.commands = [
            ('scoops', self.scoop)
        ]

    def scoop(self, message, args):
        """
        Get a [scoop](http://hotscoops.co/) from the [scoops
        API](http://hotscoops.co/raw).
        """

        scoop = request.urlopen('http://hotscoops.co/raw').read().decode(
            'utf-8')
        self.irc.privmsg(message.source, scoop)
