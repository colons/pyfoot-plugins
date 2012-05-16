# -*- coding: utf-8 -*-
import lxml.html
#import lxml.etree
import requests
from urlparse import urlparse
import re

from random import choice
import urllib
from BaseHTTPServer import BaseHTTPRequestHandler
import plugin

defaults = {
        'http_url_blacklist': [],
        }

user_agents = [
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
    'Opera/9.25 (Windows NT 5.1; U; en)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
    'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9'
]
html_types = ['text/html','application/xhtml+xml']
redirect_codes = [301,302,303]

responses = BaseHTTPRequestHandler.responses

def choose_agent():
    return choice(user_agents)

def ajax_url(url):
    """ AJAX HTML snapshot URL parsing, pretty much required for a modern scraper. """
    """ https://developers.google.com/webmasters/ajax-crawling/docs/specification """
    hashbang_index = url.find('#!')
    if hashbang_index != -1:
        base = url[:hashbang_index]
        joiner = '?' if '?' not in base else '&'
        url = ''.join([base,joiner,'_escaped_fragment_=',urllib.quote(url[hashbang_index+2:], '=')])
    return url

def prettify_url(url):
    """ Removes URL baggage to display a clean hostname/path. """
    """ Can be passed a string or a urlparse.ParseResult object. """
    if isinstance(url, urlparse.ParseResult) == False:
        url = urlparse.urlparse(url)
    return url.hostname + re.sub('/$', '', url.path)


class Plugin(plugin.Plugin):
    def register_commands(self):
        self.regexes = [
                ('.*\\bhttps?://.*', self.title)
                ]

    def title(self, message, args):
        """ Returns the HTML title tag of URLs posted.
        $https://twitter.com/#!/camh/statuses/147449116551680001
        >Twitter / Cameron Kenley Hunt: There are only three hard  ... \x03#|\x03 \x02twitter.com\x02
        """

        for word in message.content.split():
            if word.startswith('http://') or word.startswith('https://'):
                permitted = True

                for i in self.conf.conf['http_url_blacklist']:
                    channel, blacklist = i.split(' ')

                    if channel == message.source and re.match(blacklist, word):
                        permitted = False

                if permitted:
                    url_parsed = urlparse(word)
                    url_hostname = url_parsed.hostname
                    word = self.irc.strip_formatting(ajax_url(word))
                    request_headers = {'User-Agent': choose_agent()}

                    try:
                        resource = requests.head(word, headers=request_headers, allow_redirects=True)
                        resource.raise_for_status()

                        if resource.history != [] and resource.history[-1].status_code in redirect_codes:
                            word = resource.history[-1].headers['Location']
                            redirection_url = urlparse(word)
                            if redirection_url.netloc == '':
                                word = ''.join([url_parsed.scheme,'://',url_hostname,redirection_url.path])
                            elif redirection_url.netloc != url_hostname:
                                url_hostname = '%s \x034->\x03 %s' % (url_hostname, prettify_url(word))
                            word = ajax_url(word)

                        resource_type = resource.headers['Content-Type'].split(';')[0]
                        if resource_type in html_types:
                            resource = requests.get(word, headers=request_headers)
                            resource.raise_for_status()
                            """Seems that most pages claiming to be XHTML—including many large websites—
                            are not strict enough to parse correctly, usually for some very minor reason,
                            and it's a waste to attempt to parse it as XML first. This code will remain
                            for the day we can reliably parse XHTML as XML for the majority of sites."""
                            #if (html_types[1] in resource_type) or (('xhtml' or 'xml') in resource.text.split('>')[0].lower()):  # application/xhtml+xml
                            #    title = lxml.etree.fromstring(resource.text).find('.//xhtml:title', namespaces={'xhtml':'http://www.w3.org/1999/xhtml'}).text.strip()
                            #else:  # text/html

                            title = lxml.html.fromstring(resource.text).find(".//title").text.replace('\n','').strip()
                        else:
                            """TODO: Make this feature togglable, since it can seem spammy for image dumps."""
                            title = 'Type: %s, Size: %s bytes' % (resource_type, resource.headers['Content-Length'])
                    except requests.exceptions.ConnectionError:
                        title = 'Error connecting to server'
                    except requests.exceptions.HTTPError, httpe:
                        title = '%s %s' % (httpe.response.status_code, responses[httpe.response.status_code][0])
                    summary = '%s \x034|\x03 \x02%s\x02' % (title, url_hostname)
                    self.irc.privmsg(message.source, summary)
