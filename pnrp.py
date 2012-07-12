#!/usr/bin/python
#
# Pipo
# http://snarfed.org/space/windows+p2p
# Copyright 2003 Ryan Barrett <pipo@ryanb.org>
#
# File: pnrp.py
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA

"""
Implements the multi-level cache part of the Peer Network Resolution Protocol,
which is part of Microsoft's Peer-to-Peer networking protocol:
http://www.microsoft.com/technet/prodtechnol/winxppro/deploy/p2pintro.mspx
"""

import time
import math


class PnrpCache:

  """ Implements a multi-level PnrpCache, as described in the Windows
  Peer-to-Peer white paper. Maps a peer ID to a CPA, or Certified Peer Address.
  Each level of the cache is one tenth the size of the level above it, and each
  level has a maximum number of entries. The bottom level is anchored by the
  seed, which is usually the local peer ID. Eviction is done on an LRU basis.
  """
  __cloud_size  = None
  __level_size  = None
  __max_levels  = None
  __seed_id     = None
  __levels      = None   # list of (min id, max id, cache dictionary) tuples.
                         # each cache maps a peer id to a (cpa, timestamp).
                         # (timestamp is seconds since the epoch, as a float.)

  def __init__(self, cloud_size, level_size, seed_id, seed_cpa):
    """ The constructor. cloud_size is the size of the peer ID space (ie the
    largest possible peer ID plus one), level_size is the max # of entries in
    each level, and seed_id and seed_cpa comprise is the initial cache line.
    """
    assert cloud_size > 0 and level_size > 0

    self.__cloud_size = cloud_size
    self.__level_size = level_size
    self.__max_levels = math.ceil(math.log10(cloud_size))

    self.__seed_id = seed_id
    self.__levels = [(0, cloud_size, {})]   # first level is the whole cloud
    self.add(seed_id, seed_cpa)
    

  def add(self, id, cpa):
    """ Adds the given id => cpa mapping to the cache. If the current level is
    full and is the bottom level another level is added if possible. Otherwise,
    a cache line will be evicted.
    """
    assert id >= 0 and id < self.__cloud_size

    # find the appropriate level and add it
    level = self.__find_level(id)
    cache = self.__levels[level][2]
    cache[id] = (cpa, time.time())

    # if this made the level full, add levels until the bottom level isn't
    # full, or until we can't add any more levels
    while (len(cache) > self.__level_size and 
           len(self.__levels) < self.__max_levels):
        self.__add_level()
        cache = self.__levels[-1][2]

    if len(cache) > self.__level_size:
      self.__evict(cache)


  def get(self, id):
    """ Returns the CPA for this id. In the process, the timestamp on its cache
    line is updated to maintain state for LRU eviction. Throws a KeyError if
    the id is not in the cache.
    """
    cache = self.__levels[self.__find_level(id)][2]
    cpa, timestamp = cache[id]
    cache[id] = (cpa, time.time())
    return cpa


  def get_closest(self, id):
    """ Returns the CPA of the cached id closest (numerically) to the given id.
    This is used for finding a peer using the DHT properties of the cache - to
    find a given peer, you'll need to talk to at most log(peers in the cloud.)
    """
    canary = (id, (0, 0))
    all = [canary]

    for min, max, cache in self.__levels:
      all += cache.items()

    all.sort()
    i = all.index(canary)
    previd, (prevcpa, t) = all[i - 1]     # these work because of circularity
    nextid, (nextcpa, t) = all[(i + 1) % len(all)]

    prevdiff = abs(id - previd)
    nextdiff = abs(id - nextid)
    if i == 0:
      prevdiff = self.__cloud_size - prevdiff
    elif i == len(all) - 1:
      nextdiff = self.__cloud_size - nextdiff

    if prevdiff < nextdiff:
      return prevcpa
    else:
      return nextcpa
  

  def __find_level(self, id):
    """ Returns the level in the cache where the given id belongs. (Note that
    the appropriate level might not have been created yet, in which case
    find_level will return the lowest level that has been created.)
    """
    # search levels bottom-up, so that we return the lowest possible level
    for i in range(len(self.__levels) - 1, -1, -1):
      min, max, cache = self.__levels[i]
      if ((min <= max and id >= min and id < max) or
          (min > max and id >= min or id < max)):       # if level is circular
        return i

    assert False, "id %d outside cloud [0, %d]" % (id, self.__cloud_size)


  def __add_level(self):
    """ Adds a level to the cache, and moves the seed and any other appropriate
    cache lines to the new level.
    """
    num_levels = len(self.__levels)
    assert num_levels < self.__max_levels

    # create new level
    level_size = math.ceil(self.__cloud_size / 10 ** num_levels)
    min = (self.__seed_id - level_size / 2) % self.__cloud_size
    max = (self.__seed_id + level_size / 2) % self.__cloud_size
    self.__levels.append((min, max, {}))

    # move existing cache lines to new level
    old = self.__levels[num_levels - 1][2]
    new = self.__levels[num_levels][2]
    for (key, value) in old.items():
      level = self.__find_level(key)
      if level != num_levels - 1:
        assert level== num_levels
        del old[key]
        new[key] = value
    # end for


  def __evict(self, cache):
    """ Evicts a cache line by LRU.
    """
    swapped = [(timestamp, id) for id, (cpa, timestamp) in cache.items()
               if id != self.__seed_id]  # the seed should never be evicted
    evictee = min(swapped)[1]
    del cache[evictee]
    
    

              
