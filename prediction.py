""" Prediction client """
import sys
import os
from urllib import urlencode
import json
import getopt
from optparse import OptionParser
import time
try:
    import httplib2
except ImportError:
    sys.stderr.write("Please install httplib2.\n")
    sys.exit(1)
                     
    
CLIENT_LOGIN_URI = "https://www.google.com/accounts/ClientLogin"
TRAINING_URI = "https://www.googleapis.com/prediction/v1.1/training"

numerics = ('int', 'float', 'long', 'complex')

class HTTPError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)    
    
    
class Auth():
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.token = None
        self.http_status = None
        self.captcha = {}
        self.h = httplib2.Http(".cache")
        
        self._fetch_auth_token()
        
    def _fetch_auth_token(self):
        """ 
        Request auth token and set class var.
        
        Error
           403:    Poplulate self.captcha
        
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
            if status == "403":
                self.captcha["Error"] = content["Error"]
                if self.captcha["Error"] == "CaptchaRequired":
                    self.captcha["CaptchaToken"] = content["CaptchaToken"]
                    self.captcha["CaptchaUrl"] = content["CaptchaUrl"]
                
            raise HTTPError('HTTP status code: {s}'.format(s=self.http_status))
        
        try:
            i = content.rindex('Auth')
        except ValueError:
            raise ValueError("Auth not found in content")
        
        authstring = content[i:].strip("\n")
        s_auth = authstring.split("=")
        self.token = s_auth[1]
        

class Prediction():
    def __init__(self, auth, bucket, data):
        self.bucket = bucket
        self.data = data
        self.auth = None
        
        self.h = httplib2.Http(".cache")


    def invoke_training(self):
        """
        Invoke training. 
        
        Return
           http status code
        """
        headers = {"Content-Type":"application/json", 
                   "Authorization":"GoogleLogin auth={a}".format(a=self.auth)}
        body = '{data:{}}'
        training_uri = "{t}?data={b}%2F{d}".format(t=TRAINING_URI, b=self.bucket, 
                                                      d=self.data)
        
        resp, content = self.h.request(training_uri, "POST", body, headers=headers)
        status = resp["status"]
        if 'status' != "200":
            raise HTTPError('HTTP status code: {s}'.format(s=status))


    def training_complete(self):
        """
        Return: 
            "HTTP status code:  n"
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
        """ Delete a previously trained mode. """
        #-H "Authorization: GoogleLogin auth=auth-token"
        #https://www.googleapis.com/prediction/v1.1/training/mybucket%2Fmydata        
        pass
    
def main():

    try:
        p.invoke_training()
    except HTTPError as e:
        sys.stderr.write("invoke_training returned: {ex}".format(ex=e))
        return 1

    #TODO Maintain any type of state in a cookie? auth, bucket, data
    training_complete = False
    while not training_complete:
        retval =  p.training_complete()
        if ":" not in retval:
            training_complete = False
        if debug: print("Still training")
        time.sleep(30.0)
    
    if "HTTP" in retval:
        print("training_complete() returned HTTP status code: {c}".format(c=retval))
        return 1
    else:
        print("Estimated accuracy: {a}".format(a=retval))
        
    #invoke predictions
    try:
        retval = p.predict()
    except ValueError as e:
        sys.stderr.write("predict returned: {ex}".format(ex=e))


if __name__ == "__main__":
    sys.exit(main())