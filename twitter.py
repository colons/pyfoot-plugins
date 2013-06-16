from twitter import Twitter, OAuth

import plugin

defaults = {
    'twitter_oath': {'token': '',
                     'token_secret': '',
                     'consumer_key': '',
                     'consumer_secret': ''}
}


class Plugin(plugin.Plugin):
    shelf_required = True

    def postfork(self):
        self.tw_api = Twitter(auth=OAuth(**self.conf['twitter_oath']))

    def register_commands(self):
        self.commands = [
            ('twitter <<query>>', self.query),
            ('twitter set <screen_name>', self.set_user),
            ('twitter', self.self),
        ]

    def query(self, message, args):
        """
        Get the latest tweet from a user or search with either a hashtag or a
        multi-word search string.
        """

        query = args['query']

        if query.startswith('#') or ' ' in query:
            tweet = self.tw_api.search.tweets(q=query)['statuses'][0]

        else:
            screen_name = self.shelf.get(query.lower(), query.lower())

            tweet = self.tw_api.statuses.user_timeline(
                screen_name=screen_name)[0]

        self.send_tweet(message, tweet)

    def send_tweet(self, message, tweet):
        self.send_struc(message.source,
                        (tweet['text'],
                         'http://twitter.com/%s/status/%s'
                         % (tweet['user']['screen_name'],
                            tweet['id_str']))
                        )

    def set_user(self, message, args):
        """
        Tell <pyfoot> who you are.
        """

        name = args['screen_name']
        self.tw_api.users.show(screen_name=name)  # will error if not a user
        self.shelf[message.nick.lower()] = name
        self.shelf.sync()
        self.send_struc(message.source,
                        ('\x02%s\x02 is now Twitter user \x02%s\x02'
                         % (message.nick, name),
                         'http://twitter.com/%s' % name))

    def self(self, message, args):
        """
        Get your latest tweet.
        """

        self.query(message, {'query': message.nick})
