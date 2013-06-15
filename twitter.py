from twitter import Twitter, OAuth

import plugin

defaults = {
    'twitter_oath': {'token': '',
                     'token_secret': '',
                     'consumer_key': '',
                     'consumer_secret': ''}
}


class Plugin(plugin.Plugin):
    def postfork(self):
        self.tw_api = Twitter(auth=OAuth(**self.conf['twitter_oath']))

    def register_commands(self):
        self.commands = [
            ('twitter <screen_name>', self.user),
        ]

    def user(self, message, args):
        """
        Get the latest tweet from a user.
        """

        latest = self.tw_api.statuses.user_timeline(
            screen_name=args['screen_name'])[0]
        self.send_struc(message.source,
                        (latest['text'],
                         'http://twitter.com/%s/status/%s'
                         % (latest['user']['screen_name'],
                            latest['id_str']))
                        )
