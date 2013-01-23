import plugin

defaults = {
    'woof_trigger': (
        r'(?i).*(\btrench|woo+f|good dog|bad dog|good boy|treat|\bmeow\b|\bbar'
        r'k\b|\barf\b|\bfetch\b|\bmoo+\b|\bqua+ck\b|\bcluck\b|\bwalk\b|\bwalki'
        r'e\b|\bwalkies\b|\bho+nk\b|\bwo+nk\b|\bsqua+wk\b|\bca+w\b|\boink\b|\b'
        r'nya|\bwan\b|\bnyro|\bgeso|\bneigh\b|\bcollar\b|\bawoo+\b|\bwan\b|\bt'
        r'wee+t\b).*'
    ),
    'woof_greeting': 'woof',
}


class Plugin(plugin.Plugin):
    def register_commands(self):
        self.regexes = [
            (self.conf.conf['woof_trigger'], self.woof),
        ]

    def woof(self, message, args):
        """
        Xe's a [dog](https://colons.snapjoy.com/albums/205814788331186243);
        xe's excitable.

        $woof

        >woof
        """

        self.irc.privmsg(message.source, self.conf.conf['woof_greeting'])
