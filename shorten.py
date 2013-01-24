import plugin


class Plugin(plugin.Plugin):
    def register_commands(self):
        self.commands = [
            ('shorten <url>', self.shorten)
        ]

    def shorten(self, message, args):
        """
        Shorten a URL

        $<comchar>shorten http://nkd.su/

        >luser: http://waa.ai/garbage
        """

        short = self.shorten_url(args['url'])

        if message.source != message.nick:
            string = '%s: %s' % (message.nick, short)
        else:
            string = short

        self.irc.privmsg(message.source, string)
