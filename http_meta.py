import re
import urllib.parse
import urllib.request
import urllib.parse
import urllib.error
import time
from http.server import BaseHTTPRequestHandler

import requests
import chardet
import html.entities
from hurry import filesize
from twitter import Twitter, OAuth

import plugin


defaults = {
    'http_url_blacklist': {
        # '#we-hate-imgur': ['imgur\.com'],
    },

    # whether to print mime-type and other metadata if <title> is unavailable
    'http_mime': True,

    'twitter_oath': {'token': '',
                     'token_secret': '',
                     'consumer_key': '',
                     'consumer_secret': ''}
}

# HTML MIME types.
HTML_TYPES = ('text/html', 'application/xhtml+xml')

# HTTP status codes appropriate for detecting normal redirection.
REDIRECT_CODES = (301, 302, 303)

# A structure required by hurry.filesize for custom suffixes.
FILESIZES = [
    (1024 ** 5, ' PiB'),
    (1024 ** 4, ' TiB'),
    (1024 ** 3, ' GiB'),
    (1024 ** 2, ' MiB'),
    (1024 ** 1, ' KiB'),
    (1024 ** 0, ' B'),
]

# Regex range that matches all Unicode characters except the C0 (U+0000-U+001F)
# and C1 (U+007F-U+009F) control characters and the space (U+0020)
ALL_CONTROLS_AND_SPACE = '[^\u0000-\u0020\u007f-\u009f]'

YOUTUBE_API_URL = 'http://www.youtube.com/get_video_info?video_id=%s'

FOURCHAN_API_URL = 'http://api.4chan.org/'
FOURCHAN_POST_API = FOURCHAN_API_URL + '%s/res/%s'


def ajax_url(url):
    """
    AJAX HTML snapshot URL parsing

    Take a URL string, turn its #! fragment into the prescribed query, and
    return a string.

    https://developers.google.com/webmasters/ajax-crawling/docs/specification
    """

    hashbang_index = url.find('#!')
    if hashbang_index != -1:
        base = url[:hashbang_index]
        joiner = '?' if '?' not in base else '&'
        url = ''.join((base, joiner, '_escaped_fragment_=',
                       urllib.parse.quote(url[hashbang_index+2:],
                                          '!"$\'()*,/:;<=>?@[\\]^`{|}~')))
    return url


def prettify_url(url):
    """
    Remove URL baggage to display a clean hostname/path.

    Returns a string when passed either a string or a urlparse.ParseResult.
    """

    if not isinstance(url, urllib.parse.ParseResult):
        url = urllib.parse.urlparse(url)
    urlstr = url.hostname + url.path
    return urlstr


class NoTitleError(Exception):
    """
    This page has no title :<
    """


