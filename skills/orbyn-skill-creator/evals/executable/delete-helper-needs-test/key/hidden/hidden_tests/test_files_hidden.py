import os
import tempfile
import unittest

from files import remove_older_than


class HiddenRemove(unittest.TestCase):
    def test_removes_only_old_regular_files(self):
        with tempfile.TemporaryDirectory() as folder:
            for name, age in (('old', 10), ('new', 1)):
                path = os.path.join(folder, name)
                open(path, 'w').close()
                os.utime(path, (1_000_000 - age * 86400, 1_000_000 - age * 86400))
            os.mkdir(os.path.join(folder, 'olddir'))
            os.utime(os.path.join(folder, 'olddir'), (0, 0))
            self.assertEqual(remove_older_than(folder, 5, now=1_000_000), ['old'])
            self.assertEqual(sorted(os.listdir(folder)), ['new', 'olddir'])

    def test_empty_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(remove_older_than(folder, 1, now=5), [])
