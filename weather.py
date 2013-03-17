import plugin
import urllib.request
import urllib.error
import urllib.parse
from urllib.parse import quote
import json

defaults = {
    'wunderground_key': '',
    'forecasts_per_message': 3,
    'days_ahead': 6,
}


def f_to_c(f):
    return (f - 32) * (5./9.)


class Plugin(plugin.Plugin):
    def register_commands(self):
        self.commands = [('weather current <<location>>', self.current),
                         ('weather forecast <<location>>', self.forecast),
                         ('weather today <<location>>', self.today)]

    def prepare(self):
        self.url = (
            "http://api.wunderground.com/api/"
            + self.conf['wunderground_key'] + "/%s/q/%s.json")

        self.current_msg = (
            "\x02%s\x02 \x03#|\x03 %s\u00b0F \x03#:\x03 %s\u00b0C \x03#|\x03 "
            "humidity \x03#:\x03 %s \x03#|\x03 wind \x03#:\x03 %s at %s mph")

        self.suggestions_msg = "\x02matches\x02 \x03#|\x03 %s"

        self.conditions_str = (
            '\x02%s\x02 \x03#:\x03 %s%s \x03#:\x03 high %s\u00b0F %s\u00b0C '
            '\x03#:\x03 low %s\u00b0F %s\u00b0C \x03#:\x03 %s%% humid \x03#:'
            '\x03 %s at %s mph')

        # self.conditions_str = "%s \x03#:\x03 %s"

    def loc_string(self, location):
        """
        Creates a human-readable location string based on a wunderground
        results.
        """

        if 'full' in location:
            return location['full']

        return ', '.join([
            location[size] for size in ['name', 'state', 'country']
            if location[size] != ''])

    def suggest(self, data):
        results = data['response']['results']
        suggestions = [self.loc_string(r) for r in results]
        suggestions_str = ' \x03#|\x03 '.join(suggestions)
        msg = self.suggestions_msg % suggestions_str
        return msg

    def current(self, message, args):
        """
        Fetches the current weather in `<location>`.

        $<comchar>w c stafford, uk

        >\x02Stafford, Staffordshire\x02 \x03#|\x03 61\u00b0F \x03#:\x03
        16\u00b0C \x03#|\x03 humidity \x03#:\x03 68% \x03#|\x03 wind
        \x03#:\x03 W at 9 mph
        """

        url = self.url % ('conditions', quote(args["location"]))
        print(url)
        data = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))

        if 'results' in data['response']:
            msg = self.suggest(data)
        else:
            conditions = data['current_observation']

            city = self.loc_string(conditions['display_location'])

            tempf = conditions['temp_f']
            tempc = conditions['temp_c']
            humidity = conditions['relative_humidity']
            wind_mph = conditions['wind_mph']
            wind_dir = conditions['wind_dir'].lower()

            msg = self.current_msg % (
                city, tempf, tempc, humidity, wind_dir, wind_mph)

        self.irc.privmsg(message.source, msg)

    def forecast(self, message, args):
        """
        Fetches the weather forecast for `<location>`.

        $<comchar>w f nantwich and crewe

        >\x02Crewe, Cheshire East\x02 \x03#|\x03 \x02mon\x02 \x03#:\x03 high
        70\u00b0F 21\u00b0C \x03#:\x03 low 48\u00b0F 8\u00b0C \x03#:\x03 partly
        sunny \x03#|\x03 \x02tue\x02 \x03#:\x03 high 75\u00b0F 23\u00b0C
        \x03#:\x03 low 50\u00b0F 10\u00b0C \x03#:\x03 clear \x03#|\x03
        \x02wed\x02 \x03#:\x03 high 82\u00b0F 27\u00b0C \x03#:\x03 low
        59\u00b0F 15\u00b0C \x03#:\x03 partly sunny \x03#|\x03 \x02thu\x02
        \x03#:\x03 high 77\u00b0F 25\u00b0C \x03#:\x03 low 52\u00b0F 11\u00b0C
        \x03#:\x03 cloudy
        """

        url = self.url % ('forecast10day', quote(args["location"]))
        print(url)
        data = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))

        if 'results' in data['response']:
            msg = self.suggest(data)
            self.irc.privmsg(message.source, msg)

        else:
            forecast = data['forecast']['simpleforecast']['forecastday']
            summaries = []

            for day in forecast:
                precip_str = ''
                qpf_str = ' \x03#:\x03 %s" %s'
                qpf = day['qpf_allday']['in']
                snow = day['snow_allday']['in']

                if qpf > 0:
                    precip_str = qpf_str % (qpf, 'rain')

                if snow > 0:
                    precip_str = qpf_str % (snow, 'snow') + precip_str

                summaries.append(self.conditions_str % (
                    day['date']['weekday'].lower(),
                    day['conditions'].lower(),
                    precip_str,
                    day['high']['fahrenheit'],
                    day['high']['celsius'],
                    day['low']['fahrenheit'],
                    day['low']['celsius'],
                    day['avehumidity'],
                    day['avewind']['dir'].lower(),
                    day['avewind']['mph']
                ))

            if 'today' in args:
                summaries = summaries[:1]
            else:
                summaries = summaries[:self.conf['days_ahead']]

            while summaries:
                msg = ' \x03#|\x03 '.join(
                    summaries[0:self.conf['forecasts_per_message']])
                summaries = summaries[self.conf['forecasts_per_message']:]
                self.irc.privmsg(message.source, msg)

    def today(self, message, args):
        """ Like the above, but for one day only. """
        args['today'] = True
        self.forecast(message, args)
