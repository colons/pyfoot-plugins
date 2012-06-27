import plugin
import urllib.request, urllib.error, urllib.parse
from urllib.parse import urlencode
from xml.dom import minidom

def f_to_c(f):
    return (f - 32) * (5./9.)

class Plugin(plugin.Plugin):
    def register_commands(self):
        self.commands = [('weather current <<location>>', self.current),
                         ('weather forecast <<location>>', self.forecast),
                         ('weather today <<location>>', self.today)]

    def prepare(self):
        self.url = "http://www.google.com/ig/api?"

    def current(self, message, args):
        """ Fetches the current weather in <span class="irc"><span class="repl">location</span></span>.
        $<comchar>w c stafford, uk
        >\x02Stafford, Staffordshire\x02 \x03#|\x03 61\u00b0F \x03#:\x03 16\u00b0C \x03#|\x03 humidity \x03#:\x03 68% \x03#|\x03 wind \x03#:\x03 W at 9 mph
        """

        url = self.url + urlencode({"weather":args["location"]})
        data = urllib.request.urlopen(url)
        dom = minidom.parse(data)

        msg = "\x02%s\x02 \x03#|\x03 %s\u00b0F \x03#:\x03 %s\u00b0C \x03#|\x03 humidity \x03#:\x03 %s \x03#|\x03 wind \x03#:\x03 %s"

        city = dom.getElementsByTagName("city")[0].getAttribute("data")
        tempf = dom.getElementsByTagName("temp_f")[0].getAttribute("data")
        tempc = dom.getElementsByTagName("temp_c")[0].getAttribute("data")
        humidity = dom.getElementsByTagName("humidity")[0].getAttribute("data")[10:]
        wind = dom.getElementsByTagName("wind_condition")[0].getAttribute("data")[6:]

        msg = msg % (city, tempf, tempc, humidity, wind)
        self.irc.privmsg(message.source, msg)

    def forecast(self, message, args):
        """ Fetches the weather forecast for <span class="irc"><span class="repl">location</span></span>.
        $<comchar>w f nantwich and crewe
        >\x02Crewe, Cheshire East\x02 \x03#|\x03 \x02mon\x02 \x03#:\x03 high 70\u00b0F 21\u00b0C \x03#:\x03 low 48\u00b0F 8\u00b0C \x03#:\x03 partly sunny \x03#|\x03 \x02tue\x02 \x03#:\x03 high 75\u00b0F 23\u00b0C \x03#:\x03 low 50\u00b0F 10\u00b0C \x03#:\x03 clear \x03#|\x03 \x02wed\x02 \x03#:\x03 high 82\u00b0F 27\u00b0C \x03#:\x03 low 59\u00b0F 15\u00b0C \x03#:\x03 partly sunny \x03#|\x03 \x02thu\x02 \x03#:\x03 high 77\u00b0F 25\u00b0C \x03#:\x03 low 52\u00b0F 11\u00b0C \x03#:\x03 cloudy
        """

        url = self.url + urlencode({"weather": args["location"]})
        data = urllib.request.urlopen(url)
        dom = minidom.parse(data)

        msg = '\x02%s\x02' % dom.getElementsByTagName("city")[0].getAttribute("data")

        conditions = dom.getElementsByTagName("forecast_conditions")
        conditions_str = " \x03#|\x03 \x02%s\x02 \x03#:\x03 high %s\u00b0F %s\u00b0C \x03#:\x03 low %s\u00b0F %s\u00b0C \x03#:\x03 %s"

        for elements in conditions:
            day = elements.getElementsByTagName("day_of_week")[0].getAttribute("data")
            high_f = elements.getElementsByTagName("high")[0].getAttribute("data")
            high_c = '%i' % f_to_c(int(high_f))
            low_f = elements.getElementsByTagName("low")[0].getAttribute("data")
            low_c = '%i' % f_to_c(int(low_f))
            condition = elements.getElementsByTagName("condition")[0].getAttribute("data")
            msg += conditions_str % (day.lower(), high_f, high_c, low_f, low_c, condition.lower())

            if 'today' in args:
                break

        self.irc.privmsg(message.source, msg)

    def today(self, message, args):
        """ Like the above, but for one day only. """
        args['today'] = True
        self.forecast(message, args)
