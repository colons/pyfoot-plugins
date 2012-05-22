import time
#import codecs
from os import path,mkdir

from translate import Translator
import plugin 

defaults = {
        'party_via': 'ja',
        'party_dir': '~/.pyfoot/party/'
        }


def dupes(party):
    """ Returns True if the latest phrase appears twice in our party """
    if ''.join(party[-1:]) in [party[i] for i in range(0, len(party)-1, 2)]:
        return True
    else:
        return False

class Plugin(plugin.Plugin):
    def prepare(self):
        self.translator = Translator(self.conf.conf['bing_app_id'])

    def register_commands(self):
        self.commands = [
                ('party <<phrase>>', self.party),
                ('partyvia <lang> <<phrase>>', self.partyvia),
                ]
    

    def party(self, message, args):
        """ A recreation of <a href="http://translationparty.com/">Translation Party</a> using the Bing translate API.
        $<comchar>party scissor me timbers
        >I have a tree.\x03# |\x03 \x027\x02 attempts\x03# |\x03 http://woof.bldm.us/party/<network>/Derasonika-120213-235608 """
        try:
            transvia = args['lang']
        except AttributeError:
            transvia = self.conf.conf['party_via']

        party = [args['phrase']]
        while dupes(party) == False:
            party.append(self.translator.translate('en', transvia, party[-1]))
            party.append(self.translator.translate(transvia, 'en', party[-1]))
        
        filename = '%s-%s' % (message.nick, time.strftime('%y%m%d-%H%M%S'))
        filepath = path.expanduser(self.conf.conf['party_dir']+self.conf.alias+'/')
        if not path.exists(filepath):
            mkdir(filepath)
        elif path.exists(filepath) and not path.isdir(filepath):
            raise OSError('\'party_dir\' is not a directory')
        filepath = filepath+filename+'.txt'

        sup = '\n'.join(party)
        metadata = 'source: %s, via: %s' % (message.source, transvia)

        print ' -- Writing to %s...' % filepath
        file = open(filepath, mode='w')
        file.write(metadata)
        file.write(sup)
        file.close()
        
        attempts = (len(party)-1)/2
        self.irc.privmsg(message.source, '%s | \x02%i\x02 attempts | %sparty/%s/%s/' % (party[-1], attempts, self.conf.conf['web_url'], self.conf.alias, filename), pretty=True)


    def partyvia(self, message, args):
        """ Specify a language code, must be both <a href="http://msdn.microsoft.com/en-us/library/dd877907.aspx">here</a> and <a href="http://msdn.microsoft.com/en-us/library/dd877886.aspx">here</a> """
        self.party(message, args)
