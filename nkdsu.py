from time import sleep
import json
from urllib import request

import plugin

defaults = {
    'nkdsu_np_channels': [],
    'nkdsu_interval': 20,
}


class Plugin(plugin.Plugin):
    """
    A plugin that keeps channels updated with the currently playing track on
    [Neko Desu](http://thisisthecat.com/index.php/neko-desu) according to the
    [nkd.su API](http://nkd.su/help/api).
    """

    url = 'http://nkd.su/api/'
    np_str = 'now playing\x03# |\x03 \x02%s\x02\x03# :\x03 %s\x03# :\x03 %s\x03# |\x03 %s'
    unroled_np_str = 'now playing\x03# |\x03 \x02%s\x02\x03# :\x03 %s\x03# |\x03 %s'

    def prepare(self):
        np = self.now_playing()
        if np:
            self.latest_play = np['id']
        else:
            self.latest_play = None

    def now_playing(self):
        week = self.get_week()
        if week['playlist']:
            return week['playlist'][-1]['track']
        else:
            return None

    def get_week(self):
        bytes = request.urlopen(self.url).read()
        serial = bytes.decode('utf-8')
        return json.loads(serial)

    def notify_our_channels(self, np):
        if np['role']:
            np_str = self.np_str % (
                np['title'], np['role'], np['artist'], self.shorten_url(np['url']))
        else:
            np_str = self.unroled_np_str % (
                np['title'], np['artist'], self.shorten_url(np['url']))

        for channel in self.conf['nkdsu_np_channels']:
            self.irc.privmsg(channel, np_str)

    def run(self):
        while True:
            sleep(self.conf['nkdsu_interval'])
            np = self.now_playing()

            if np and np['id'] != self.latest_play:
                self.notify_our_channels(np)
                self.latest_play = np['id']
            elif (not np) and (self.latest_play is not None):
                self.latest_play = None
