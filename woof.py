import plugin

defaults = {
        'woof_trigger': '(?i).*(\\btrench|woo+f|good dog|bad dog|good boy|treat|\\bmeow\\b|\\bbark\\b|\\barf\\b|\\bfetch\\b|\\bmoo+\\b|\\bqua+ck\\b|\\bcluck\\b|\\bwalk\\b|\\bwalkie\\b|\\bwalkies\\b|\\bho+nk\\b|\\bwo+nk\\b|\\bsqua+wk\\b|\\bca+w\\b|\\boink\\b|\\bnya|\\bwan\\b|\\bnyro|\\bgeso|\\bneigh\\b|\\bcollar\\b|\\bawoo+\\b|\\bwan\\b|\\btwee+t\\b).*',
        'woof_greeting': 'woof',
        }

class Plugin(plugin.Plugin):
    def register_commands(self):
        self.regexes = [
                (self.conf.get('woof_trigger'), self.woof),
                ]

    def woof(self, message, args):
        """ He's a <a href="http://d.bldm.us/gallery/photos/a3300/120125%20006.jpg">dog</a>; he's excitable.
        $woof
        >woof"""
        self.irc.privmsg(message.source, self.conf.get('woof_greeting'))
