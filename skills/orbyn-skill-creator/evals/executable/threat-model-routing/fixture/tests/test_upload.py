import os
import tempfile
import unittest

import upload


class UploadTests(unittest.TestCase):
    def test_save(self):
        with tempfile.TemporaryDirectory() as folder:
            upload.UPLOAD_DIR = folder
            self.assertEqual(upload.save_upload('a.txt', b'x', 'u')['owner'], 'u')
            self.assertTrue(os.path.exists(os.path.join(folder, 'a.txt')))
