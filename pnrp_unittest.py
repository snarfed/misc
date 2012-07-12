#!/usr/bin/python
#
# Pipo
# http://snarfed.org/space/windows+p2p
# Copyright 2003 Ryan Barrett <pipo@ryanb.org>
#
# File: pnrp_unittest.py
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
Unit tests for pnrp.py.
"""

import select
import unittest
from pnrp import PnrpCache

class pnrpUnitTest(unittest.TestCase):

  def setUp(self):
    pass

  def test_create(self):
    # try creating a cache with level size 0
    self.assertRaises(AssertionError, PnrpCache, 5, 0, 3, 4)

    # try create a cache with cloud size -1
    self.assertRaises(AssertionError, PnrpCache, -1, 3, 3, 4)

    # try creating a cache with seed > cloud size
    self.assertRaises(AssertionError, PnrpCache, 5, 3, 10, 4)

    # try creating a cache with seed -2
    self.assertRaises(AssertionError, PnrpCache, 5, 3, -2, 4)

    # create a cache with only one level
    cache = PnrpCache(10, 10, 0, 1)
    self.assertEqual(1, cache.get(0))
    self.assertUncached(cache, 2)


  def test_add(self):
    cache = PnrpCache(10, 10, 0, 1)

    try:
      cache.add(-1, 0)
      self.fail('added a negative peer id')
    except:
      pass

    try:
      cache.add(100, 0)
      self.fail('added a peer id outside of the cloud namespace')
    except:
      pass

    cache.add(2, 3)
    self.assertEqual(3, cache.get(2))

    cache.add(4, 5)
    cache.add(6, 7)
    cache.add(8, 9)

    self.assertEqual(5, cache.get(4))
    self.assertEqual(7, cache.get(6))

    cache.add(0, 9)
    self.assertEqual(9, cache.get(0))


  def test_eviction(self):
    """ NOTE: This uses select([], [], [], ...) as a poor-man's sleep()
    function. This may not work on Windows!
    """
    cache = PnrpCache(10, 3, 0, 1)  # only one level

    cache.add(2, 3)
    self.sleep(.1)
    cache.add(4, 5)

    # cache is now full. next addition should evict id 2 (not 0; it's the seed)
    self.sleep(.1)
    cache.add(6, 7)
    self.assertUncached(cache, 2)

    # check that get() updates timestamp for LRU
    cache.get(4)
    cache.add(8, 9)
    self.assertUncached(cache, 6)


  def test_new_level(self):
    # 3-level cache, max 2 entries each level
    cache = PnrpCache(1000, 2, 0, 1)

    cache.add(201, 1)
    cache.add(301, 1)   # should create a new level, containing (0, 1)

    self.assertEquals(2, len(cache._PnrpCache__levels))
    cache.get(0)        # make sure these are all still cached
    cache.get(201)
    cache.get(301)

    cache.add(21, 1)
    cache.add(31, 1)    # should create a new level, containing (0, 1)

    self.assertEquals(3, len(cache._PnrpCache__levels))
    cache.get(0)        # make sure these are all still cached
    cache.get(21)
    cache.get(31)
    cache.get(201)
    cache.get(301)

    cache.add(2, 1)
    self.sleep(.1)
    cache.add(3, 1)     # should evict (2, 1)
    self.assertUncached(cache, 2)


  def test_add_that_creates_multiple_levels_and_evicts(self):
    cache = PnrpCache(9000, 3, 0, 1)

    cache.add(2, 3)
    self.sleep(1)
    cache.add(3, 4)
    self.assertEqual(1, len(cache._PnrpCache__levels))

    cache.add(8999, 5)
    self.assertEqual(4, len(cache._PnrpCache__levels))
    self.assertUncached(cache, 2)


  def test_seed_not_evicted(self):
    cache = PnrpCache(10, 2, 0, 1)
    cache.add(2, 3)
    cache.add(4, 5)

    cache.get(0)
    cache.get(4)
    self.assertUncached(cache, 2)



  def test_circularity(self):
    cache = PnrpCache(100, 2, 0, 1)
    cache.add(20, 1)
    cache.add(30, 1)

    # the bottom level should be circular
    self.assertEqual(2, len(cache._PnrpCache__levels))
    min, max, bottom_level = cache._PnrpCache__levels[1]
    self.assertEqual(95, min)
    self.assertEqual(5, max)

    cache.add(95, 1)
    self.assertEqual(1, bottom_level[95][0])

    self.sleep(.1)
    cache.add(4, 1)
    self.assertEqual(1, bottom_level[4][0])
    self.assertUncached(cache, 95)

    self.sleep(.1)
    cache.add(6, 1)
    top_level = cache._PnrpCache__levels[0][2]
    self.assertEqual(1, top_level[6][0])
    self.assertUncached(cache, 20)


  def test_get_closest(self):
    cache = PnrpCache(1000, 1, 0, 1)

    self.assertEquals(1, cache.get_closest(0))

    cache.add(50, 2)
    self.assertEquals(1, cache.get_closest(4))
    self.assertEquals(2, cache.get_closest(26))
    self.assertEquals(2, cache.get_closest(400))
    self.assertEquals(1, cache.get_closest(600))
    self.assertEquals(1, cache.get_closest(997))

    cache.add(500, 3)
    self.assertEquals(2, cache.get_closest(200))
    self.assertEquals(3, cache.get_closest(300))
    self.assertEquals(3, cache.get_closest(740))
    self.assertEquals(1, cache.get_closest(760))


  #
  # utility methods
  #
  def sleep(self, secs):
    """ NOTE: This uses select([], [], [], ...) as a poor-man's sleep()
    function. This may not work on Windows!
    """
    select.select([], [], [], secs)

  def assertUncached(self, cache, id, msg = None):
    if not msg:
      msg = 'id %d should not exist in cache!' % id

    try:
      cache.get(id)
      print cache._PnrpCache__levels
      self.fail(msg)
    except KeyError:
      pass

if __name__ == '__main__':
  unittest.main()
