""" Prediction client """
import sys
import os
from urllib import urlencode
import json
import getopt
from optparse import OptionParser
import ConfigParser
import time

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
__version__ = "0.1g"
    
CLIENT_LOGIN_URI = "https://www.google.com/accounts/ClientLogin"
TRAINING_URI = "https://www.googleapis.com/prediction/v1.1/training"
numerics = ('int', 'float', 'long', 'complex')

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
    

class Auth():
    """ Google account authorization. """
    def __init__(self, email, password, botoconfig=""):
        """
        Args:
           email:            A valid Google email address.  e.g., kevin_dykstra@gmail.com
           password:         The Google account password.
           boto_config:      Name of the .boto file
        """
        self.email = email
        self.password = password
        self.boto_config = boto_config
        self.token = None
        self.http_status = None
        self.captcha = {}
        self.h = httplib2.Http(".cache")
        
        self._fetch_auth_token()
        if self.boto_config:
            self._write_boto_auth()
                
    def _write_boto_auth(self):
        """ If the boto config file exists, write the authorization
        token string to the Credentials section if this token is
        different from the one stored.
        """
        section = "Credentials"
        option = 'authorization'
        
        if not os.path.isfile(self.boto_config):
            raise OSError('Cannot find boto config file {f}'.format(f=self.boto_config))
        config = ConfigParser.RawConfigParser()
        config.readfp(open(self.boto_config))
        if config.has_option(section, option):
            auth = config.get(section, option)
        else:
            auth = None
        if auth == self.token:
            return
        
        config.set(section, option, self.token)
        with open(self.boto_config, 'w') as fh:
            config.write(fh)
            
    def _fetch_auth_token(self):
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
        self.token = s_auth[1]

        
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
        objects = self.storage.fetch_ojbects()
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
        TODO: Return -1.0 if not complete, else accuracy
        Return: 
            "Training hasn't completed"
            "estimated accuracy: 0.xx"
        """
        is_complete_uri="{tui}/{b}%2F{d}".format(tui=TRAINING_URI,
                                                 b=self.bucket,
                                                 d=self.data)
        headers = {"Authorization":"GoogleLogin auth={a}".format(a=self.auth)}
        resp, content = self.h.request(is_complete_uri, "GET", headers=headers)

        status = resp['status'] 
        if status != 200:
            raise HTTPError("HTTP status code: {s}".format(s=status))

        j = json.loads(content)
        modelinfo = j['data']['modelinfo']
        
        return modelinfo

    
    def predict(self, fmt, data):
        """
        Submit prediction
        """
        formats = ("text", "numeric", "mixture")
        if fmt not in formats:
            raise ValueError("format must be text, numeric, or mixture: {f}".format(f=fmt))

        #{"data":{"input" : {"text" : [ "myinput" ] }}}
        #{"data":{"input" : {"numeric" : [ 1, 10, 0 ] }}}
        #{"data":{"input" : {"mixture" : [ "text", 10, 0 ] }}}
        if fmt == 'text' and not isinstance(data, str):
            raise ValueError("text input must be of type string.")
        elif fmt == 'numeric' and type(data) not in numerics:
            raise ValueError('numeric input must be of type {n}'.format(n=numerics))

        jdata = json.dumps('"data":{"input" : {"{f}" : [ "{d}" ] }}}'.format(f=fmt,
                                                                             d=data))
    
        prediction_uri = "{t}?data={b}%2F{d}/predict".format(t=TRAINING_URI, 
                                                             b=self.bucket, 
                                                             d=self.data)
        headers = {"Content-Type":"application/application/json", 
                   "Authorization": "GoogleLogin auth=auth-token"}
        body = {}
        resp, content = self.h.request(prediction_uri, "POST", urlencode(body),
                                       headers=jdata)
        
        status = resp["status"]
        if 'status' != "200":
            raise HTTPError('HTTP status code: {s}'.format(s=status))
        
        #TODO Is it content or an element within content?
        return self._parse_prediction_json(content)
        
    
    def _parse_prediction_json(self, json):
        """
        Return a dictionary of just the pertinent data.
        #TODO Generic parsing of json - see Buzz
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
        
        if json.get('data').get('output'):
            output = json['data']['output']
        elif json.get('data').get('kind'):
            output = json['data']
            
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
        