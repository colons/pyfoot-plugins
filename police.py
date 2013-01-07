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

def geocode(query):
    url = 'http://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false' % urllib.parse.quote(query)
    print(' -- '+url)
    raw_data = urllib.request.urlopen(url).read().decode('utf-8')
    data = json.loads(raw_data)
    return data


class Plugin(plugin.Plugin):
    """ CHEESE IT, IT'S THE <a href="http://police.uk/">ROZZERS</a> """
    url = 'http://policeapi2.rkh.co.uk/api/%s'
    help_missing = 'no %s found for query \x02%s\x02'

    def register_commands(self):
        self.commands = [
                ('crime summary <<location>>', self.hood_summary),
                ('crime compare <<location_a>> vs. <<location_b>>', self.hood_compare),
            ]


    def attempt_to_get_one_location(self, message, query):
        data = geocode(query)
        results = data['results']

        if len(results) == 1:
            return (results[0]['formatted_address'],
                    results[0]['geometry']['location'])

        elif len(results) == 0:
            self.irc.privmsg(message.source, self.help_missing % ('location', query))
            return None

        elif len(results) > 1:
            self.irc.privmsg(
                    message.source,
                    '\x02did you mean\x02 \x03#|\x03 ' + ' \x03#:\x03 '.join([r['formatted_address'] for r in results])
                    )
            return None

    def attempt_to_get_neighbourhood(self, message, latlng, name):
        try:
            data = self.query('locate-neighbourhood?q=%s,%s' % (latlng['lat'], latlng['lng']))
        except urllib.error.HTTPError:
            self.irc.privmsg(message.source, 'no police found for \x02%s\x02' % name)
            return None
    
        return data
    
    def hood(self, geocoded):
        crimes = self.query(geocoded['force'], geocoded['neighbourhood'], 'crime')['crimes']
        date = list(crimes.keys())[0]
        hood = crimes[date]
        return hood

    def hood_summary(self, message, args):
        """
        Summarise crime data in a given location.
        $<comchar>crime s leicester
        >\x02Leicester, UK\x02 \x03#|\x03 crime rate: \x024.53\x02 (average) \x03#|\x03 burglary \x03#:\x03 \x020.87\x02 \x03#|\x03 anti social behaviour \x03#:\x03 \x020.72\x02 \x03#|\x03 vehicle crime \x03#:\x03 \x020.58\x02 \x03#|\x03 criminal damage arson \x03#:\x03 \x020.58\x02 \x03#|\x03 violent crime \x03#:\x03 \x020.43\x02
        """
        
        location = self.attempt_to_get_one_location(message, args['location'])

        if location:
            name, latlng = location
            print(name)
            print(latlng)
        else:
            # we didn't get a fix, abandon hope
            return

        hood_response = self.attempt_to_get_neighbourhood(message, latlng, name)

        if not hood_response:
            return

        hood = self.hood(hood_response)

        if message:
            worst_crime_types = sorted_list_of_crime_types(hood)
            self.irc.privmsg(message.source,
                '\x02%s\x02 \x03#|\x03 crime rate: \x02%s\x02 (%s) \x03#|\x03 ' % (
                    name,
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

    
    def hood_compare(self, message, args):
        """
        Compare two neighbourhoods.
        $<comchar>cr leicester vs london 
        >\x02Leicester, UK\x02 vs. \x02London, UK\x02 \x03#|\x03 crime rate \x03#:\x03 \x0217.61\x02 (above average) vs. \x02207.71\x02 (high) \x03#|\x03 commonest crime \x03#:\x03 \x02anti social behaviour\x02 (3.54) vs. \x02other theft\x02 (92.56) \x03#|\x03 rarest crime \x03#:\x03 \x02robbery\x02 (0.00) vs. \x02vehicle crime\x02 (1.33)
        """ 
        hood_a = {'query': args['location_a']}
        hood_b = {'query': args['location_b']}

        for hood in (hood_a, hood_b):
            location = self.attempt_to_get_one_location(message, hood['query'])

            if location:
                name, latlng = location
            else:
                return

            hood_response = self.attempt_to_get_neighbourhood(message, latlng, name)

            if not hood_response:
                return

            hood_api = self.hood({
                'force': hood_response['force'],
                'neighbourhood': hood_response['neighbourhood']
                })
            hood['worst'] = sorted_list_of_crime_types(hood_api)
            hood['api'] = hood_api
            hood['name'] = name 
        
        strings = [
            '\x02%s\x02 vs. \x02%s\x02' % (
                hood_a['name'], hood_b['name']
                ),

            'crime rate \x03#:\x03 \x02%s\x02 (%s) vs. \x02%s\x02 (%s)' % (
                hood_a['api']['all-crime']['crime_rate'], hood_a['api']['all-crime']['crime_level'].replace('_', ' '), 
                hood_b['api']['all-crime']['crime_rate'], hood_b['api']['all-crime']['crime_level'].replace('_', ' '),
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


    def query(self, *args):
        url = self.url % '/'.join(args)
        print(' -- '+url)
        raw_data = urllib.request.urlopen(url).read().decode('utf-8')
        data = json.loads(raw_data)
        return data
