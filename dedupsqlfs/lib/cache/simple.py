# -*- coding: utf8 -*-
"""
@author Sergey Dryabzhinsky
"""

from time import time

"""
@2020-01-17 New cache item interface

CacheItem:
    c_time: float, timestamp, then added, updated, set to 0 if expired
    c_value: int|str, some data

"""

class CacheItem:
    __slots__ = 'c_time', 'c_value'

    def __init__(self, c_time=0.0, c_value=None):
        self.c_time = c_time
        self.c_value = c_value

try:
    from recordclass import dataobject
    class CacheItem(dataobject):
        c_time: float
        c_value: object
except:
    pass

class CacheTTLseconds(object):
    """
    Simple cache storage
    
    {
        key (int | str) : CacheItem, ...
    }
    
    """

    _max_ttl = 300

    _storage = None

    def __init__(self):
        self._storage = {}
        pass

    def __len__(self):
        return len(self._storage)

    def set_max_ttl(self, seconds):
        self._max_ttl = seconds
        return self

    def set(self, key, value):
        c = CacheItem()
        c.c_time = time()
        c.c_value = value
        self._storage[ key ] = c
        return self

    def get(self, key, default=None):
        # not setted
        now = time()

        item = self._storage.get(key)
        if item is None:
            item = CacheItem()
            item.c_time = 0
            item.c_value = default
        val = item.c_value
        t = item.c_time

        if now - t > self._max_ttl:
            return val

        # update time only if value was set
        if key in self._storage:
            self._storage[ key ].c_time = now

        return val

    def unset(self, key):
        if key in self._storage:
            del self._storage[ key ]
        return self

    def clear(self):
        now = time()
        count = 0
        for key in set(self._storage.keys()):
            item = self._storage[key]
            if now - item.c_time > self._max_ttl:
                del self._storage[key]
                count += 1
        return count
