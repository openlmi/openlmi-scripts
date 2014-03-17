import unittest

from lmi.scripts.common.util import FilteredDict

class FilteredDictTest(unittest.TestCase):

    def test_empty(self):
        d = FilteredDict(tuple(), {})
        self.assertEqual(0, len(d))
        self.assertNotIn('key', d)
        self.assertEqual(0, len(d.keys()))
        self.assertEqual(0, len(d.values()))
        self.assertEqual(0, len(d.items()))
        self.assertRaises(KeyError, d.__getitem__, 'key')
        self.assertRaises(KeyError, d.__setitem__, 'key', 'value')

    def test_empty_keys(self):
        d = FilteredDict(tuple(), {'a': 1})
        self.assertEqual(0, len(d))
        self.assertNotIn('a', d)
        self.assertEqual(0, len(d.keys()))
        self.assertEqual(0, len(d.values()))
        self.assertEqual(0, len(d.items()))
        self.assertRaises(KeyError, d.__getitem__, 'a')
        self.assertRaises(KeyError, d.__setitem__, 'a', 2)

    def test_empty_origin(self):
        d = FilteredDict(tuple('a'), {})
        self.assertEqual(0, len(d))
        self.assertNotIn('a', d)
        self.assertEqual(0, len(d.keys()))
        self.assertEqual(0, len(d.values()))
        self.assertEqual(0, len(d.items()))
        self.assertRaises(KeyError, d.__getitem__, 'a')
        d['a'] = 1
        self.assertEqual(1, len(d))
        self.assertEqual(1, d['a'])
        self.assertIn('a', d)
        self.assertEqual(['a',], d.keys())
        self.assertEqual([1], d.values())
        self.assertEqual([('a', 1)], d.items())
        di = d.iteritems()
        self.assertEqual(('a', 1), di.next())
        self.assertRaises(StopIteration, di.next)
        d['a'] = 2
        self.assertEqual(2, d['a'])
        del d['a']
        self.assertEqual(0, len(d))

    def test_filled(self):
        original = {'b': 2, 'c': 3}
        d = FilteredDict(('a', 'b'), original)
        self.assertEqual(1, len(d))
        self.assertNotIn('a', d)
        self.assertIn('b', d)
        self.assertNotIn('c', d)
        self.assertEqual(1, len(d.keys()))
        self.assertEqual(1, len(d.values()))
        self.assertEqual(1, len(d.items()))
        self.assertRaises(KeyError, d.__getitem__, 'a')
        self.assertEqual(2, d['b'])
        di = d.iteritems()
        self.assertEqual(('b', 2), di.next())
        self.assertRaises(StopIteration, di.next)
        self.assertEqual(2, d.pop('b'))
        self.assertEqual(0, len(d))
        self.assertEqual({'c': 3}, original)
        d.update({'a': 1, 'b': 4})
        self.assertEqual({'a': 1, 'b': 4, 'c': 3}, original)
        self.assertEqual(2, len(d))
        self.assertEqual(set((('a', 1), ('b', 4))), set(d.items()))
        d.clear()
        self.assertEqual(0, len(d))
        self.assertEqual({'c': 3}, original)
        self.assertRaises(KeyError, d.__setitem__, 'c', 5)
        self.assertRaises(KeyError, d.update, {'b': 2, 'c': 3})

if __name__ == '__main__':
    unittest.main()
