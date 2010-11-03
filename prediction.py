""" Prediction client """
import sys
import os
from urllib import urlencode
import json
import getopt
from optparse import OptionParser
import ConfigParser
import time
import shutil

try:
    import boto
except ImportError:
    sys.stderr.write("Please install the boto library.")
    sys.exit(1)
                     
try:
    import httplib2
except ImportError:
    sys.stderr.write("Please install httplib2.\n")
    sys.exit(1)
                     
__author__ = ('hancock.robert@gmail.com (Robert Hancock)')
__version__ = "0.1a"
    
CLIENT_LOGIN_URI = "https://www.google.com/accounts/ClientLogin"
TRAINING_URI = "https://www.googleapis.com/prediction/v1.1/training"
NUMERICS = (int, float, long, complex)

class HTTPError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)    

class StorageError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)    

class TrainingError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)     

class Auth():
    """ Google account authorization for Google Storage. """
    def __init__(self, email, password, botoconfig="", newtoken=False):
        """
        Args:
           email:            A valid Google email address.  e.g., kevin_dykstra@gmail.com
           password:         The Google account password.
           botoconfig:       If auth_token exists in this file, return it
                             else: get a new token, write it to the file, and return it.
           newtoken:         If true, writes a new token to the .boto file.
        """
        self.email = email
        self.password = password
        self.boto_config = botoconfig
        if not isinstance(newtoken, bool):
            raise ValueError("Keyword argument newtoken must be type boolean: {e}".format(type(newtoken)))
        else:
            self.newtoken = newtoken
        self.auth_token = None
        self.http_status = None
        self.captcha = {}
        self.section = "Credentials"
        self.option = 'authorization'
        self.h = httplib2.Http(".cache")
        
    def fetch_token(self):
        if self.boto_config:
            if not os.path.isfile(self.boto_config):
                raise OSError("Cannot find {b}".format(b=self.boto_config))
            else:
                self.config = ConfigParser.RawConfigParser()
                self.config.readfp(open(self.boto_config))
                if not self.newtoken:
                    self._fetch_boto_auth()
        
        if not self.auth_token:
            self._fetch_new_auth_token()
            if self.boto_config:
                self._write_boto_auth()
        
        return self.auth_token
        
                
    def _fetch_boto_auth(self):
        if self.config.has_option(self.section, self.option):
            self.auth_token = self.config.get(self.section, self.option)
        else:
            self.auth_token = None
        
    def _write_boto_auth(self):
        """ If the boto config file exists, write the authorization
        token string to the Credentials section if this token is
        different from the one stored.
        
        N.B. When the config writes to file is does not preserver comments
        in the file.  Therefore, it is backed up with the name:
        canoncial_filename.nonce, where nonce is the current time in epoch seconds.
        """
        self.config.set(self.section, self.option, self.auth_token)
        path, fname = os.path.split(self.boto_config)
        boto_backup = os.path.join(path, "{f}.{x}".format(f=fname,x=time.time()))
        shutil.copyfile(self.boto_config, boto_backup)
        
        with open(self.boto_config, 'w') as fh:
            self.config.write(fh)
            
    def _fetch_new_auth_token(self):
        """ 
        Request auth token and set class var.
        
        Error
           403:    Deal with self.captcha
        
        Return
            A dictonary with keys
            Status - HTTP status code (required)
            Error - 
            
        If it fails, should it return a dict of data?
        """
        retval = {"Status":""}
        headers = {"Content-Type":"application/x-www-form-urlencoded"}
        body =  {"accountType":"HOSTED_OR_GOOGLE", "Email":self.email,
                 "Passwd":self.password, "service":"xapi", "source":"account"}
        
        resp, content = self.h.request(CLIENT_LOGIN_URI, "POST", urlencode(body),
                                       headers=headers)
        
        self.http_status = resp["status"]
        #TODO
        # Raise an exception or return the verification data in a dict
        if self.http_status != "200":
            #if self.http_status == "403":
                # Bad Authentication
                #self.captcha["Error"] = content["Error"]
                #if self.captcha["Error"] == "CaptchaRequired":
                    #self.captcha["CaptchaToken"] = content["CaptchaToken"]
                    #self.captcha["CaptchaUrl"] = content["CaptchaUrl"]
                
            raise HTTPError('HTTP status code: {s}'.format(s=self.http_status))
        
        try:
            i = content.rindex('Auth')
        except ValueError:
            raise ValueError("Auth not found in content")
        
        authstring = content[i:].strip("\n")
        s_auth = authstring.split("=")
        self.auth_token = s_auth[1]

        
class Storage():
    def __init__(self, auth_token):
        self.auth_token = auth_token
        self.h = httplib2.Http(".cache")

    def fetch_buckets(self):
        """
        N.B. The boto library requires your auth token to be in the .boto 
        configuration file.
        Example:
            [Credentials]
            authorization = DQAAAK8AAACdOpX9GMAPb7MIPIb
        
        Return:
            A list of all bucket names. """
        config = boto.config
        uri = boto.storage_uri("", "gs")
        buckets = uri.get_all_buckets()
        
        return [b.name for b in buckets]
    
    def fetch_ojbects(self, bucket):
        uri = boto.storage_uri(bucket, "gs")

        #"List your objects."
        objects = uri.get_bucket()
        return [obj.name for obj in objects]
                

