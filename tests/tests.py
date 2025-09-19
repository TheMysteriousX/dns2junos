import unittest

from scripts.dns2junos import main

# flake8: noqa: E501


class TestScript(unittest.TestCase):

    def test_exec(self):
        with self.assertRaises(SystemExit) as e:
            main()
        self.assertEqual(e.exception.code, 2)