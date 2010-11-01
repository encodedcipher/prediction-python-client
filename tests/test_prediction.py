""" Unit tests for Prediction Python Client 

Some of these are more functional tests.

"""
import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import prediction as p

#------START--- Change to your valid entries -----------
good_email = "hancock.robert@gmail.com"
good_password = "w1ls0n1136"
boto_config = "/home/rhancock/.boto"
good_bucket = "utest"
good_object = "small"
#------STOP--- Change to your valid entries -----------

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
            a = p.Auth(good_email, good_password, botoconfig="badfile")
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
        self.assertEquals(type(res), list)

    def test_fetch_buckets_bad(self):
        self.assertRaises(Exception, self.s_bad.fetch_buckets, ())
        
    def test_fetch_objects(self):
        res = self.s.fetch_ojbects(self.buckets[0])
        self.assertEquals(type(res),list)
        
    def test_fetch_objects_bad(self):
        self.assertRaises(Exception, self.s.fetch_ojbects, ('bad_bucket'))
        
class TestPrediction(unittest.TestCase):
    def setUp(self):
        global boto_config
        self.auth = p.Auth(good_email, good_password, boto_config)
        self.bad_auth = 'badauth'
        self.bad_bucket = "badbucket"
        self.bad_object = "baddata"
        
    def test_auth_bad_auth(self):
        try:
            pred = p.Prediction(self.bad_auth, good_bucket, good_object)
        except Exception as e:
            self.assertEqual(type(e), TypeError)
    
    def test_auth_bad_bucket(self):
        try:
            pred = p.Prediction(self.auth.token, self.bad_bucket, good_object)
        except Exception as e:
            self.assertEqual(type(e), p.StorageError)
            
    def test_auth_bad_object(self):
        try:
            pred = p.Prediction(self.auth.token, good_bucket, self.bad_object)
        except Exception as e:
            self.assertEqual(type(e), p.StorageError)
            
class TestPredict(unittest.TestCase):
    def setUp(self):
        self.bad_fmt = "badformat"
        self.test_data = "test data"
        self.auth = p.Auth(good_email, good_password)
        self.pred = p.Prediction(self.auth.token, good_bucket, good_object)
        
    def test_predict_bad_format(self):
        try:
            self.pred.predict(self.bad_fmt, self.test_data)
        except Exception as e:
            self.assertEqual(type(e), ValueError)
            
    def test_predict_bad_data(self):
        try:
            self.pred.predict("text", 666.0)
        except Exception as e:
            self.assertEqual(type(e), ValueError)
    
        try:
            self.pred.predict("numeric", "string")
        except Exception as e:
            self.assertEqual(type(e), ValueError)
            
    def test_predict_good(self):
        
            
    
        
                         
if __name__ == "__main__":
    unittest.main()