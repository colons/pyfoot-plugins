import urllib.request
import urllib.error
import urllib.parse
import json
from random import choice
from math import fabs
from os import path
import re

import plugin


class Plugin(plugin.Plugin):
    """
    Fresh MyAnimeList facts, milled from [mal-api.com](http://mal-api.com).
    """

    shelf_required = True

    def register_commands(self):
        self.commands = [
            ('mal search <<query>>', self.search),
            ('mal set <user>', self.define),
            ('mal summarise <user>', self.summarise),
            ('mal', self.summarise_self),
            ('mal watching <user>', self.watching),
            ('mal watching', self.watching_self),
            ('mal fight <user1> <user2>', self.fight),
            ('mal fight <user>', self.fight_self),
            ('mal compare <user1> <user2>', self.compare),
            ('mal compare <user>', self.compare_self),
        ]

    def prepare(self):
        self.url = 'http://mal-api.com/%s?%s'
        self.default_args = ['format=json']
        self.user_file_path = path.expanduser(
            self.conf['content_dir']+'mal')
        self.help_setup = (
            "link a MyAnimeList account to your IRC nick with '" +
            self.conf['comchar']+"mal set <account name>'"
        )
        self.help_missing = 'no such MAL user \x02%s\x02'

    def define(self, message, args):
        """
        Many of these functions benefit from knowing whose IRC nicks correspond
        to which MAL user, so be sure to tell <pyfoot> who you are.

        $<comchar>mal set colons

        >\x02nivi\x02 is now MAL user \x02colons\x02\x03# |\x03
        http://myanimelist.net/profile/\x02colons
        """

        user = args['user']

        try:
            self.query('animelist/%s' % user)
        except urllib.error.HTTPError:
            self.irc.privmsg(message.source,
                             self.help_missing % user, pretty=True)
        else:
            self.shelf[message.nick.lower()] = user
            self.shelf.sync()
            self.irc.privmsg(
                message.source,
                '\x02%s\x02 is now MAL user \x02%s\x02 | '
                'http://myanimelist.net/profile/\x02%s' % (message.nick, user,
                                                           user),
                pretty=True)

    def maluser(self, user):
        """
        Takes a user - irc or mal - and returns the appropriate MAL username.
        """

        return self.shelf.get(user.lower(), user)

    def select(self, things, limit=5):
        if len(things) <= limit:
            selection = things
        else:
            selection = []

            while len(selection) < limit:
                thing = choice(things)
                if thing not in selection:
                    selection.append(thing)

        return selection

    def oiz(self, thing):
        """ Pipe user ratings and episode counts through this. """
        if thing == 0:
            return '-'
        else:
            return thing

    def summarise_self(self, message, args):
        args = {'user': message.nick}
        self.summarise(message, args)

    def summarise(self, message, args):
        """
        Summarise a particular user (or yourself).

        $<comchar>mal theshillito

        >http://myanimelist.net/animelist/\x02theshillito\x02\x03# |\x03
        \x0262.17\x02 days across \x02281\x02 keions\x03# |\x03 K-On!:
        Ura-On!\x03# :\x03 \x027\x02/\x027\x02\x03# :\x03 \x027\x02\x03# |\x03
        Ah! My Goddess\x03# :\x03 \x0224\x02/\x0224\x02\x03# :\x03
        \x0210\x02\x03# |\x03 Kamen no Maid Guy\x03# :\x03
        \x0212\x02/\x0212\x02\x03# :\x03 \x029\x02\x03# |\x03 Makai Senki
        Disgaea\x03# :\x03 \x0212\x02/\x0212\x02\x03# :\x03 \x027\x02\x03#
        |\x03 K-On!\x03# :\x03 \x0213\x02/\x0213\x02\x03# :\x03 \x029\x02
        """

        user = self.maluser(args['user'])

        try:
            data = self.query('animelist/%s' % user)
        except urllib.error.HTTPError:
            self.irc.privmsg(message.source,
                             self.help_missing % user,
                             pretty=True)
            return

        days = data['statistics']['days']
        animelist = data['anime']

        consumed = []
        planned = 0

        for a in animelist:
            if a['watched_status'] == 'plan to watch':
                planned += 1
            else:
                consumed.append(a)

        selection = self.select(consumed)

        if len(selection) == 0:
            showlist_string = ''
        else:
            showlist_string = ' | %s' % ' | '.join(
                ['%s : \x02%s\x02/\x02%s\x02 : \x02%s\x02' % (
                    a['title'],
                    self.oiz(a['watched_episodes']),
                 self.oiz(a['episodes']), self.oiz(a['score']))
                 for a in selection])

        summary = (
            'http://myanimelist.net/animelist/\x02%s\x02 | \x02%s\x02 days '
            'across \x02%d\x02 keions%s'
            % (user, days, len(consumed), showlist_string)
        )

        self.irc.privmsg(message.source, summary, pretty=True)

    def common_keions(self, users):
        """
        Get a list of tuples of keions that any two users have in common.
        """

        ud_list = []
        for user in users:
            try:
                data = self.query('animelist/%s' % user)
            except urllib.error.HTTPError:
                return self.help_missing % user
            ud_list.append(data)

        common = []

        for a1 in ud_list[0]['anime']:
            for a2 in ud_list[1]['anime']:
                if (
                    a1['id'] == a2['id']
                    and a1['watched_status'] != 'plan to watch'
                    and a2['watched_status'] != 'plan to watch'
                ):
                    common.append((a1, a2))

        return common

    def compare_self(self, message, args):
        """ Like a fight, but friendlier."""
        self.compare(message, {'user1': message.nick, 'user2': args['user']})

    def compare(self, message, args):
        users = [self.maluser(u) for u in [args['user1'], args['user2']]]
        common = self.common_keions(users)
        if type(common) == str:
            self.irc.privmsg(message.source, common, pretty=True)
            return

        consensus = []
        both_scored = 0

        for a1, a2 in common:
            if (a1['score'] == a2['score']) and a1['score'] != 0:
                consensus.append(a1)
            if a1['score'] != 0 and a2['score'] != 0:
                both_scored += 1

        if len(consensus) > 0:
            selection = self.select(consensus)
            self.irc.privmsg(
                message.source,
                '\x02%s\x02 and \x02%s\x02 | \x02%d\x02 common keions | '
                'agreement on \x02%d\x02/\x02%d\x02 mutually scored keions | '
                '%s' % (
                    users[0], users[1],
                    len(common), len(consensus),
                    both_scored,
                    ' | '.join(['%s : \x02%d\x02' % (a['title'], a['score'])
                                for a in selection])),
                pretty=True)
        else:
            # find the closest thing to common ground we have
            smallest_gap = 10
            closest = []

            for a1, a2 in common:
                if a1['score'] != 0 and a2['score'] != 0:
                    gap = fabs(a1['score'] - a2['score'])
                    if gap < smallest_gap:
                        smallest_gap = gap
                        closest = [(a1, a2)]
                    elif gap == smallest_gap:
                        closest.append((a1, a2))

            if len(closest) > 0:
                selection = self.select(closest)
                self.irc.privmsg(
                    message.source,
                    "\x02%s\x02 and \x02%s\x02 | \x02%d\x02 common keions | %s"
                    % (
                        users[0], users[1], len(common),
                        ' | '.join(['%s : \x02%d\x02, \x02%d\x02' % (
                            a[0]['title'], a[0]['score'],
                            a[1]['score'])
                        for a in selection])),
                    pretty=True)
            else:
                # we have no common ground :<
                selection = self.select(common)
                self.irc.privmsg(
                    message.source,
                    "\x02%s\x02 and \x02%s\x02 have \x02%d\x02 keions in "
                    "common | %s" % (
                        users[0], users[1],
                        len(common), ' | '.join([
                            a[0]['title'] for a in selection])),
                    pretty=True)

    def fight_self(self, message, args):
        """
        Fight someone.

        $<comchar>mal fight xinil

        >\x02colons\x02 vs. \x02xinil\x02\x03# |\x03 average contention\x03#
        :\x03 \x021.12\x02\x03# |\x03 Tengen Toppa Gurren Lagann\x03# :\x03
        \x024\x02 vs. \x028\x02

        If you specify an additional username, you don't have to get involved
        yourself.

        $<comchar>mal fight xinil theshillito

        >\x02xinil\x02 vs. \x02theshillito\x02\x03# | \x03average
        contention\x03# :\x03 \x022.10\x02\x03# |\x03 Cowboy Bebop\x03# :\x03
        \x0210\x02 vs. \x024\x02\x03# |\x03 Fate/stay night\x03# :\x03
        \x027\x02 vs. \x021\x02
        """

        self.fight(message, {
            'user1': message.nick,
            'user2': args['user']
        })

    def fight(self, message, args):
        users = [self.maluser(u) for u in [args['user1'], args['user2']]]
        common = self.common_keions(users)
        if type(common) == str:
            self.irc.privmsg(message.source, common, pretty=True)
            return

        largest_gap = 0
        contention = []
        total_gap = 0
        considered = 0

        for a1, a2 in common:
            if a1['score'] != 0 and a2['score'] != 0:
                gap = fabs(a1['score'] - a2['score'])
                total_gap += gap
                considered += 1
                if gap > largest_gap:
                    largest_gap = gap
                    contention = [(a1, a2)]
                elif gap == largest_gap:
                    contention.append((a1, a2))

        if considered > 0:
            average_gap = total_gap/float(considered)

        if len(contention) > 0:
            selection = self.select(contention)
            self.irc.privmsg(
                message.source,
                "\x02%s\x02 vs. \x02%s\x02 | average contention : \x02%.2f\x02"
                " | %s" % (
                    users[0], users[1],
                    average_gap,
                    ' | '. join([
                        '%s : \x02%d\x02 vs. \x02%d\x02' % (
                            a[0]['title'], a[0]['score'],
                            a[1]['score'])
                        for a in selection])),
                pretty=True)
        else:
            self.irc.privmsg(
                message.source,
                "\x02%s\x02 and \x02%s\x02 need to watch and score more stuff"
                % (users[0], users[1]),
                pretty=True)

    def search(self, message, args):
        """
        $<comchar>mal search churuya

        >\x02Nyoro-n Churuya-san\x02\x03# :\x03 ONA\x03# |\x03
        http://myanimelist.net/anime/5957\x03# |\x03 An anime adaptation of
        the 4-panel strip manga release: Nyoron Churuya-san. Based on Suzumiya
        Haruhi's energetic and 'always up to go' character, Tsuruya.
        """

        query = args['query']

        search = self.query('anime/search',
                            ['q=%s' % urllib.parse.quote(query)])

        try:
            keion = search[0]
        except IndexError:
            self.irc.privmsg(
                message.source,
                'no results | http://myanimelist.net/anime.php?q=%s'
                % urllib.parse.quote(query),
                pretty=True)
            return

        for show in search:
            if show['title'].lower() == args['query'].lower():
                keion = show

        keion_page = 'http://myanimelist.net/anime/%i' % show['id']

        # the html stripping should not be here, but it is for now because fuck
        # you
        self.irc.privmsg(
            message.source,
            '\x02%s\x02 : %s | %s | %s' % (
                keion['title'], keion['type'], keion_page,
                re.sub('<[^<]+?>', '', keion['synopsis'])),
            pretty=True, crop=True
        )

    def query(self, query, additional_args=[]):
        args = '&'.join(self.default_args+additional_args)
        print(' -- '+self.url % (query, args))
        raw_data = urllib.request.urlopen(self.url % (
            query, args)).read().decode('utf-8')
        data = json.loads(raw_data)
        return data

    def watching_self(self, message, args):
        self.watching(message, {
            'user': message.nick,
        })

    def watching(self, message, args):
        """
        Find out what a person (or yourself) is watching.
        """

        user = self.maluser(args['user'])

        try:
            data = self.query('animelist/%s' % user)
        except urllib.error.HTTPError:
            self.irc.privmsg(message.source,
                             self.help_missing % user,
                             pretty=True)
            return

        watching = [(a['title'],
                     '%s/%s' % (a['watched_episodes'],
                                self.oiz(a['episodes'])))
                    for a in data['anime']
                    if a['watched_status'] == 'watching']

        self.send_struc(message.source,
                        ['%i keions' % len(watching)] + self.select(watching))

    def correlate(self, id1, id2):
        print('hi')
