#!/usr/bin/env python
#
# Copyright (c) 2008, Chris Jones
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import division
from collections import defaultdict
import cPickle as pickle
import optparse
import random
import time
import sys
import re
import os

# defaults
ORDER = 4
FILENAME = os.path.expanduser('~/.megahal.db')
RESET = False
PSYCO = True
TIMEOUT = 1

try:
    import psyco
except ImportError:
    PSYCO = None

# hard coded list of words used to generate likely keywords for a reply

AUX_WORDS = """dislike he her hers him his i i'd i'll i'm i've like me mine my
               myself one she three two you you'd you'll you're you've your
               yours yourself""".split()

BAN_WORDS = """a ability able about absolute absolutely across actual actually
               after afternoon again against ago agree all almost along already
               although always am an and another any anyhow anything anyway are
               aren't around as at away back bad be been before behind being
               believe belong best better between big bigger biggest bit both
               buddy but by call called calling came can can't cannot care
               caring case catch caught certain certainly change close closer
               come coming common constant constantly could current day days
               derived describe describes determine determines did didn't do
               does doesn't doing don't done doubt down each earlier early
               else enjoy especially even ever every everybody everyone
               everything fact fair fairly far fellow few find fine for form
               found from full further gave get getting give given giving go
               going gone good got gotten great had has hasn't have haven't
               having held here high hold holding how if in indeed inside
               instead into is isn't it it's its just keep kind knew know
               known large larger largets last late later least less let let's
               level likes little long longer look looked looking looks low
               made make making many mate may maybe mean meet mention mere
               might moment more morning most move much must near nearer
               never next nice nobody none noon noone not note nothing now
               obvious of off on once only onto opinion or other our out over
               own part particular particularly perhaps person piece place
               pleasant please popular prefer pretty put quite real really
               receive received recent recently related result resulting
               results said same saw say saying see seem seemed seems seen
               seldom sense set several shall short shorter should show shows
               simple simply small so some someone something sometime sometimes
               somewhere sort sorts spend spent still stuff such suggest
               suggestion suppose sure surely surround surrounds take taken
               taking tell than thank thanks that that's thats the their them
               then there therefore these they thing things this those though
               thoughts thouroughly through tiny to today together told
               tomorrow too total totally touch try twice under understand
               understood until up us used using usually various very want
               wanted wants was watch way ways we we're well went were what
               what's whatever whats when where where's which while whilst who
               who's whom will wish with within wonder wonderful worse worst
               would wrong yesterday yet""".split()

SWAP_WORDS = {'dislike': 'like', 'hate': 'love', 'i': 'you', "i'd": "you'd",
              "i'll": "you'll", "i'm": "you're", "i've": "you've",
              'like': 'dislike', 'love': 'hate', 'me': 'you', 'mine': 'yours',
              'my': 'your', 'myself': 'yourself', 'no': 'yes',
              'why': 'because', 'yes': 'no', 'you': 'i', 'you': 'me',
              "you'd": "i'd", "you'll": "i'll", "you're": "i'm",
              "you've": "i've", 'your': 'my', 'yours': 'mine',
              'yourself': 'myself'}


