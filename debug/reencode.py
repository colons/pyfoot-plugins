import module

class Module(module.Module):
    def register_commands(self):
        self.commands = [
                ('reencode <from> <to> <<phrase>>', self.reencode),
                ]

    def send(self, target, message):
        """ Raw version of self.irc.send """
        try:
            if 'c' in self.irc.channels[target]['modes']:
                message = self.irc.strip_formatting(message)
        except KeyError:
            pass

        message = self.irc.crop(message, 'PRIVMSG', target)
        message = 'PRIVMSG %s :%s\r\n' % (target, message)
        print ' >> %s' % message

        self.irc.socket.send(message)

    def reencode(self, message, args):
        """ <strong>DEBUG:</strong> Reencodes <span class="irc"><span class="repl">phrase</span></span> from character set <span class="irc"><span class="repl">from</span></span> to <span class="irc"><span class="repl">to</span></span>. <span class="irc"><span class="repl">from</span></span> and <span class="irc"><span class="repl">to</span></span> must be any of the standard encodings listed <a href="http://docs.python.org/library/codecs.html#standard-encodings">here</a>."""
        output = ' '.join(message.content_raw.split(' ')[3:]).decode(args['from']).encode(args['to'])
        self.send(message.source, output)