# http://effbot.org/zone/re-sub.htm#unescape-html
def html_unescape(text):
    """
    Remove HTML or XML character references and entities from a text string.
    """

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return chr(int(text[3:-1], 16))
                else:
                    return chr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = chr(html.entities.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    return re.sub("&#?\w+;", fixup, text)


class Plugin(plugin.Plugin):
    """ Returns metadata about HTTP URLs. """
    http_frame = r'(?i).*https?://(www\.)?%s'

    def prepare(self):
        self.handlers = [
            (self.http_frame % 'twitter\.com/.*', self.twitter),
            (self.http_frame % 'youtube\.com/.*', self.youtube),
            (self.http_frame % 'youtu\.be/.*', self.youtube),
            (self.http_frame % '(boards\.)?4chan.com/.*', self.fourchan),
        ]

    def postfork(self):
        self.tw_api = Twitter(auth=OAuth(**self.conf['twitter_oath']))

    def register_commands(self):
        self.regexes = [
            (self.http_frame % ALL_CONTROLS_AND_SPACE, self.httpmeta)
        ]

    def url_list(self, message):
        urls = re.findall('(?i)https?://%s+'
                          % ALL_CONTROLS_AND_SPACE, message.content)

        try:
            blacklist = '(?i)'
            for b in self.conf['http_url_blacklist'][message.source]:
                blacklist += b + '|'
            blacklist = blacklist[0:-1]
            urls = [url for url in urls if not re.search(blacklist, url)]
        except KeyError:
            pass

        return urls

    def httpmeta(self, message, args):
        """
        $https://twitter.com/#!/camh/statuses/147449116551680001

        >Twitter / Cameron Kenley Hunt: There are only three hard  ...
        >\x03#|\x03 \x02twitter.com\x02
        """

        urls = self.url_list(message)

        for url in urls:
            for regex, handler in self.handlers:
                if re.match(regex, url):
                    our_handler = handler
                    break
            else:
                our_handler = self.title

            result = our_handler(url)

            if (our_handler != self.title) and (not result):
                result = self.title(url)

            self.send_struc(message.source, result)

    def twitter(self, url):
        match = re.search(r'(?<=status/)\d+(?=/|$)', url)

        if not match:
            return None

        tweet_id = match.group(0)

        tweet = self.tw_api.statuses.show(id=tweet_id)
        author = tweet['user']
        return ((tweet['text'], '\x02%s\x02 (%s)' % (author['name'],
                                                     author['screen_name'])))

    def youtube(self, url):
        match = re.search(r'\b[a-zA-Z0-9\-_]{11}\b', url)

        if not match:
            return None

        video_id = match.group(0)

        resource = requests.get(YOUTUBE_API_URL % video_id)
        video = urllib.parse.parse_qs(resource.text)

        if video['status'][0] == 'fail':
            return None

        total_seconds = int(video['length_seconds'][0])
        seconds = total_seconds % 60
        minutes = (total_seconds - seconds) / 60

        return (video['title'][0], '%i:%02i' % (minutes, seconds),
                '%s views' % video['view_count'][0])

    def fourchan(self, url):
        threadmatch = re.search(url, url)

    def title(self, url):
        url_parsed = urllib.parse.urlparse(url)
        url_hostname = url_parsed.hostname
        url = ajax_url(self.irc.strip_formatting(url))
        request_headers = {
            'User-Agent': ('Mozilla/5.0 (Windows; U; Windows NT 5.1; it; '
                           'rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11')}

        start_time = time.time()

        try:
            resource = requests.head(url, headers=request_headers,
                                     allow_redirects=True)

            if resource.status_code == 501:
                resource = requests.get(url, headers=request_headers,
                                        allow_redirects=True)

            if resource.status_code == 405:
                request_headers['Range'] = 'bytes=1-5'
                resource = requests.get(url, headers=request_headers,
                                        allow_redirects=True)
                del request_headers['Range']

            else:
                resource.raise_for_status()

            if resource.history != [] and (resource.history[-1].status_code
                                           in REDIRECT_CODES):
                url = resource.history[-1].headers['Location']
                redirection_url = urllib.parse.urlparse(url)
                if redirection_url.netloc == '':
                    url = ''.join((url_parsed.scheme, '://', url_parsed.netloc,
                                   redirection_url.path))
                elif redirection_url.hostname != url_hostname:
                    url_hostname = '%s \x03#->\x03 %s' % (url_hostname,
                                                          prettify_url(url))
                url = ajax_url(url)

            resource_type = resource.headers['Content-Type'].split(';')[0]
            if resource_type in HTML_TYPES:
                resource = requests.get(url, headers=request_headers)
                resource.raise_for_status()

                # RFC 2616 HTTP1.1__ discourages this, but then again it also
                # doesn't require the charset to be specified.

                # The requests library, in accordance with the RFC, falls back
                # to Latin-1 if charset is not in the Content-Type header.

                # This conditional at least ensures that the charset is
                # checked, even if the result is incorrect.
                # https://github.com/kennethreitz/requests/issues/592

                if resource.encoding == 'ISO-8859-1':
                    resource.encoding = chardet.detect(resource.content
                                                       )['encoding']
                try:
                    title = re.findall('(?si)(?<=<title).*?>.*?(?=</title>)',
                                       resource.text)[0]
                    title = re.sub('.*?>', '', title)
                except IndexError:
                    raise NoTitleError
                title = re.sub('(?s)\s+', ' ', html_unescape(title).strip())
            else:
                # TODO: Make this feature togglable, since it can seem spammy
                # for image dumps.
                raise NoTitleError

        except requests.exceptions.ConnectionError:
            title = 'server connection error'

        except requests.exceptions.HTTPError as httpe:
            title = '%s %s'.lower() % (
                httpe.response.status_code,
                BaseHTTPRequestHandler.responses[httpe.response.status_code][0]
            )

        except NoTitleError:
            if not self.conf.conf['http_mime']:
                # stop here
                return None

            try:
                data_length = filesize.size(float(
                    resource.headers['Content-Length']), FILESIZES)
            except TypeError:
                data_length = 'size unknown'
            title = '%s \x03#|\x03 %s' % (resource_type, data_length)

        end_time = time.time()

        time_length = '%.2f seconds' % (end_time - start_time)
        return ((title, time_length, '\x02%s\x02' % url_hostname))