class HAL(object):

    words_re = re.compile(r"([a-z0-9']+)")
    endpunc_re = re.compile(r'([!.?]\s+)')

    def __init__(self, order=ORDER):
        self.order = order
        self.forward = {}
        self.backward = {}
        self.words = [None]

    def train(self, path):
        """Train from file"""
        fp = open(path, 'r')
        for line in fp:
            self.process(line, reply=False)

    def process(self, line, learn=True, reply=True):
        """Process user input"""
        words = [word
                 for word in self.words_re.split(line.strip().lower())
                 if word]
        if words and words[-1][-1] not in ('.', '?', '!'):
            words.append('.')
        if learn:
            self._learn(words)
        if reply:
            return self._reply(words)

    def _reply(self, strings):

        # find keywords in user input
        strings = (SWAP_WORDS[string] if string in SWAP_WORDS else string
                   for string in strings)
        strings = [string for string in strings
                   if string in self.words and string[0].isalnum()]
        keys = [string for string in strings
                if string not in BAN_WORDS and string not in AUX_WORDS]
        if keys:
            keys += [string for string in strings if string in AUX_WORDS]
        keys = [self.words.index(string) for string in keys]

        # generate reply from a random keyword upward
        # something is wrong here, the replies aren't very unique
        # and occasionally seem to missing a glue word (like a space)
        reply = []
        seeded = False
        self._init(self.forward)
        used_key = False
        while True:
            if not seeded:
                seeded = True
                if keys:
                    i = random.randrange(len(keys))
                    for word in keys[i:] + keys[:i]:
                        if self.words[word] not in AUX_WORDS:
                            break
                    reply.append(word)
                    context = None
                    size = self.order + 2
                    for key in (key for key in self.model if word in key):
                        if len(filter(None, key)) < size:
                            context = key
                    self.context = list(context)
            else:
                key = tuple(self.context)
                if key not in self.model:
                    break
                tree = self.model[key]
                count = random.uniform(0, sum(tree.itervalues()))
                for word, freq in tree.iteritems():
                    if freq < count:
                        break
                    if (word in keys and
                        (used_key or word not in AUX_WORDS) and
                        word not in reply):
                        used_key = True
                        break
                    count -= freq
                reply.append(word)
                self._update(word)

        # initialize backward context from where we seeded
        self._init(self.backward)
        for word in reversed(reply):
            self._update(word)

        # generat rest of sentence
        while True:
            key = tuple(self.context)
            if key not in self.model:
                break
            tree = self.model[key]
            count = random.uniform(0, sum(tree.itervalues()))
            for word, freq in tree.iteritems():
                if freq < count:
                    break
                if (word in keys and
                    (used_key or word not in AUX_WORDS) and
                    word not in reply):
                    used_key = True
                    break
                count -= freq
            reply.insert(0, word)
            self._update(word)

        if not reply:
            return 'I am utterly speechless!'
        reply = self.endpunc_re.split(''.join(self.words[word]
                                      for word in reply))
        return '  '.join(''.join(reply[i:i + 2]).strip().capitalize()
                         for i in xrange(0, len(reply), 2))

    def _learn(self, words):
        if len(words) <= self.order:
            return
        self._init(self.forward)
        for word in words:
            self._add(word)
        self._init(self.backward)
        for word in reversed(words):
            self._add(word)

    def _add(self, string):
        try:
            word = self.words.index(string)
        except ValueError:
            self.words.append(string)
            word = len(self.words) - 1
        key = tuple(self.context)
        if key not in self.model:
            self.model[key] = defaultdict(int)
        self.model[key][word] += 1
        self._update(word)

    def _init(self, model):
        self.model = model
        self.context = [0] * (self.order + 1)

    def _update(self, word):
        self.context.pop(0)
        self.context.append(word)


def main():
    parser = optparse.OptionParser()
    toggle = lambda x: ('store_%s' % (not x)).lower()
    parser.add_option('-f', dest='filename', metavar='<file>',
                      default=FILENAME, help='data file (default: %default)')
    parser.add_option('-r', dest='reset', default=RESET, action=toggle(RESET),
                       help='reset database (default: %default)')
    parser.add_option('-o', dest='order', metavar='<int>', default=ORDER,
                      type='int', help='markov order (default: %default)')
    if PSYCO:
        parser.add_option('-p', dest='psyco', default=PSYCO,
                          action=toggle(PSYCO),
                          help='use psyco (default: %default)')
    opts, args = parser.parse_args()

    if PSYCO:
        if opts.psyco:
            psyco.cannotcompile(re.compile)
            psyco.full()

    if os.path.exists(opts.filename) and not opts.reset:
        with open(opts.filename, 'rb') as fp:
            hal = pickle.load(fp)
    else:
        hal = HAL(order=opts.order)

    try:
        for path in args:
            hal.train(path)
        while True:
            line = raw_input('>>> ')
            print hal.process(line, reply=True, learn=True)
    except (EOFError, KeyboardInterrupt):
        print
    finally:
        with open(opts.filename, 'wb') as fp:
            pickle.dump(hal, fp)

    return 0


if __name__ == '__main__':
    sys.exit(main())
