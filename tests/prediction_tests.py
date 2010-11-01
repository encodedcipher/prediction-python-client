import unittest
import sys
import os


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import prediction as p

class TestAuth(unittest.TestCase):

    def setUp(self):
        pass
        
    def test_bad_email(self):
        email = "bademail"
        password = "password"
        self.assertRaises(p.HTTPError, p.Auth, (email, password))
                          

if __name__ == "__main__":
    unittest.main()