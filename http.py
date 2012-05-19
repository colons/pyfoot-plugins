# -*- coding: utf-8 -*-
#import lxml.html
#import lxml.etree
import requests
import urlparse
import re
from random import choice
import urllib
from BaseHTTPServer import BaseHTTPRequestHandler
import chardet
import htmlentitydefs
from hurry import filesize

import time

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

class NoTitleError(Exception):
    def __init__(self):
        pass

""" Thanks to Fredrik Lundh: http://effbot.org/zone/re-sub.htm#unescape-html """
##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

filesizes = [
    (1024 ** 5, ' PiB'),
    (1024 ** 4, ' TiB'),
    (1024 ** 3, ' GiB'),
    (1024 ** 2, ' MiB'),
    (1024 ** 1, ' KiB'),
    (1024 ** 0, ' B'),
    ]

class Plugin(plugin.Plugin):
    def prepare(self):
        self.regex_str = '.*\\bhttps?://.?.*'
        self.regex = re.compile(self.regex_str)

    def register_commands(self):
        self.regexes = [
                (self.regex_str, self.title)
                ]

    def title(self, message, args):
        """ Returns the HTML title tag of URLs posted.
        $https://twitter.com/#!/camh/statuses/147449116551680001
        >Twitter / Cameron Kenley Hunt: There are only three hard  ... \x03#|\x03 \x02twitter.com\x02
        """

        for word in message.content.split():
            if self.regex.match(word):
                permitted = True
                start_time = time.time()

                for i in self.conf.conf['http_url_blacklist']:
                    channel, blacklist = i.split(' ')

                    if channel == message.source and re.match(blacklist, word):
                        permitted = False

                if permitted:
                    url_parsed = urlparse.urlparse(word)
                    url_hostname = url_parsed.hostname
                    word = self.irc.strip_formatting(ajax_url(word))
                    agent = choose_agent()
                    request_headers = {'User-Agent': agent}
                    request_headers_405 = {'User-Agent': agent, 'Range': 'bytes=1-5'}

                    try:
                        resource = requests.head(word, headers=request_headers, allow_redirects=True)
                        if resource.status_code == 405:
                            resource = requests.get(word, headers=request_headers_405, allow_redirects=True)
                        else:
                            resource.raise_for_status()

                        if resource.history != [] and resource.history[-1].status_code in redirect_codes:
                            word = resource.history[-1].headers['Location']
                            redirection_url = urlparse.urlparse(word)
                            if redirection_url.netloc == '':
                                word = ''.join([url_parsed.scheme,'://',url_hostname,redirection_url.path])
                            elif redirection_url.netloc != url_hostname:
                                url_hostname = '%s \x034->\x03 %s' % (url_hostname, prettify_url(word))
                            word = ajax_url(word)

                        resource_type = resource.headers['Content-Type'].split(';')[0]
                        if resource_type in html_types:
                            resource = requests.get(word, headers=request_headers)
                            resource.raise_for_status()
                            if resource.encoding == 'ISO-8859-1':
                                resource.encoding = chardet.detect(resource.content)['encoding']
                            """Seems that most pages claiming to be XHTML—including many large websites—
                            are not strict enough to parse correctly, usually for some very minor reason,
                            and it's a waste to attempt to parse it as XML first. This code will remain
                            for the day we can reliably parse XHTML as XML for the majority of sites."""
                            #if (html_types[1] in resource_type) or (('xhtml' or 'xml') in resource.text.split('>')[0].lower()):  # application/xhtml+xml
                            #    title = lxml.etree.fromstring(resource.text).find('.//xhtml:title', namespaces={'xhtml':'http://www.w3.org/1999/xhtml'}).text.strip()
                            #else:  # text/html

                            #title = lxml.html.fromstring(resource.text).find(".//title").text.replace('\n','').strip()
                            title = re.findall('(?i)(?<=<title>).*(?=</title>)', resource.text, re.DOTALL)[0]
                            if title == '':
                                raise NoTitleError
                            else:
                                title = unescape(title).replace('\n','').strip() + u' \x034|\x03 '
                        else:
                            """TODO: Make this feature togglable, since it can seem spammy for image dumps."""
                            raise NoTitleError
                    except requests.exceptions.ConnectionError:
                        title = 'Error connecting to server'
                    except requests.exceptions.HTTPError, httpe:
                        title = '%s %s' % (httpe.response.status_code, responses[httpe.response.status_code][0])
                    except NoTitleError:
                        title = ''
                    end_time = time.time()
                    time_length = 'Found in %s sec.' % round(end_time-start_time, 2)
                    try:
                        data_length = filesize.size(float(resource.headers['Content-Length']), filesizes)
                    except TypeError:
                        data_length = u'Unknown size'
                    summary = '%s%s \x034|\x03 %s \x034|\x03 %s \x034|\x03 \x02%s\x02' % (title, resource_type, data_length, time_length, url_hostname)
                    self.irc.privmsg(message.source, summary)
