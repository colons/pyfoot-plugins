import urllib.request, urllib.error, urllib.parse
import json

import plugin

from pprint import pprint

def sorted_list_of_crime_types(hood):
    crime_types = [{
        'crime_type': t.replace('-', ' '),
        'stats': hood[t]
        } for t in hood.keys() if t != 'all-crime']

    worst_crime_types = sorted(crime_types, key=lambda t: t['stats']['crime_rate'], reverse=True)

    return worst_crime_types 


class Plugin(plugin.Plugin):
    """ CHEESE IT, IT'S THE ROZZERS """
    url = 'http://policeapi2.rkh.co.uk/api/%s'
    help_missing = 'no %s found for query \x02%s\x02'

    def register_commands(self):
        self.commands = [
                ('crime forces <query>', self.forces),
                ('crime neighbourhoods <force> <query>', self.neighbourhoods),
                ('crime summary <force> <neighbourhood>', self.hood_summary),
                ('crime compare <force_a> <neighbourhood_a> <force_b> <neighbourhood_b>', self.hood_compare),
            ]

    def neighbourhoods(self, message, args):
        """ List the neighbourhoods in a given force matching a string
        $<comchar>cri nei leicestershire br
        >\x02C05\x02 (Braunstone Park and Rowley Fields) \x03#:\x03 \x02L51\x02 (Thorpe Astley and Braunstone Town) \x03#:\x03 \x02L64\x02 (Broughton Astley and Walton)
        """ 

        query = args['query'].lower()

        hoods = self.query(args['force'], 'neighbourhoods')
        pprint(hoods)
        filtered_hoods = []
        for hood in hoods:
            if query in hood['name'].lower() or query in hood['id'].lower():
                filtered_hoods.append(hood)

        if not filtered_hoods:
            self.irc.privmsg(message.source, self.help_missing % ('neighbourhoods', query))
        else:
            self.irc.privmsg(message.source, ' \x03#:\x03 '.join(
                ['\x02%s\x02 (%s)' % (f['id'], f['name']) for f in filtered_hoods])
                )
            

    def forces(self, message, args):
        """
        Search for a force by a particular string.
        $<comchar>crime forces le
        >\x02cleveland\x02 (Cleveland Police) \x03#:\x03 \x02leicestershire\x02 (Leicestershire Police) \x03#:\x03 \x02north-wales\x02 (North Wales Police) \x03#:\x03 \x02south-wales\x02 (South Wales Police) \x03#:\x03 \x02thames-valley\x02 (Thames Valley Police)
        """
        forces = self.query('forces')
        query = args['query'].lower()

        filtered_forces = []

        for force in forces:
            if query in force['id'] or query in force['name'].lower():
                filtered_forces.append(force)

        if not filtered_forces:
            self.irc.privmsg(message.source, self.help_missing % ('forces', query))
        else:
            self.irc.privmsg(message.source, ' \x03#:\x03 '.join(
                ['\x02%s\x02 (%s)' % (f['id'], f['name']) for f in filtered_forces])
                )
    
    def hood_compare(self, message, args):
        """
        Compare two neighbourhoods.
        $<comchar>cr c leicestershire C04 city-of-london cs 
        """ 
        hood_a = {'force': args['force_a'], 'neighbourhood': args['neighbourhood_a']}
        hood_b = {'force': args['force_b'], 'neighbourhood': args['neighbourhood_b']}

        for hood in (hood_a, hood_b):
            hood_api = self.hood_summary(False, {'force': hood['force'], 'neighbourhood': hood['neighbourhood']})
            hood['worst'] = sorted_list_of_crime_types(hood_api)
            hood['api'] = hood_api
        
        strings = [
            '\x02%s\x02 vs. \x02%s\x02' % (
                hood_a['neighbourhood'], hood_b['neighbourhood']
                ),

            'crime rate \x03#:\x03 \x02%s\x02 (%s) vs. \x02%s\x02 (%s)' % (
                hood_a['api']['all-crime']['crime_rate'], hood_a['api']['all-crime']['crime_level'], 
                hood_b['api']['all-crime']['crime_rate'], hood_b['api']['all-crime']['crime_level'],
                ),

            'commonest crime \x03#:\x03 \x02%s\x02 (%s) vs. \x02%s\x02 (%s)' % (
                hood_a['worst'][0]['crime_type'], hood_a['worst'][0]['stats']['crime_rate'],
                hood_b['worst'][0]['crime_type'], hood_b['worst'][0]['stats']['crime_rate'],
                ),

            # oh god oh god
            'rarest crime \x03#:\x03 \x02%s\x02 (%s) vs. \x02%s\x02 (%s)' % (
                hood_a['worst'][-1]['crime_type'], hood_a['worst'][-1]['stats']['crime_rate'],
                hood_b['worst'][-1]['crime_type'], hood_b['worst'][-1]['stats']['crime_rate'],
                ),
            ]

        self.irc.privmsg(message.source, ' \x03#|\x03 '.join(strings))

    def hood_summary(self, message, args):
        """
        Summarise crime data in a given location.
        $<comchar>crime summary leicestershire L55
        >Crime rate: \x024.53\x02 (average) \x03#|\x03 burglary \x03#:\x03 \x020.87\x02 \x03#|\x03 anti social behaviour \x03#:\x03 \x020.72\x02 \x03#|\x03 vehicle crime \x03#:\x03 \x020.58\x02 \x03#|\x03 criminal damage arson \x03#:\x03 \x020.58\x02 \x03#|\x03 violent crime \x03#:\x03 \x020.43\x02
        """
        crimes = self.query(args['force'], args['neighbourhood'], 'crime')['crimes']
        #self.irc.privmsg(message.source, summary, pretty=True)
        date = list(crimes.keys())[0]

        hood = crimes[date]


        if message:
            worst_crime_types = sorted_list_of_crime_types(hood)
            self.irc.privmsg(message.source,
                'Crime rate: \x02%s\x02 (%s) \x03#|\x03 ' % (
                    hood['all-crime']['crime_rate'],
                    hood['all-crime']['crime_level'].replace('_', ' '),
                    ) + ' \x03#|\x03 '.join([
                        '%s \x03#:\x03 \x02%s\x02' % (
                            t['crime_type'],
                            t['stats']['crime_rate'],
                            ) for t in worst_crime_types[:5]
                        ])
                )
        else:
            return hood

    

    def query(self, *args):
        url = self.url % '/'.join(args)
        print(' -- '+url)
        raw_data = urllib.request.urlopen(url).read().decode('utf-8')
        data = json.loads(raw_data)
        return data
