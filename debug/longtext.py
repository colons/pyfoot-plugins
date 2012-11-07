import plugin
from . import _rawsend
from . import _longtext

class Plugin(plugin.Plugin):
    def register_commands(self):
        self.commands = [
                ('longtext <to>', self.longtext),
                ]

    def longtext(self, message, args):
        """ <strong>DEBUG:</strong> Sends a long string of text in the character set <span class="irc"><span class="repl">to</span></span>. The text must be a string in _longtext.py decoded by Python's unicode() or string.decode() functions and the plugin will crash gracefully if <span class="irc"><span class="repl">to</span></span> cannot handle some or all of the characters. <span class="irc"><span class="repl">to</span></span> must be any of the standard encodings listed <a href="http://docs.python.org/library/codecs.html#standard-encodings">here</a>."""
        _rawsend.send(self.irc, message.source.encode(self.conf.conf['charset']), _longtext.string.encode(args['to']))
