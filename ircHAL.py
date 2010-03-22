__author__    = "Lorenzo Giuliani (lor@frenzart.com)"
__version__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2009 Lorenzo Giuliani"
__license__   = "GPL"

from halpy.hal import HAL
from IRCClient import *
import os, sys, locale
import yaml

import re


class ircHAL(LogAllMixin, IRCClient):

    def __init__(self, server, port, nick, channel, hal):
        """docstring for __init__"""
        self.botname = nick
        self.channel = channel
        IRCClient.__init__(self, server, port)
        self.connect(nick, "non sono un bot :(")
        self.join(channel)

        self.H = hal

    def handle_say(self, source, to, message):
        nick = getnick(source)

        if re.match('!list', message.lower()):
            self.say(self.channel, 'Lista file marrany:')
            self.say(self.channel, '  1. Meila ')
            self.say(self.channel, '  2. MorboOS (l\'os di gurumanno) ')
            self.say(self.channel, '  3. area portuale di Livorno ')
            self.say(self.channel, '  4. una vera finta pietra dell\'Aquila ')
            self.say(self.channel, '  5. Cylon n.6 ')
        if message.lower().find(self.botname.lower()) >= 0:
            self.say(self.channel, self.H.process(message, reply=True, learn=True))
        elif nick.lower().find('mabo') >= 0 or nick.lower().find('mab0') >= 0:
            self.say(self.channel, self.H.process(message, reply=True, learn=False))
        else:
            self.H.process(message, reply=False, learn=True)

    def handle_ping(self):
        yml = open('irchal.yml', 'w')
        yml.write(yaml.dump(self.H))
        yml.close()

def main():
    from optparse import OptionParser
    
    parser = OptionParser(
        usage="usage: %prog [-s irc.server.net [-p 6667]][-c #channel][-n NickName]",
        version="%prog 0.1")
    parser.add_option("-s", "--server",
                      dest="server",
                      default="irc.freenode.net",
                      help="IRC Server name")
    parser.add_option("-p", "--port",
                      dest="port",
                      default="6667",
                      help="IRC server port, default \"6777\"")
    parser.add_option("-c", "--channel",
                      dest="channel",
                      default="#amigaita",
                      help="Name of the bot")
    parser.add_option("-n", "--nick",
                      dest="nick",
                      default="Meila",
                      help="Name of the bot")
    parser.add_option("-t", "--train",
                      dest="train",
                      default=False,
                      help="Path of a file Hal needs to study")
    parser.add_option("-v", "--verbose",
                      dest="verbose",
                      default=False,
                      help="Print to stdout everythng as possible")


    (options, args) = parser.parse_args()

    nickname  = options.nick.capitalize()
    version  = "0.1"
    verbose  = options.verbose
    server   = options.server
    port     = int(options.port)
    channel  = options.channel
    username = "marrano"
    debug    = False
    train    = options.train
    
    if os.path.exists('irchal.yml'):
        with open('irchal.yml', 'rb') as fp:
            hal = yaml.load(fp.read())
    else:
        hal = HAL(4)  

    try:
        if train:
            hal.train(train)
        else:
            bot = ircHAL(server, port, nickname, channel, hal)
            bot.mainloop()
    except (EOFError, KeyboardInterrupt):
        yml = open('irchal.yml', 'w')
        yml.write(yaml.dump(hal))
        yml.close()

    return 0

if __name__ == '__main__':
    sys.exit(main())
