import unittest
import sys
import os


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import prediction as p
good_email = "hancock.robert@gmail.com"
good_password = "w1ls0n1136"

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.bad_email = "bademail"
        self.bad_password = "password"  
        
    def test_good_email_password(self):
        a = p.Auth(good_email, good_password)
        self.assertEquals(a.http_status, "200")
        
    def test_bad_creds(self):
        # assertRaises does not work with init and optional arg
        try:
            a = p.Auth(self.bad_email, good_password)
        except Exception as e:
            self.assertEqual(type(e), p.HTTPError)
            
    def test_bad_boto(self):
        try:
            a = p.Auth(good_email, good_password, boto_config="badfile")
        except Exception as e:
            self.assertEqual(type(e), OSError)
 
class TestStorage(unittest.TestCase):
    def setUp(self):
        self.a = p.Auth(good_email, good_password)
        self.s = p.Storage(self.a)
        self.buckets = self.s.fetch_buckets()
        
        self.s_bad = p.Storage('bad_auth')
                          
    def test_fetch_buckets(self):
        res = self.s.fetch_buckets()
        self.assertIsInstance(res, list)

    def test_fetch_buckets_bad(self):
        self.assertRaises(Exception, self.s_bad.fetch_buckets, ())
        
    def test_fetch_objects(self):
        res = self.s.fetch_ojbects(self.buckets[0])
        self.assertIsInstance(res, list)
        
    def test_fetch_objects_bad(self):
        self.assertRaises(Exception, self.s.fetch_ojbects, ('bad_bucket'))
        
if __name__ == "__main__":
    unittest.main()