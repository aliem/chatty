#!/bin/python
# IRC client class.                                           vim:et:ts=4
# Adam Sampson <azz@gnu.org>

import sys, socket

def getnick(s):
    n = s.find("!")
    if n > -1:
        return s[:n]
    else:
        return s

def ircsplit(s, num):
    """Split a string of the form word1 word2 .. wordN :string."""
    l = s.split(" ", num)
    if len(l) < (num + 1):
        l.append(None)
    elif l[num][0] == ":":
        l[num] = l[num][1:]
    return l

class IRCClient:
    """A simple IRC client class. Subclass this to implement your own
    IRC applications."""

    def __init__(self, server, port):
        """Open a connection to an IRC server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server
        self.socket.connect((self.server, port))
        self.fd = self.socket.makefile("r")
        self.open = 1
        self.my_nick = None

    def __del__(self):
        """Close the connection."""
        if self.open: self.quit()

    def send(self, string):
        """Send a string to the server."""
        self.handle_outgoing(string)
        self.socket.send(string + "\n")

    def recv(self):
        """Read a line from the server. Return None on EOF."""
        line = self.fd.readline()
        if line == "":
            return None
        else:
            s = line.strip()
            self.handle_incoming(s)
            return s

    def connect(self, nick, realname = "IRCClient", password = None):
        """Log in to the server."""
        if password: self.send("PASS :" + password)
        self.nick(nick)
        self.send("USER " + nick + " 0 * :" + realname)

    def nick(self, nick):
        self.send("NICK " + nick)
        self.my_nick = nick

    def kick(self, channel, nick, reason):
        if reason is None:
            self.send("KICK " + channel + " " + nick)
        else:
            self.send("KICK " + channel + " " + nick + " :" + reason)

    def topic(self, channel, topic):
        self.send("TOPIC " + channel + " :" + topic)

    def quit(self, reason = "Quit"):
        """Quit from the server."""
        self.send("QUIT :" + reason)
        self.socket.close()
        self.open = 0

    def join(self, channel, key = None):
        """Join a channel."""
        if key is None:
            self.send("JOIN " + channel)
        else:
            self.send("JOIN " + channel + " " + key)

    def usermode(self, channel, user, mode):
        """Change a user's modes on a channel."""
        self.send("MODE " + channel + " " + mode + " " + user)

    def op(self, channel, user): self.usermode(channel, user, "+o")
    def deop(self, channel, user): self.usermode(channel, user, "-o")
    def voice(self, channel, user): self.usermode(channel, user, "+v")
    def devoice(self, channel, user): self.usermode(channel, user, "-v")
        
    def say(self, to, text):
        """Send a message to a user or channel."""
        self.send("PRIVMSG " + to + " :" + text)

    def notice(self, to, text):
        self.send("NOTICE " + to + " :" + text)

    def mainloop(self):
        while 1:
            line = self.recv()
            if not line: break

            prefix = None
            if line[0] == ":": (prefix, line) = line[1:].split(" ", 1)
            (command, params) = line.split(" ", 1)
           
            if command[0] >= '0' and command[0] <= '9':
                # Server reply
                code = int(command)
                self.handle_reply(prefix, code, params)
            elif command == "PING":
                self.send("PONG " + params)
                self.handle_ping()
            elif command == "NICK":
                l = ircsplit(params, 0)
                self.handle_nick(prefix, l[0])
            elif command == "MODE":
                self.handle_mode(prefix, params)
            elif command == "QUIT":
                l = ircsplit(params, 0)
                self.handle_quit(prefix, l[0])
            elif command == "JOIN":
                l = ircsplit(params, 0)
                self.handle_join(prefix, l[0])
            elif command == "PART":
                l = ircsplit(params, 1)
                self.handle_part(prefix, l[0], l[1])
            elif command == "TOPIC":
                l = ircsplit(params, 1) 
                self.handle_topic(prefix, l[0], l[1])
            elif command == "INVITE":
                l = ircsplit(params, 1)
                self.handle_invite(prefix, l[0], l[1])
            elif command == "KICK":
                l = ircsplit(params, 2)
                self.handle_kick(prefix, l[0], l[1], l[2])
            elif command == "PRIVMSG":
                l = ircsplit(params, 1)
                self.handle_say(prefix, l[0], l[1])
            elif command == "NOTICE":
                l = ircsplit(params, 1)
                self.handle_notice(prefix, l[0], l[1])
            else:
                self.handle_command(prefix, command, params)
                
    def getnick(self, s):
        return split(s, "!", 1)[0]

    def get_nick(self): return self.my_nick

    def handle_incoming(self, line): pass
    def handle_outgoing(self, line): pass
    def handle_nick(self, old, new): pass
    def handle_mode(self, nick, modes): pass
    def handle_quit(self, nick, reason): pass
    def handle_join(self, nick, channel): pass
    def handle_part(self, nick, channel, reason): pass
    def handle_topic(self, nick, channel, topic): pass
    def handle_invite(self, source, to, channel): pass
    def handle_kick(self, source, channel, to, reason): pass
    def handle_say(self, source, to, message): pass
    def handle_notice(self, source, to, message): pass
    def handle_unknown(self, prefix, command, params): pass
    def handle_reply(self, prefix, code, params): pass
    def handle_ping(self): pass

class LogAllMixin:
    def handle_incoming(self, line):
        print >>sys.stderr, "< " + line

    def handle_outgoing(self, line):
        print >>sys.stderr, "> " + line

