# -*- coding: utf-8 -*-

import plugin
import urllib2
from urllib import urlencode
from xml.dom import minidom

class Plugin(plugin.Plugin):
    def register_commands(self):
        self.commands = [('weather current <<location>>', self.current),
                         ('weather forecast <<location>>', self.forecast)]
    def prepare(self):
        self.url = "http://www.google.com/ig/api?"
        
    def current(self, message, args):
        """ Fetches the current weather in <span class="irc"><span class="repl">location</span></span>.
        $<comchar>w c stafford, uk
        >\x02Stafford, Staffordshire\x02 \x03#|\x03 61°F \x03#:\x03 16°C \x03#|\x03 humidity \x03#:\x03 68% \x03#|\x03 wind \x03#:\x03 W at 9 mph"""
        
        url = self.url + urlencode({"weather":args["location"]})
        data = urllib2.urlopen(url)
        dom = minidom.parse(data)

        msg = u"\x02%s\x02 \x03#|\x03 %s°F \x03#:\x03 %s°C \x03#|\x03 humidity \x03#:\x03 %s \x03#|\x03 wind \x03#:\x03 %s"

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
        >\x02Crewe, Cheshire East\x02 \x03#|\x03 \x02Mon\x02 \x03#:\x03 high 70°F \x03#:\x03 low 48°F \x03#:\x03 Partly Sunny \x03#|\x03 \x02Tue\x02 \x03#:\x03 high 75°F \x03#:\x03 low 50°F \x03#:\x03 Clear \x03#|\x03 \x02Wed\x02 \x03#:\x03 high 82°F \x03#:\x03 low 59°F \x03#:\x03 Partly Sunny \x03#|\x03 \x02Thu\x02 \x03#:\x03 high 77°F \x03#:\x03 low 52°F \x03#:\x03 Cloudy
        """
        
        url = self.url + urlencode({"weather": args["location"]})
        data = urllib2.urlopen(url)
        dom = minidom.parse(data)

        msg = u'\x02%s\x02' % dom.getElementsByTagName("city")[0].getAttribute("data")

        conditions = dom.getElementsByTagName("forecast_conditions")
        conditions_str = u" \x03#|\x03 \x02%s\x02 \x03#:\x03 high %s°F \x03#:\x03 low %s°F \x03#:\x03 %s"

        for elements in conditions:
            day = elements.getElementsByTagName("day_of_week")[0].getAttribute("data")
            high_f = elements.getElementsByTagName("high")[0].getAttribute("data")
            low_f = elements.getElementsByTagName("low")[0].getAttribute("data")
            condition = elements.getElementsByTagName("condition")[0].getAttribute("data")
            msg += conditions_str % (day, high_f, low_f, condition)

        self.irc.privmsg(message.source, msg)
