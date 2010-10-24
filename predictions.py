""" Prediction client """
import sys
import os
import httplib2
from urllib import urlencode
import json
import getopt
from optparse import OptionParser
import time

#sys.path.append(os.path.join(os.path.dirname(__file__), 'third_party'))
CLIENT_LOGIN_URI = "https://www.google.com/accounts/ClientLogin"
TRAINING_URI = "https://www.googleapis.com/prediction/v1.1/training"

class Error200(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)    
    
    
class Prediction():
    def __init__(self, email, password, bucket, data):
        self.email = email
        self.password = password
        self.bucket = bucket
        self.data = data
        self.auth = None
        
        self.h = httplib2.Http(".cache")

    def auth_token(self):
        """ 
        Request auth token
        
        Return
            auth:   the auth token string
            None:   failure
        """
        headers = {"Content-Type":"application/x-www-form-urlencoded"}
        body =  {"accountType":"HOSTED_OR_GOOGLE", "Email":self.email,
                 "Passwd":self.password, "service":"xapi", "source":"account"}
        
        resp, content = self.h.request(CLIENT_LOGIN_URI, "POST", urlencode(body), headers=headers)
        
        # TODO shoudl this return an errno instead of raising an exception
        if resp["status"] != "200":
            raise Error200("200")
        
        try:
            i = content.rindex('Auth')
        except ValueError:
            print("Auth not found in content")
            authstring = content[i:].strip("\n")
            s_auth = authstring.split("=")
            self.auth = s_auth[1]
        

    def invoke_training(self):
        """
        Invoke training.
        
        Return
           http status code
        """
        headers = {"Content-Type":"application/json", 
                   "Authorization":"GoogleLogin auth={a}".format(a=self.auth)}
        body = '{data:{}}'
        my_training_uri = "{t}?data={b}%2F{d}".format(t=TRAINING_URI, b=self.bucket, 
                                                      d=self.data)
        
        resp, content = self.h.request(my_training_uri, "POST", body, headers=headers)
        return resp['status'] 


    def training_complete(self):
        """
        Return
            Accuracy as 0.xx, else -1.0
        """
        is_complete_uri="{tui}/{b}%2F{d}".format(tui=TRAINING_URI,
                                                 b=self.bucket,
                                                 d=self.data)
        headers = {"Authorization":"GoogleLogin auth={a}".format(a=self.auth)}
        resp, content = self.h.request(is_complete_uri, "GET", headers=headers)

        status = resp['status'] 
        if status != "200":
            # TODO Should this be -1
            return False

        #TODO Check the json
        #{"data":{
        #"data":"mybucket/mydata", "modelinfo":"Training hasn't completed."}}}
        return True

        # Json response
        # parse for  "modelinfo":"Training hasn't completed."
        # else
        # "modelinfo":"estimated accuracy: 0.xx"
        #{"data":{
        #"data":"mybucket/mydata", "modelinfo":"estimated accuracy: 0.xx"}}}
        # return accuracy or -1 if not complete

    def predict(self):
        pass
    #PREDICT
    # Format input as json
    # Invoke query with POSTpp
    # Parse json response

def main():
    usage = "%prog email password bucket data"
    parser = OptionParser(usage)
    parser.add_option("-D", "--debug", dest="debug", action="store_true",
                      help="Write debug to stdout.")
    
    [options, args] = parser.parse_args()
    if len(args) < 4:
        parser.error('Incorrect number of arguments')
        return -1
    else:
        email = args[0]
        password = args[1]
        bucket = args[2]
        data = args[3]
        
    debug = True if options.debug else False

    p = Prediction(email, password, bucket, data)

    try:
        p.auth_token()
    except ValueError:
        sys.stderr.write("auth_toke() failed")
        return 1

    status = p.invoke_training()
    if status != '200':
        sys.stderr.write("invoke_training returned: {s}".format(s=status))
        return 1

    try:
        while not p.training_complete():
            # TODO logging decorator
            if debug: print("Still training")
            time.sleep(30.0)
    except Error200 as e:
        print e
        return 1
    
    if debug: print("Training complete")


if __name__ == "__main__":
    sys.exit(main())