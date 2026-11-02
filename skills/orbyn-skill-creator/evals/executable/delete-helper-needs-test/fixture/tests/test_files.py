import os
import tempfile
import unittest

from files import list_files


class FilesTests(unittest.TestCase):
    def test_lists_only_files(self):
        with tempfile.TemporaryDirectory() as folder:
            open(os.path.join(folder, 'a'), 'w').close()
            os.mkdir(os.path.join(folder, 'd'))
            self.assertEqual(list_files(folder), ['a'])
