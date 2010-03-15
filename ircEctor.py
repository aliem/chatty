#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:et:ts=2

# Copyright (C) 2009 Lorenzo GIULIANI 
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Lorenzo Giuliani - lor@frenzart.com 

# $Id$
"""
  irc module for pyEctor.py
"""

__author__    = "Lorenzo Giuliani (lor@frenzart.com)"
__version__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2009 Lorenzo Giuliani"
__license__   = "GPL"

from pyector.Ector import *
from IRCClient import *
import sys, locale

ENCODING    = locale.getdefaultlocale()[1]
DEFAULT_ENCODING    = sys.getdefaultencoding()

sys.setrecursionlimit(4000)

class ircECTOR(LogAllMixin, IRCClient):
  def __init__(self, server, port, nick, channel):
    self.botname = nick
    self.channel = channel
    IRCClient.__init__(self, server, port)
    self.connect(nick, "No, I am not a bot!")
    self.join(channel)

    self.previousEntryNode = None
    self.lastEntryNode = None

    UttererNode.__decay    = 5
    SentimentNode.__decay  = 5
    ExpressionNode.__decay = 20
    SentenceNode.__decay   = 25
    TokenNode.__decay      = 20
    self.ector = Ector(nick)

  def handle_say(self, source, to, message):
    nick = getnick(source)
    
    ##message = message.decode('iso-8859-1')

    if to == self.channel:
      #self.ector.setUser(nick)
      self.lastEntryNode = self.ector.addEntry(message)
      if self.previousEntryNode:
        self.ector.cn.addLink(self.previousEntryNode, self.lastEntryNode)
      else:
        self.lastEntryNode.beg += 1
      
      self.ector.cleanState()
      self.ector.propagate(2)
      
      replyNode = self.ector.getActivatedSentenceNode()
      reply     = replyNode.getSymbol()
      reply     = reply.replace("@bot@", nick)
      reply     = reply.replace("@user@", self.botname)
      self.previousEntryNode = replyNode
      """
      (reply, nodes)    = self.ector.generateSentence()
      reply     = reply.replace("@bot@",  nick)
      reply     = reply.replace("@user@", self.botname)
      previousSentenceNode = None
      """

      if message.lower().find(self.botname.lower()) >= 0 or nick.lower() == "mic64" or nick.lower() == "mabo" or nick.lower() == "mab0":        
        self.say(self.channel, reply)

      return
    elif to == self.get_nick():
      l = message.strip().lower().split(" ")
      if len(l) < 1:
        self.say(nick, "hi, do i know you?")
        return
      if l[0] == "dump":
        f = self.ector.dump()
        if f["cn"] < 1:
          self.say(nick,"returned an int < 1")
        elif f["cn"] > 0:
          self.say(nick,"returned an int > 0")
        return
      else:
        self.say(nick, "sorry, i can't understand")
      return

  def handle_ping(self):
    """
      since Ector can work only with one user at time
      this will save the User State in one single file

      TODO: look into Eric to give him a list of users instead
    """
    self.ector.setUser("User")
    d = self.ector.dump()
    print >>sys.stderr, "++> Writing ECTOR dump ( "+str(d)+" )"


def main():
  from optparse import OptionParser

  parser = OptionParser(
      usage="usage: %prog [-s irc.server.net [-p 6667]][-c #channel][-n NickName]",
      version="%prog 0.1")
  parser.add_option(
      "-s", "--server",
      dest="server",
      default="irc.freenode.net",
      help="IRC Server name")
  parser.add_option(
      "-p", "--port",
      dest="port",
      default="6667",
      help="IRC server port, default \"6777\"")
  parser.add_option(
      "-c", "--channel",
      dest="channel",
      default="#amigaita",
      help="Name of the bot")
  parser.add_option(
      "-n", "--nick",
      dest="nick",
      default="Iaia",
      help="Name of the bot")
  parser.add_option(
      "-v", "--verbose",
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
    
  # Quiet mode is above sentence or generate modes
  if not verbose:
    sentence_mode    = False
    generate_mode    = False
    
  previousSentenceNode    = None
  nodes                   = None

  try:
    bot = ircECTOR(server, port, nickname, channel)
    bot.mainloop()
  except (KeyboardInterrupt):
    bot.dump()

  return 0

if __name__ == "__main__":
  sys.exit(main())
