import BeautifulSoup
import urllib
from urlparse import urlparse
import string
import re
from random import choice

import module

class Module(module.Module):
    def prepare(self):
        self.user_agents = [
                'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
                'Opera/9.25 (Windows NT 5.1; U; en)',
                'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
                'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
                'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
                'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9'
            ]

    def register_commands(self):
        self.regexes = [
                ('.*\\bhttps?://.*', self.title)
                ]

    def title(self, message, args):
        """ Returns the HTML title tag of URLs posted.
        $https://twitter.com/#!/camh/statuses/147449116551680001
        >Twitter / Cameron Kenley Hunt: There are only three hard  ...\x03# |\x03 \x02twitter.com\x02
        """
        for word in message.content.split():
            if word.startswith('http://') or word.startswith('https://'):
                permitted = True

                for i in self.conf.get('url_blacklist'):
                    channel, blacklist = i.split(' ')

                    if channel == message.source and re.match(blacklist, word):
                        permitted = False

                if permitted:

                    '''AJAX HTML Snapshot URL parsing'''
                    hashbang_index = word.find('#!')
                    if hashbang_index != -1:
                        url_base = word[:hashbang_index]
                        if '?' in url_base:
                            join = '&'
                        else:
                            join = '?'
                        url_fragment = urllib.quote(word[hashbang_index+2:], '=')
                        word = url_base + join + '_escaped_fragment_=' + url_fragment

                    parsed_url = urlparse(word)

                    opener = urllib.FancyURLopener()
                    setattr(opener, 'version', choice(self.user_agents))

                    pagesoup = BeautifulSoup.BeautifulSoup(opener.open(word))
                    title = BeautifulSoup.BeautifulStoneSoup((pagesoup.title.string).replace('\n', '').strip(), convertEntities="html").contents[0]
                    summary = '%s\x03# |\x03\x02 %s\x02' % (title, parsed_url.hostname)
                    self.irc.privmsg(message.source, summary)
