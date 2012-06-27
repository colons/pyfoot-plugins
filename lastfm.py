import urllib.request, urllib.error, urllib.parse
import json
from random import choice
from math import fabs
from os import path
import pickle
import re

import plugin

defauts = {
        'lastfm_api_key': None
        }

class Plugin(plugin.Plugin):
    def register_commands(self):
        self.commands = [
                ('lastfm set <user>', self.define),
                ('np', self.now_playing_self),
                ('np <user>', self.now_playing),
            ]

    def prepare(self):
        self.url = 'http://ws.audioscrobbler.com/2.0/?%s'

        self.default_args = {
                'format': 'json',
                'api_key': self.conf.conf['lastfm_api_key']
                }

        self.user_file_path = path.expanduser(self.conf.conf['content_dir']+'lastfm')
        self.lastfmusers = {}
        self.help_missing = 'no such Last.fm user \x02%s\x02'

        self.np_string = '%s \x03#|\x03 http://www.last.fm/user/\x02%s\x02'
        
        try:
            userfile = open(self.user_file_path, 'rb')
            self.lastfmusers = pickle.load(userfile)
            userfile.close()
        except:
            print(' :: error reading MAL user pickle, will create one when necessary')
    
    def define(self, message, args):
        """ Let <pyfoot> know who you are.
        $<comchar>lastfm set nivijh
        >\x02nivi\x02 is now Last.fm user \x02NiviJh\x02\x03# |\x03 http://www.last.fm/user/\x02NiviJh\x02"""
        user = args['user']
        data = self.query({'method': 'user.getInfo', 'user': user})

        try:
            user = data['user']['name']
        except KeyError:
            self.irc.privmsg(message.source, self.explain_error(data, user=user))
            return

        else:
            try: # just in case other instances of pyfoot have altered the file since we last read it
                userfile = open(self.user_file_path, 'rb')
            except IOError:
                print(' :: error reading lastfm user pickle, creating one now')
                lastfmusers = {}
            else:
                lastfmusers = pickle.load(userfile)
                userfile.close()

            lastfmusers[self.conf.alias+' '+message.nick.lower()] = user 

            userfile = open(self.user_file_path, 'wb')
            pickle.dump(lastfmusers, userfile)
            userfile.close()
            self.irc.privmsg(message.source, '\x02%s\x02 is now Last.fm user \x02%s\x02 | http://last.fm/user/\x02%s\x02' % (message.nick, user, user), pretty=True)

    def now_playing_self(self, message, args):
        """ Spam the channel with your terrible taste in music.
        $<comchar>np
        >\x02富士山\x02 \x03#:\x03 電気グルーヴ \x03#|\x03 http://www.last.fm/user/\x02NiviJh\x02 """
        self.now_playing(message, args)
    
    def now_playing(self, message, args):
        """ Spam the channel with other people's terrible taste in music. """
        if 'user' in args:
            user = self.lastfmuser(args['user'])
        else:
            user = self.lastfmuser(message.nick)

        args = {
                'method': 'user.getRecentTracks',
                'limit': '1',
                'user': user,
                }
        
        all_data = self.query(args)
        try:
            data = all_data['recenttracks']
        except KeyError:
            self.irc.privmsg(message.source, self.explain_error(all_data, user=user))
            return

        try:
            track = data['track'][0]
        except KeyError:
            track = data['track']
            
        if '@attr' in track and 'nowplaying' in track['@attr'] and track['@attr']['nowplaying'] == 'true':
            np = True
        else:
            np = False

        if np:
            metadata = []
            metadata.append('\x02%s\x02' % track['name'])
            metadata.append(track['artist']['#text'])

            if track['album']['#text'] != '':
                metadata.append(track['album']['#text'])

            report = self.np_string % (' \x03#:\x03 '.join(metadata), data['@attr']['user'])
        else:
            report = self.np_string % ('not currently playing anything', data['@attr']['user'])

        self.irc.privmsg(message.source, report)

    def lastfmuser(self, user):
        """ Takes a user - irc or lastfm - and determines the appropriate MAL username """
        try:
            userfile = open(self.user_file_path, 'rb')
        except IOError:
            print(' :: no MAL user pickle found, ignoring')
            lastfmusers = {}
        else:
            lastfmusers = pickle.load(userfile)
            userfile.close()
            
        print(lastfmusers)

        try:
            lastfmuser = lastfmusers[self.conf.alias+' '+user.lower()]
        except KeyError:
            return user
        else:
            return lastfmuser

    def explain_error(self, data, user=None):
        if data['error'] == 6 and user:
            return(self.help_missing % user)
        else:
            return(data['message'].lower())

    def query(self, args):
        all_args = self.default_args
        all_args.update(args)

        argstring = '&'.join(['%s=%s' % (k, all_args[k]) for k in all_args])
        print(' -- '+self.url % argstring)
        raw_data = urllib.request.urlopen(self.url % argstring).read().decode('utf-8')
        data = json.loads(raw_data)
        return data
