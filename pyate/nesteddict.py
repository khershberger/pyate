# -*- coding: utf-8 -*-
"""
Created on Tue Apr 30 10:13:54 2019

@author: kyleh
"""

from functools import reduce


class NestedDict(object):
    def __init__(self, data=None):
        if data is None:
            self.d = {}
        else:
            self.d = data

    def __repr__(self):
        return self.d.__repr__()

    def __getitem__(self, key):
        try:
            if isinstance(key, tuple):
                if len(key) > 1:
                    return reduce(dict.__getitem__, key, self.d)
                else:
                    key = key[0]  # Extract contenst of singular tuple
            return self.d[key]
        except KeyError as e:
            raise KeyError(key)

    def __setitem__(self, key, val):
        try:

            def helper(d, key, val):
                if isinstance(key, tuple):
                    if len(key) > 1:
                        if key[0] not in d:
                            dict.__setitem__(d, key[0], {})
                        return helper(d.__getitem__(key[0]), key[1:], val)
                    else:
                        key = key[0]
                return dict.__setitem__(d, key, val)

            return helper(self.d, key, val)
        except KeyError as e:
            raise KeyError(key)


# class NestedDictExtend(dict):
#     def __getitem__(self, key):
#         if isinstance(key, tuple):
#             if len(key) > 1:
#                 print('__getitem__():  tuple')
#                 #return self[key[0]][key[1:]]
#                 return self.__getitem__(key[0]).__getitem__(key[1:])
#             else:
#                 key = key[0]  # Extract contenst of singular tuple
#
#         print('__getitem__():  super.__getitem__()')
#         #return super(NestedDict, self).__getitem__(key)
#         return dict.__getitem__(self, key)
#
#     def __setitem__(self,key, val):
#         if isinstance(key, tuple):
#             if len(key) > 1:
#                 if key[0] not in self:
#                     dict.__setitem__(self, key[0], NestedDict())
#                 return self.__getitem__(key[0]).__setitem__(key[1:], val)
#             else:
#                 key = key[0]
#         return dict.__setitem__(self, key, val)
#
