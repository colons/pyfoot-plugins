from os import path
from random import choice
import re

import module

class Module(module.Module):
    def register_commands(self):
        self.commands = [
                ('hhg <character>', self.quote),
                ('hhg', self.quote_anyone)
                ]
    
    def quote_anyone(self, message, args):
        args['character'] = ''
        self.quote(message, args)

    def quote(self, message, args):
        """ Retrieves a random quote from the first two phases of the Hitchhiker's Guide to the Galaxy radio series with an optional character name filter.
        $<comchar>hhg slarti
        >Shocking cock-up. The mice were furious."""
        character = args['character']
        
        hhg = open(path.expanduser(self.conf.get('content_dir')+'hhg.txt'))
        linelist = []

        character = character.strip()
                        
        match = re.compile('^%s' % character, re.IGNORECASE)
        for line in hhg:
            if match.search(line):
                quote = ''.join(line.split(':')[1:])
                linelist.append(quote)

        self.irc.privmsg(message.source, choice(linelist))
