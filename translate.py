import urllib.request
import urllib.parse
import urllib.error

import plugin


class Translator(object):
    def __init__(self, bing_app_id):
        self.bing_app_id = bing_app_id

    def translate(self, source, target, phrase):
        """
        Translates phrase from source to target with Bing's translation API.
        """

        query = urllib.parse.quote(phrase.replace('"', '').replace('\\', ''))

        page = urllib.request.urlopen(
            'http://api.microsofttranslator.com/V2/Ajax.svc/'
            'Translate?appId=%s&from=%s&to=%s&text="%s"' % (self.bing_app_id,
                                                            source, target,
                                                            query))

        result = page.read().decode('utf-8')

        result = result.replace('"', '').replace('\\', '')

        if 'ArgumentOutOfRangeException:' in result:
            raise NameError("that's not a language, silly")

        print(' -- %s' % result)

        return result


class Plugin(plugin.Plugin):
    def prepare(self):
        self.translator = Translator(self.conf.conf['bing_app_id'])

    def register_commands(self):
        self.commands = [
            ('translate <from> <to> <<phrase>>', self.translate),
        ]

    def translate(self, message, args):
        """
        Translates `<phrase>` from `<from>` to `<to>` using the Bing translate
        API. `<from>` and `<to>` must be any of the language codes listed
        [here](http://msdn.microsoft.com/en-us/library/hh456380.aspx).

        $<comchar>translate fr en le jambon est mort

        >the ham is dead
        """

        translation = self.translator.translate(args['from'], args['to'],
                                                args['phrase'])
        self.irc.privmsg(message.source, translation)
