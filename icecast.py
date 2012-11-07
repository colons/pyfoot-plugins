import plugin
import lxml

defaults = {
        'icecast_address': '',
        'icecast_mountpoint': '',
        }


class Plugin(plugin.Plugin):
    """ An Icecast scraper. """

    def register_commands(self):
        commands = [
                ('whatson', self.whatson),
                ('wo', self.whatson)
                ]

        self.commands = commands + [
                ('mountpoints', self.list_mountpoints),
                ]
        for c,f in commands:
            self.commands.append((c + ' <mountpoint>', f))


    def whatson(self, message, args):
        print(repr(args))
        if 'mountpoint' in args:
            print('1')
            mountpoint = args['mountpoint']
        elif self.conf.conf['icecast_mountpoint'] != '':
            print('2')
            mountpoint = self.conf.conf['icecast_mountpoint']
        else:
            print('3')
            raise KeyError('No mountpoint specified!')

    def list_mountpoints(self, message, args):
        pass
