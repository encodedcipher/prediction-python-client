""" Prediction client """
import sys
import os
import httplib2
from urllib import urlencode
import json
import getopt
import time

#sys.path.append(os.path.join(os.path.dirname(__file__), 'third_party'))
CLIENT_LOGIN_URI = "https://www.google.com/accounts/ClientLogin"
TRAINING_URI = "https://www.googleapis.com/prediction/v1.1/training"

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
        
        # Check code status:200
        if resp["status"] != "200":
            print ('Response status code {sc}'.format(sc=resp["status"]))
            return None
        
        # ValueError if not found
        try:
            i = content.rindex('Auth')
        except ValueError:
            print("Auth not found in content")
            authstring = content[i:].strip("\n")
            s_auth = authstring.split("=")
            auth = s_auth[1]
        
        self.auth = auth


    def invoke_training(self):
        """
        Invoke training.
        """
        headers = {"Content-Type":"application/json", 
                   "Authorization":"GoogleLogin auth={a}".format(a=self.auth)}
        body = '{data:{}}'
        my_training_uri = "{t}?data={b}%2F{d}".format(t=TRAINING_URI, b=self.bucket, 
                                                      d=self.data)
        
        resp, content = self.h.request(my_training_uri, "POST", body, headers=headers)
        status = resp['status'] 
        print status
        if status != "200":
            return False
        
        return True


    def training_complete(self):
        """
        Args:
        bucket:   
        data:

        Return
            True if training is complete, else False
            """
        is_complete_uri="{tui}/{b}%2F{d}".format(tui=TRAINING_URI,
                                                 b=self.bucket,
                                                 d=self.data)
        headers = {"Authorization":"GoogleLogin auth={a}".format(a=self.auth)}
        resp, content = self.h.request(is_complete_uri, "GET", headers=headers)

        status = resp['status'] 
        if status != "200":
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

    def predict(self):
        pass
    #PREDICT
    # Format input as json
    # Invoke query with POSTpp
    # Parse json response

def main():
    # Command line args
    email="hancock.robert@gmail.com"
    password="w1ls0n1136"
    my_bucket="bobbuzz"
    my_data = "buzz.1287754348.5"
    #---------------

    p = Prediction(email, password, my_bucket, my_data)

    auth = p.auth_token()
    if not auth:
        return 1

    if not p.invoke_training():
        return 1

    while not p.training_complete():
        print("Still working")
        time.sleep(30.0)
    print("Training complete")


if __name__ == "__main__":
    sys.exit(main())