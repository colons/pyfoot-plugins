import json
import urllib2

import module

class Module(module.Module):
    def prepare(self):
        self.url = 'http://api.duckduckgo.com/?q=%s&format=json&no_redirect=1&no_html=1&skip_disambig=1'
        self.frame = '\x02%s\x02\x03# :\x03 %s'

    def register_commands(self):
        self.commands = [
                ('ddg <<query>>', self.ddg)
                ]

    def query(self, query):
        # response = urllib2.urlopen(self.url % query, None, {'User-Agent': 'pyfoot/hg bitbucket.org/colons/pyfoot/'})
        response = urllib2.urlopen(self.url % query)
        data = json.load(response)
        return data
    
    def get_answer(self, query):
        data = self.query(query)
        print data['Answer']
        if data['Answer'] == "Safe search filtered your search to: <b>off</b>. Use !safeoff command to turn off temporarily.":
            return "sorry, duckduckgo can't deal with dirty words, the pussies"

        if data['Redirect']:
            return data['Redirect']
        
        if data['Answer']:
            return self.frame % (data['AnswerType'], data['Answer'])

        if data['AbstractText']:
            return self.frame % (data['AbstractText'], data['AbstractURL'])

        if data['Definition']:
            return self.frame % ('\x03#:\x03 '.join(data['Definition'].split(': ')[1:]), data['DefinitionURL'])

        if len(data['RelatedTopics']) == 1:
            return self.frame % (data['RelatedTopics'][0]['Text'], data['RelatedTopics'][0]['FirstURL'])
        
        if len(data['RelatedTopics']) > 1:
            return self.frame+'\x03# |\x03 %i other topics' % (data['RelatedTopics'][0]['Text'], data['RelatedTopics'][0]['FirstURL'], len(data['RelatedTopics']))

        return '\x02search\x02'

    def ddg(self, message, args):
        """ Issue a <a href="http://duckduckgo.com/api.html">DuckDuckGo</a> query.
        $<comchar>ddg 2^10
        >\x02calc\x02\x03# :\x03 2 ^ 10 = 1,024\x03# |\x03 http://ddg.gg/?q=2%5E10 """
        query = urllib2.quote(args['query'])

        answer = self.get_answer(query)

        if answer:
            self.irc.privmsg(message.source, '%s\x03# |\x03 http://ddg.gg/?q=%s' % (answer, query))
