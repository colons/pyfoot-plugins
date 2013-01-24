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
                if pod.attrib.get('primary', None) == 'true':
                    result = pod.find('subpod').find('plaintext').text
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
            self.send_struc(
                message.source,
                [
                    '\x02did you mean\x02',

                    [d.text for d in
                     tree.find('didyoumeans').findall('didyoumean')],

                    self.shorten_url(self.human_url % quote(args['query'])),
                ])

    def query(self, query):
        url = self.url % (quote(query), self.conf.get('wolfram_app_id'))
        print(' -- %s' % url)
        response = request.urlopen(url).read().decode('utf-8')
        response = re.sub(r'\s+', ' ', response)
        tree = fromstring(response)

        return tree
