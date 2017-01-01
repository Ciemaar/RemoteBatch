import unittest

from pogoplug import *
from secrets import POGOPLUG_VALTOKEN


class ConnectionTest(unittest.TestCase):
    def test_connect(self):
        self.c = Connection(POGOPLUG_VALTOKEN)
        assert self.c
        assert self.c.getUser()


class FileTest(unittest.TestCase):
    def setUp(self):
        self.c = Connection(POGOPLUG_VALTOKEN)

    def test_retrieve_drives(self):
        assert len(self.c.drives)
        for drive in self.c.drives:
            assert isinstance(drive, Directory)

    def test_retrieve_file(self):
        drives = self.c.drives
        assert len(drives[0].files)
        for file_obj in drives[0].files:
            assert isinstance(file_obj, BaseFile)


if __name__ == "__main__":
    unittest.main()
