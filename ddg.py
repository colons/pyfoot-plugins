import json
import urllib.request
import urllib.error
import urllib.parse

import plugin


class Plugin(plugin.Plugin):
    def prepare(self):
        self.url = (
            'http://api.duckduckgo.com/?q=%s&format=json&no_redirect=1&no_html'
            '=1&skip_disambig=1')
        self.frame = '\x02%s\x02\x03# :\x03 %s'

    def register_commands(self):
        self.commands = [
            ('ddg <<query>>', self.ddg)
        ]

    def query(self, query):
        response = urllib.request.urlopen(
            self.url % query).read().decode('utf-8')
        data = json.loads(response)
        return data

    def get_answer(self, query):
        data = self.query(query)
        print(data['Answer'])
        if data['Answer'].startswith("Safe search filtered your search to: "):
            return "sorry, duckduckgo can't deal with dirty words, the pussies"

        if data['Redirect']:
            return data['Redirect']

        if data['Answer']:
            return self.frame % (data['AnswerType'], data['Answer'])

        if data['AbstractText']:
            return self.frame % (data['AbstractText'], data['AbstractURL'])

        if data['Definition']:
            return self.frame % (
                '\x03#:\x03 '.join(data['Definition'].split(': ')[1:]),
                data['DefinitionURL'])

        if len(data['RelatedTopics']) == 1:
            return self.frame % (
                data['RelatedTopics'][0]['Text'],
                data['RelatedTopics'][0]['FirstURL'])

        if len(data['RelatedTopics']) > 1:
            return self.frame+'\x03# |\x03 %i other topics' % (
                data['RelatedTopics'][0]['Text'],
                data['RelatedTopics'][0]['FirstURL'],
                len(data['RelatedTopics']))

        return '\x02search\x02'

    def ddg(self, message, args):
        """
        Issue a [DuckDuckGo](http://duckduckgo.com/api.html) query.

        $<comchar>ddg 2^10

        >\x02calc\x02\x03# :\x03 2 ^ 10 = 1,024\x03# |\x03
        http://ddg.gg/?q=2%5E10
        """
        query = urllib.parse.quote(args['query'])

        answer = self.get_answer(query)

        if answer:
            self.irc.privmsg(message.source,
                             '%s\x03# |\x03 http://ddg.gg/?q=%s' % (answer,
                                                                    query))
