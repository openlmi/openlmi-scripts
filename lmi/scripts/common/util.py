# Copyright (C) 2013-2014 Red Hat, Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of the FreeBSD Project.
#
# Authors: Michal Minar <miminar@redhat.com>
#
"""
Various utilities for LMI Scripts.
"""

class FilteredDict(dict):
    """
    Dictionary-like collection that wraps some other dictionary and provides
    limited access to its keys and values. It permits to get, delete and set
    items specified in advance.

    .. note::
        Please use only the methods overriden. This class does not guarantee
        100% API compliance. Not overriden methods won't work properly.

    :param list key_filter: Set of keys that can be get, set or deleted.
        For other keys, :py:class:`KeyError` will be raised.
    :param dictionary original: Original dictionary containing not only
        keys in *key_filter* but others as well. All modifying operations
        operate also on this dictionary. But only those keys in *key_filter*
        can be affected by them.
    """

    def __init__(self, key_filter, original=None):
        dict.__init__(self)
        if original is not None and not isinstance(original, dict):
            raise TypeError("original needs to be a dictionary")
        if original is None:
            original = dict()
        self._original = original
        self._keys = frozenset(key_filter)

    def __contains__(self, key):
        return key in self._keys and key in self._original

    def __delitem__(self, key):
        if not key in self._keys:
            raise KeyError(repr(key))
        del self._original[key]

    def clear(self):
        for key in self._keys:
            self._original.pop(key, None)

    def copy(self):
        return FilteredDict(self._keys, self._original)

    def iterkeys(self):
        for key in self._keys:
            yield key

    def __getitem__(self, key):
        if not key in self._keys:
            raise KeyError(repr(key))
        return self._original[key]

    def __iter__(self):
        for key in self._keys:
            if key in self._original:
                yield key

    def __eq__(self, other):
        return (   isinstance(other, FilteredDict)
               and self._original == other._original
               and self._keys == other._keys)

    def __lt__(self, other):
        if isinstance(other, dict):
            return {  k: v for k, v in self._original.items()
                   if k in self._keys} < other
        if not isinstance(other, FilteredDict):
            raise TypeError("Can not compare FilteredDict to objects"
                    " of other types!")
        return self._original <= other._original and self._keys <= other._keys

    def __len__(self):
        return len(self.keys())

    def __setitem__(self, key, value):
        if not key in self._keys:
            raise KeyError(repr(key))
        self._original[key] = value

    def keys(self):
        return [k for k in self._keys if k in self._original]

    def values(self):
        return [self._original[k] for k in self.keys() if k in self._original]

    def items(self):
        return [(k, self._original[k]) for k in self.keys()]

    def iteritems(self):
        return iter(self.items())

    def pop(self, key, *args):
        ret = self[key]
        del self[key]
        return ret

    def popitem(self):
        for key in self._keys:
            if key in self._original:
                return self.pop(key)
        raise KeyError("FilterDict is empty!")

    def update(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError('Expected just one positional argument!')
        if args and callable(getattr(args[0], 'keys', None)):
            for key in args[0].keys():
                self[key] = args[0][key]
        elif args:
            for key, value in args[0]:
                self[key] = value
        for key, value in kwargs.items():
            self[key] = value

