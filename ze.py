import urllib2
import module
from random import choice
import re

class Module(module.Module):
    def register_commands(self):
        self.commands = [
                ('ze', self.ze),
                ]

    def prepare(self):
        self.url = 'http://srcommunity.org/w/index.php?action=raw&title=%s'

    def get_wikitext(self, title):
        wikitext = urllib2.urlopen(self.url % (title)).read()
        return wikitext

    def reformat(self, line):
        line = line.strip()
        line = re.sub("<.*?>| *\(.*?\)|''|\[[^\]]+?\||[\[\]]+", '', line)

        line = line.lstrip(' :').strip()

        return line

    def get_quote(self):
        ep_index = self.get_wikitext('A_Show_Episode_Guide')
        eps = ep_index.split('== ... Episodes ..::.. Transcripts ==')[1].split('\n==')[0].split('\n')
        eps = [e.split('[[')[-1].split('|')[0].replace(' ', '_') for e in eps if len(e) > 0 and e.startswith('# [')]
        eps = [e for e in eps if e.startswith('A_show:_')]

        ep = choice(eps)

        transcript = self.get_wikitext(ep)

        epno = int(transcript.split('http://ashow.zefrank.com/episodes/')[1].split(' ')[0])
        source = 'http://ashow.zefrank.com/episodes/%i' % epno

        transcript = transcript.split('\n(Credits:')[0]
        transcript = transcript.split('\n(Links from sidebar:')[0]
        try:
            transcript = transcript.split('|next]]')[1]
        except IndexError:
            transcript = transcript.split(' | next\n')[1]

        lines = transcript.split('\n')
        lines = [self.reformat(l) for l in lines]
        lines = [l for l in lines if len(l) > 0 and not l.startswith(('#', '(', '|', '{', '}'))]

        line = choice(lines)

        return (line, source)

    def ze(self, message, args):
        """ Returns a random quote from the <a href="http://srcommunity.org/wiki/A_Show_Episode_Guide">a show transcriptions</a>. """
        quote, source = self.get_quote()
        self.irc.privmsg(message.source, quote+'\x03# |\x03 '+source)
