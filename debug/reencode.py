import plugin
from . import _rawsend

class Plugin(plugin.Plugin):
    def register_commands(self):
        self.commands = [
                ('reencode <from> <to> <<phrase>>', self.reencode),
                ]

    def reencode(self, message, args):
        """ <strong>DEBUG:</strong> Reencodes <span class="irc"><span class="repl">phrase</span></span> from character set <span class="irc"><span class="repl">from</span></span> to <span class="irc"><span class="repl">to</span></span>. <span class="irc"><span class="repl">from</span></span> and <span class="irc"><span class="repl">to</span></span> must be any of the standard encodings listed <a href="http://docs.python.org/library/codecs.html#standard-encodings">here</a>."""
        output = ' '.join(message.content_raw.split(' ')[3:]).decode(args['from']).encode(args['to'])
        _rawsend.send(self.irc, message.source, output)
