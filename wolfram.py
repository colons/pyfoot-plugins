# -*- coding: utf-8 -*-

import plugin

from urllib import request
from urllib.parse import quote
from xml.etree.ElementTree import fromstring
import re


defaults = {
    'wolfram_app_id': None,
}


class Plugin(plugin.Plugin):
    url = 'http://api.wolframalpha.com/v2/query?input=%s&appid=%s'
    human_url = 'http://www.wolframalpha.com/input/?i=%s'

    def register_commands(self):
        self.commands = [
            ('wolfram <<query>>', self.wolfram)
        ]

    def wolfram(self, message, args):
        """
        Query the [Wolfram Alpha](http://www.wolframalpha.com/) API.
        """

        tree = self.query(args['query'])

        if tree.attrib['success'] == 'true':

            results = []

            for pod in tree.findall('pod'):
                if (pod.attrib.get('primary', None) == 'true'
                        or (pod.attrib.get('title', None) == 'Results')):
                    result = pod.find('subpod').find('plaintext').text
                    if result:
                        results.append([r.strip() for r in result.split(' | ')])

                elif pod.attrib['title'] == 'Input interpretation':
                    interp = pod.find('subpod').find('plaintext').text
                    results.append(['\x02%s\x02' % i
                                    for i in interp.split(' | ')])

            results.append(self.shorten_url(
                self.human_url % quote(args['query'])
            ))

            self.send_struc(message.source, results)

        elif tree.attrib['error'] == 'true':
            msg = tree.find('error').find('msg').text
            self.irc.privmsg(message.source, self.err % msg)

        else:
            for a, b in [('didyoumeans', 'didyoumean'), ('tips', 'tip')]:
                if tree.find(a):
                    elements = tree.find(a).findall(b)

                    if b == 'tip':
                        texts = [e.attrib['text'] for e in elements]
                    else:
                        texts = [e.text for e in elements]

                    self.send_struc(
                        message.source,
                        [
                            '\x02sorry about this\x02',
                            texts,
                            self.shorten_url(self.human_url % quote(args['query'])),
                        ])

                    return
            raise

    def query(self, query):
        url = self.url % (quote(query), self.conf.get('wolfram_app_id'))
        print(' -- %s' % url)
        response = request.urlopen(url).read().decode('utf-8')
        response = re.sub(r'\s+', ' ', response)
        tree = fromstring(response)

        return tree
