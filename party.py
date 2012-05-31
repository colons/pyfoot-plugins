import time
#import codecs
from os import path, mkdir, listdir
from bottle import template, HTTPError

from .translate import Translator
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
        self.party_path = path.expanduser(self.conf.conf['party_dir']+'/'+self.conf.alias+'/')

        self.commands = [
                ('party <<phrase>>', self.party),
                ('partyvia <lang> <<phrase>>', self.partyvia),
                ]

    def register_urls(self):
        self.urls = [
                ('/party/%s/' % self.conf.alias, self.party_index),
                ('/party/%s/<filename>/' % self.conf.alias, self.party_detail),
                ]

    def party(self, message, args):
        """ A recreation of <a href="http://translationparty.com/">Translation Party</a> using the Bing translate API.
        $<comchar>party scissor me timbers
        >I have a tree. \x03#|\x03 \x027\x02 attempts \x03#|\x03 http://woof.bldm.us/party/<network>/luser-120213-235608 """
        try:
            transvia = args['lang']
        except KeyError:
            transvia = self.conf.conf['party_via']

        party = [args['phrase']]
        while dupes(party) == False:
            party.append(self.translator.translate('en', transvia, party[-1]))
            party.append(self.translator.translate(transvia, 'en', party[-1]))

        filename = '%s-%s' % (message.nick, time.strftime('%y%m%d-%H%M%S'))

        if not path.exists(self.party_path):
            mkdir(self.party_path)
        elif path.exists(self.party_path) and not path.isdir(self.party_path):
            raise OSError("'party_dir' is not a directory")
        filepath = self.party_path+filename+'.txt'

        sup = '\n'.join(party)
        metadata = 'source: %s, via: %s\n\n' % (message.source, transvia)

        print(' -- Writing to %s...' % filepath)
        file = open(filepath, mode='w')
        file.write(metadata)
        file.write(sup)
        file.close()

        attempts = int((len(party)-1)/2)
        self.irc.privmsg(message.source, '%s | \x02%i\x02 attempts | %s/party/%s/%s/' % (party[-1], attempts, self.conf.conf['web_url'], self.conf.alias, filename), pretty=True)

    def partyvia(self, message, args):
        """ Specify a language code, must be both <a href="http://msdn.microsoft.com/en-us/library/dd877907.aspx">here</a> and <a href="http://msdn.microsoft.com/en-us/library/dd877886.aspx">here</a> """
        self.party(message, args)


    # web stuff follows
    def get_party(self, party_filename):
        party_file = open(self.party_path+'/'+party_filename)
        party = party_file.readlines()
        party_file.close()

        if party[0].startswith('source: '):
            metadata_string = party[0]
            party = party[2:]
            
        party_dict = {
                'lines': party,
                'nick': '-'.join(party_filename.split('-')[:-2]),
                'date': party_filename.split('-')[-2],
                'time': party_filename.split('-')[-1][:-4],
                'initial': party[0],
                'final': party[-1],
                'attempts': int((len(party)-1)/2),
                'url': party_filename[:-4]+'/',
                }

        for entry in metadata_string.split(','):
            key = entry.split(':')[0].strip()
            value = entry.split(':')[1].strip()
            party_dict[key] = value

        return party_dict

    def party_index(self):
        parties = []

        try:
            party_files = listdir(self.party_path)
        except IOError:
            raise HTTPError(code=404)

        for party_filename in party_files:
            party_dict = self.get_party(party_filename)
            if party_dict['source'].startswith('#'):
                parties.append(party_dict)

        parties.sort(key=lambda p:int(p['date']+p['time']), reverse=True)

        return template('party_index', parties=parties, network=self.conf.alias)

    def party_detail(self, filename):
        try:
            party = self.get_party(filename+'.txt')
        except IOError:
            raise HTTPError(code=404)

        return template('party', party=party, network=self.conf.alias)
