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
ELECTION_TIMEOUT = (0, 10)  # min, max
RPC_DELAY = (0, 10)
NEW_LOG_EVERY = (1, 3)
RPC_FAIL_RATE = .1

# globals, initialized in main
nodes = None

LogEntry = collections.namedtuple('Log', ('term', 'index', 'contents'))


def rpc(method):
    """Decorator for RPC methods.

    Expects that the RPC method returns a string with the result.

    * Resets the election timeout.
    * Delays random amount 1-20s.
    * Occasionally fails, ie doesn't call the decorated method.
    """
    def wrapper(self, src, term, *args):
        label = f'{src} => {self} {method.__name__}'
        if random.random() < RPC_FAIL_RATE:
            print(f'{label}: randomly failed')
            return

        delay = random.triangular(*RPC_DELAY, 3)

        def receive():
            self.reset_election_timeout()
            result = method(self, src, term, *args)
            print(f'{label}: {result}')

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
    log = None
    last_applied = 0  # within the current term
    last_committed = 0
    matched_nodes = None  # only on leader; nodes that are fully up to date

    def __init__(self, name):
        self.name = name
        self.state = 'follower'
        self.term = 0
        self.votes = set()
        self.log = []
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
        self.last_applied = self.last_committed = 0
        self.voted_for = None
        self.votes = set()
        self.matched_nodes = None

    def reset_election_timeout(self):
        if self.election_timeout:
            self.election_timeout.cancel()

        delay = random.uniform(*ELECTION_TIMEOUT)
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

        if self.state != 'follower':
            result = f'currently a {self.state}'
            granted = False
        elif self.voted_for:
            result = f'already voted for {self.voted_for}'
            granted = False
        else:
            result = 'already granted' if self.voted_for == src.name else 'granting!'
            self.voted_for = src.name
            granted = True

        src.vote(self, self.term, granted)
        return result

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
            self.votes = set()
            self.matched_nodes = set()
            print(f'{self} is now leader! With votes {self.votes}')
            Timer(random.uniform(*NEW_LOG_EVERY), self.new_log).start()

    def new_log(self):
        if self.state != 'leader':
            return

        self.last_applied += 1
        contents = random.choice(string.ascii_uppercase)
        self.log.append(LogEntry(self.term, self.last_applied, contents))
        for node in nodes:
            if node is not self:
                node.append_log(self, self.term, self.last_applied,
                                self.last_committed, contents)

        Timer(random.uniform(*NEW_LOG_EVERY), self.new_log).start()

    @rpc
    def append_log(self, src, term, apply_index, commit_index, contents):
        if self.term > term:
            return 'received term is old'
        self.maybe_advance_term(term)

        if apply_index <= self.last_applied:
            return 'already applied'
        elif apply_index > self.last_applied + 1:
            return f'received index {apply_index} too far ahead'

        self.last_applied += 1
        self.log.append(LogEntry(self.term, self.last_applied, contents))
        self.commit_index = min(commit_index, self.last_applied)
        src.appended(self, self.term, self.last_applied)
        return 'applied!'

    @rpc
    def appended(self, src, term, applied_index):
        if term < self.term:
            return 'term is too old'

        assert term == self.term
        if applied_index > self.last_committed:
            self.matched_nodes.add(src.name)
            if len(self.matched_nodes) + 1 >= round(len(nodes) / 2):
                self.last_committed += 1
                self.matched_nodes = set()
                print(f'{self} advanced commit index to {self.last_committed}')


def main():
    global nodes
    nodes = [Node(string.ascii_uppercase[i]) for i in range(NUM_NODES)]
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
