"""Toy implementation of the Raft consensus protocol.

https://raft.github.io/
http://thesecretlivesofdata.com/raft/
"""
import collections
from datetime import datetime, timedelta
import random
import string
from threading import Thread, Timer
import time

# all times are in seconds
NUM_NODES = 3
ELECTION_TIMEOUT_MIN = 0
ELECTION_TIMEOUT_MAX = 10
DELAY_MIN = 0
DELAY_MAX = 10
RPC_FAIL_RATE = .1

# globals, initialized in main
nodes = None
# events = []

# Event = collections.namedtuple('Event', ('when', 'callable'))
Log = collections.namedtuple('Log', ('term', 'index', 'contents'))


def rpc(method):
    """Decorator for RPC methods.

    * Resets the election timeout.
    * Delays random amount 1-20s.
    * Occasionally fails, ie doesn't call the decorated method.
    """
    def wrapper(self, src, term, *args):
        label = f'{src} => {self} {method.__name__}'
        if random.random() < RPC_FAIL_RATE:
            print(f'Randomly failing {label}')
            return

        delay = random.triangular(DELAY_MIN, DELAY_MAX, 3)

        def receive():
            self.reset_election_timeout()
            method(self, src, term, *args)

        Timer(delay, receive).start()

    return wrapper


class Node:
    name = None
    state = None  # 'follower', 'candidate', 'leader'

    # leader election
    term = 0
    votes = None  # set, names of voters
    voted_for = None  # name of votee
    election_timeout = None  # Timer

    # log replication
    last_applied = None
    last_committed = None

    def __init__(self, name):
        self.name = name
        self.state = 'follower'
        self.term = 0
        self.votes = set()
        self.reset_election_timeout()

    def __str__(self):
        return f'{self.name} ({self.state}, {self.term})'

    def maybe_advance_term(self, term):
        """Returns True if our term advanced, False otherwise."""
        if term <= self.term:
            return False

        self.state = 'follower'  # TODO: unless this is now the leader?
        print(f'{self} advancing term from {self.term} to {term}')
        self.term = term
        self.voted_for = None
        self.votes = set()

    def reset_election_timeout(self):
        if self.election_timeout:
            self.election_timeout.cancel()

        delay = random.uniform(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)
        print(f'{self} setting election timeout to {delay:.1f}s')
        self.election_timeout = Timer(delay, self.election)
        self.election_timeout.start()

    def election(self):
        self.maybe_advance_term(self.term + 1)

        if self.state == 'follower':
            print(f'{self} becoming candidate')
            self.state = 'candidate'

        self.votes = set((self.name,))
        for node in nodes:
            if node is not self:
                node.request_vote(self, self.term)

    @rpc
    def request_vote(self, src, term):
        self.maybe_advance_term(term)
        msg = f'{src} requested vote from {self}, '
        if self.state != 'follower':
            msg += f'currently a {self.state}'
            granted = False
        elif self.voted_for:
            msg += f'already voted for {self.voted_for}'
            granted = False
        else:
            msg += 'already granted' if self.voted_for == src.name else 'granting!'
            self.voted_for = src.name
            granted = True

        print(msg)
        src.vote(self, self.term, granted)

    @rpc
    def vote(self, src, term, granted):
        if self.maybe_advance_term(term):
            return
        elif not granted:
            return

        print(f'{self} received vote from {src}')
        self.votes.add(src.name)
        if len(self.votes) >= round(len(nodes) / 2):
            self.state = 'leader'
            print(f'{self} is now leader! With votes {self.votes}')
            self.votes = set()

    @rpc
    def append(self, src, term, contents):
        pass


def main():
    global nodes
    nodes = [Node(string.ascii_uppercase[i]) for i in range(NUM_NODES)]
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