class Prediction():
    """ Fuctions for training, status, predictionm and deletion.

    N.B.   You need have defined the bucket and data prior to this.
    """
    def __init__(self, auth, bucket, data):
        self.bucket = bucket
        self.data = data
        self.auth = auth
        self.h = httplib2.Http(".cache")
        self.storage = Storage(self.auth)

        if not self._bucket_exists():
            raise StorageError("Cannot find {b} in Google Storage.".format(b=self.bucket))
            
        if not self._data_exists():
            raise StorageError("Cannot find {d} in bucket {b}.".format(d=self.data,
                                                                       b=self.bucket))

    def _bucket_exists(self):
        buckets =  self.storage.fetch_buckets()
        return self.bucket in buckets
    
    def _data_exists(self):
        objects = self.storage.fetch_ojbects(self.bucket)
        return self.data in objects
            
    def invoke_training(self):
        """
        Start training from data in bucket/data.
        """
        headers = {"Content-Type":"application/json", 
                   "Authorization":"GoogleLogin auth={a}".format(a=self.auth)}
        body = '{data:{}}'
        training_uri = "{t}?data={b}%2F{d}".format(t=TRAINING_URI, b=self.bucket, 
                                                      d=self.data)
        
        resp, content = self.h.request(training_uri, "POST", body, headers=headers)
        status = resp["status"]
        if status != "200":
            raise HTTPError('HTTP status code: {s}'.format(s=status))

    def training_complete(self):
        """   
        Return: 
            -1.0:    Training hasn't completed
            0.xxx     estimated accuracy: 0.xx
        """
        is_complete_uri="{tui}/{b}%2F{d}".format(tui=TRAINING_URI,
                                                 b=self.bucket,
                                                 d=self.data)
        headers = {"Authorization":"GoogleLogin auth={a}".format(a=self.auth)}
        resp, content = self.h.request(is_complete_uri, "GET", headers=headers)

        status = resp['status'] 
        if status != '200' and status != '304':
            raise HTTPError("HTTP status code: {s}".format(s=status))

        j = json.loads(content)
        modelinfo = j['data']['modelinfo']

        if "estimated" in modelinfo:
            buf = modelinfo.split(":")
            if len(buf) > 1:
                return float(buf[1])
            else:
                raise TrainingError("modelinfo format error: {m}".format(m=modelinfo))
            
        if "hasn't" in modelinfo:
            return -1.0
        else:
            raise TrainingError('modelinfo={m}'.format(m=modelinfo))
               
    def predict(self, fmt, pdata):
        """
        Submit prediction
        """
        formats = ("text", "numeric", "mixture")
        if fmt not in formats:
            raise ValueError("Format must be text, numeric, or mixture.  You passed: '{f}'".format(f=fmt))

        #{"data":{"input" : {"text" : [ "myinput" ] }}}
        #{"data":{"input" : {"numeric" : [ 1, 10, 0 ] }}}
        #{"data":{"input" : {"mixture" : [ "text", 10, 0 ] }}}
        if fmt == 'text' and not isinstance(pdata, str):
            raise ValueError("You specifided the format as 'text' but data is {t}.".format(t=type(pdata)))
        elif fmt == 'numeric' and not isinstance(pdata, NUMERICS):
            raise ValueError('numeric input must be of type {n}'.format(n=NUMERICS))

        #jdata = json.dumps('{"data":{"input" : {\"{f}\" : [ \"{d}\" ] }}}'.format(f=fmt,d=pdata))
        jdata = json.dumps({"data": {"input" : {fmt : [ pdata ]}}})
    
        prediction_uri = "{t}?data={b}%2F{d}/predict".format(t=TRAINING_URI, 
                                                             b=self.bucket, 
                                                             d=self.data)
        headers = {"Content-Type":"application/json", 
                   "Authorization":"GoogleLogin auth={a}".format(a=self.auth)}
        #body = {}
        resp, content = self.h.request(prediction_uri, "POST", jdata,
                                       headers=headers)
        
        status = resp["status"]
        if status != "200":
            raise HTTPError('HTTP status code: {s}'.format(s=status))
        
        #TODO Is it content or an element within content?
        jcontent = json.loads(content)
        return self._parse_prediction_json(jcontent)
        
    
    def _parse_prediction_json(self, json):
        """
        Return a dictionary of just the pertinent data.
        # Categorical
        #{"data":{"output":{"kind":"prediction#output",
                 #"outputLabel":"topLabel"
                 #"outputMulti":[{"label":"value", "score":x.xx}
                                 #{"label":"value", "score":x.xx}
                                 #...]}}
        #Regression
        #{"data":{"kind":"prediction#output", "outputValue":"x.xx"}}
        """
        if not isinstance(json, dict):
            raise TypeError(
                'Expected dict as arg but received %s: %s' % type(json), 
                json)
        
        if json.get('data'):
            output = json['data']
        else:
            output = {"Error": json}
            
        return output
            

    def delete_model(self):
        """ Delete a model. """
        prediction_uri = "{t}?data={b}%2F{d}/predict".format(t=TRAINING_URI, 
                                                             b=self.bucket, 
                                                             d=self.data)        
        headers = {"Authorization": "GoogleLogin auth=auth-token"}
        body = {}
        resp, content = self.h.request(prediction_uri, "DELETE", urlencode(body),
                                       headers=headers)
        status = resp["status"]
        if 'status' != "200":
            raise HTTPError('HTTP status code: {s}'.format(s=status))
        