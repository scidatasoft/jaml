import sys
from unittest import TestCase

from utils.utils import Tee


class TestTee(TestCase):
    def test_get_content(self):
        with Tee(sys.stdout) as out, Tee(sys.stderr) as err:
            print('Hello to stdout')
            print('Hello to stdout again')
            print('Hello to stderr', file=sys.stderr)
            print('Hello to stderr again', file=sys.stderr)

        print(out.getvalue(), end='')
        print(err.getvalue(), end='', file=sys.stderr)
