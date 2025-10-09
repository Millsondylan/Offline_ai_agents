import unittest
from hello import hello_world

class TestHelloWorld(unittest.TestCase):
    def test_hello_world(self):
        self.assertIsNone(hello_world())
