from time import sleep
import feedparser

import plugin

defaults = {
        'rss_feeds': {},
        'rss_interval': 150,
        }

class Plugin(plugin.Plugin):
    """<pyfoot> is capable of reading an RSS feed into a channel, but it's not configurable live. Talk to whoever is operating your local pyfoot instance if you have a feed you'd like in a channel."""
    def prepare(self):
        self.latestitem = {}

        for channel in self.conf.conf['rss_feeds']:
            # get latest item, remember to ignore it
            url = self.conf.conf['rss_feeds'][channel]

            try:
                feed = feedparser.parse(url)
                self.latestitem[url] = feed['items'][0]
            except:
                pass

    def run(self):
        while True:
            sleep(self.conf.conf['rss_interval'])

            for channel in self.conf.conf['rss_feeds']:
                url = self.conf.conf['rss_feeds'][channel]

                try:
                    feed = feedparser.parse(url)
                    item = feed['items'][0] 
                except:
                    pass
                else:
                    if item['link'] != self.latestitem[url]['link']:
                        self.latestitem[url] = feed['items'][0]
                        title = self.latestitem[url]['title']
                        link = self.latestitem[url]['link']
                    
                        self.irc.privmsg(channel, '%s | %s' % (title, link), pretty=True)
