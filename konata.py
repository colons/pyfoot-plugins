import plugin


class Plugin(plugin.Plugin):
    def register_commands(self):
        self.commands = [
            ('konata <<nick>>', self.konata)
        ]

    def konata(self, message, args):
        """
        Expresses affection. Verbose.

        $<comchar>konata Duke Togo

        >I like Duke Togo because she is a otaku like me, except she has
        friends. Oh god I wish I had friends too ;_;
        """
        nick = args['nick']

        for line in [
            'I like %s because she is a otaku like me, except she has friends.'
            ' Oh god I wish I had friends too ;_;',

            '%s also likes videogames and she is kawaii. And there are '
            'lesbians in the show and that\'s good because I like lesbians and'
            ' I will never have a girlfriend. Why am I such a loser?!',

            '%s is like my dreamgirl she has a :3 face I love that. She is '
            'also nice why aren\'t real girls nice!? I got dumped a lot of '
            'times but I love %s and she wouldn\'t dump me because she\'s so '
            'nice and cool.',

            'We would play videogames all day and watch Naruto and other cool '
            'animes on TV, and I would have sex with her because sex is so '
            'good. I wish I could have sex with a girl'
        ]:
            self.irc.privmsg(message.source, line.replace('%s', nick))
