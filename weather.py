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
        """ Fetches the current weather in <span class="irc"><span class="repl">location</span></span>. """
        
        url = self.url + urlencode({"weather":args["location"]})
        data = urllib2.urlopen(url)
        dom = minidom.parse(data)

        msg = u"Current weather for: %s [Temp: %sF/%sC | %s | %s]"
        city = dom.getElementsByTagName("city")[0].getAttribute("data")
        tempf = dom.getElementsByTagName("temp_f")[0].getAttribute("data")
        tempc = dom.getElementsByTagName("temp_c")[0].getAttribute("data")
        humidity = dom.getElementsByTagName("humidity")[0].getAttribute("data")
        wind = dom.getElementsByTagName("wind_condition")[0].getAttribute("data")

        msg = msg % (city, tempf, tempc, humidity, wind)
        self.irc.privmsg(message.source, msg)

    def forecast(self, message, args):
        """ Fetches the weather forecast in <span class="irc"><span class="repl">location</span></span>. """
        
        url = self.url + urlencode({"weather": args["location"]})
        data = urllib2.urlopen(url)
        dom = minidom.parse(data)

        msg = u"Forecast for: "
        msg += dom.getElementsByTagName("city")[0].getAttribute("data")

        conditions = dom.getElementsByTagName("forecast_conditions")
        conditions_str = "[%s- High: %sF | Low: %sF | Outlook: %s]"
        for elements in conditions:
            day = elements.getElementsByTagName("day_of_week")[0].getAttribute("data")
            high = elements.getElementsByTagName("high")[0].getAttribute("data")
            low = elements.getElementsByTagName("low")[0].getAttribute("data")
            condition = elements.getElementsByTagName("condition")[0].getAttribute("data")
            msg += conditions_str % (day, high, low, condition)
        self.irc.privmsg(message.source, msg)
