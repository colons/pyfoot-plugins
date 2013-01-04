# -*- coding: utf-8 -*-

import plugin
from urllib import request
from random import choice
import re

class Plugin(plugin.Plugin):
    def register_commands(self):
        self.commands = [
                ('gb', self.gb)
                ]

    def gb(self, message, args):
        """ Pull a quote from the <a href="http://www.deertier.com/gb/">Giant Bomb Quoter</a>. """
        lines = request.urlopen('http://www.deertier.com/gb/quotes.js')
        quotes = []
        for line in lines:
            line = line.decode('utf-8')

            match = re.match('\s*{name:\s*"([^"]+)",\s*quote:\s*"([^"]+)"},', line)
            if match:
                quotation = re.sub('<[^>]+?>', '\x02', match.group(2))
                quote = {
                        'quote': quotation,
                        'author': match.group(1),
                        }
                quotes.append(quote)
        
        quote = choice(quotes)
        quotation = '“%s” -%s' % (quote['quote'], quote['author'])

        self.irc.privmsg(message.source, quotation)
