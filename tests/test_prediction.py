""" Unit tests for Prediction Python Client 

Some of these are more functional tests.

"""
import unittest
import sys
import os
import time
import random

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import prediction as p

#------START--- Change to your valid entries -----------
#good_email = "youremai@gmail.com"
#good_password = "yourpassword"
#good_boto_config = "/home/you/.boto"
# This bucket and object must exist.
good_bucket = "utest"
good_object = "small"
#------STOP--- Change to your valid entries -----------


def nonce():
    random.seed(time.time())
    s = str(random.random())
    ss = s.split('.')
    return ss[1]

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.bad_email = "bademail"
        self.bad_password = "password"  

    def test_good_email_password(self):
        a = p.Auth(good_email, good_password)
        token = a.fetch_token()
        self.assertEquals(type(token), str)

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

    def test_bad_newtoken(self):
        try:
            a = p.Auth(good_email, good_password, botoconfig=good_boto_config, newtoken="notbool")
        except Exception as e:
            self.assertEqual(type(e), ValueError)


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.a = p.Auth(good_email, good_password).fetch_token()
        self.s = p.Storage(self.a)
        self.buckets = self.s.fetch_buckets()
        self.s_bad = p.Storage('bad_auth')

        self.create_bucket_name = "test_storage_create_bucket"+str(nonce())
        self.test_bucket = 'test_storage'+nonce()
        self.s.create_bucket(self.test_bucket)
        self.delete_me_bucket = "test_storage_dummy"+str(nonce())
        self.s.create_bucket(self.delete_me_bucket)

        self.test_file = "test_file_{n}".format(n=nonce())

        with open(self.test_file, 'w') as fh:
            fh.write("French, Je suis le roi\n")
            fh.write("Italian, Sono il re\n")
            fh.write("English, I am the King\n")

    def tearDown(self):
        if os.path.isfile(self.test_file):
            os.remove(self.test_file)
            
        buckets = self.s.fetch_buckets()
        for bucket in buckets:
            if bucket.startswith("test"):
                objs = self.s.fetch_objects(bucket)
                if objs:
                    for obj in objs:
                        self.s.delete_object(bucket, obj)
                self.s.delete_bucket(bucket)

    def test_fetch_buckets(self):
        res = self.s.fetch_buckets()
        self.assertEquals(type(res), list)
        
    def test_fetch_buckets_bad(self):
        self.assertRaises(Exception, self.s_bad.fetch_buckets, ())

    def test_fetch_objects(self):
        res = self.s.fetch_objects(self.buckets[0])
        self.assertEquals(type(res),list)

    def test_fetch_objects_bad(self):
        self.assertRaises(Exception, self.s.fetch_objects, ('bad_bucket'))

    def test_create_bucket(self):
        self.s.create_bucket(self.create_bucket_name)
        buckets = self.s.fetch_buckets()
        self.assertTrue(self.create_bucket_name in buckets)

    def test_delete_bucket(self):
        self.s.delete_bucket(self.delete_me_bucket)
        buckets = self.s.fetch_buckets()
        self.assertTrue(self.delete_me_bucket not in buckets)

    def test_upload_file(self):
        self.s.upload_file(self.test_bucket,self.test_file)
        objects = self.s.fetch_objects(self.test_bucket)
        self.assertTrue(self.test_file in objects)

class TestPrediction(unittest.TestCase):
    def setUp(self):
        global boto_config
        self.auth = p.Auth(good_email, good_password, good_boto_config)
        self.token = self.auth.fetch_token()
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
            pred = p.Prediction(self.token, self.bad_bucket, good_object)
        except Exception as e:
            self.assertEqual(type(e), p.StorageError)

    def test_auth_bad_object(self):
        try:
            pred = p.Prediction(self.token, good_bucket, self.bad_object)
        except Exception as e:
            self.assertEqual(type(e), p.StorageError)

class TestPredict(unittest.TestCase):
    def setUp(self):
        global p
        self.bad_fmt = "badformat"
        self.test_data = "test data"
        self.auth = p.Auth(good_email, good_password)
        self.token = self.auth.fetch_token()
        self.pred = p.Prediction(self.token, good_bucket, good_object)

        # Create bucket and object for delete model test
        self.bucketname = "test_predict_dummy_bucket"+str(nonce())
        #self.objectname = "test_object_{n}".format(n=self.bucketname)
        self.test_file = "test_file_{n}".format(n=nonce())

        with open(self.test_file, 'w') as fh:
            fh.write("French, Je suis le roi\n")
            fh.write("Italian, Sono il re\n")
            fh.write("English, I am the King\n")

        self.auth = p.Auth(good_email, good_password).fetch_token()
        self.s = p.Storage(self.auth)

        self.s.create_bucket(self.bucketname)
        self.s.upload_file(self.bucketname, self.test_file)
        # TODO Training time is always exceeded.
        #this_p = p.Prediction(self.auth, self.bucketname, self.test_file)
        #training_complete = False
        #max_secs = 60
        #start_time = time.time()
        #while not training_complete:
            #try:
                #this_p.training_complete()
            #except p.TrainingError:
                #if (time.time() - start_time) > 60:
                    #print("Max training time exceeded.")
                    #sys.exit()
                    
                #time.sleep(2)

    def tearDown(self):
        if os.path.isfile(self.test_file):
            os.remove(self.test_file)

        buckets = self.s.fetch_buckets()
        for bucket in buckets:
            if bucket.startswith("test"):
                objs = self.s.fetch_objects(bucket)
                if objs:
                    for obj in objs:
                        self.s.delete_object(bucket, obj)
                self.s.delete_bucket(bucket)


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

    ## To do
    ##def test_predict_good(self):
        ##pass

    #def test_delete_model(self):
        #p = p.Prediction(self.auth, self.bucketname, self.objectname)
        #p.delete_model()
        #buckets = self.s.fetch_buckets()

    ##def test_delete_model_bad(self):
        ##pass


if __name__ == "__main__":
    unittest.main()