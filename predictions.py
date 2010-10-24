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
                     
    
#sys.path.append(os.path.join(os.path.dirname(__file__), 'third_party'))
CLIENT_LOGIN_URI = "https://www.google.com/accounts/ClientLogin"
TRAINING_URI = "https://www.googleapis.com/prediction/v1.1/training"
#QUERY_URI="https://www.googleapis.com/prediction/v1.1/query/"

class HTTPError(Exception):
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

    def fetch_auth_token(self):
        """ 
        Request auth token
        
        Return
            auth:   the auth token string
            
        If it fails, should it return a dict of data
        """
        headers = {"Content-Type":"application/x-www-form-urlencoded"}
        body =  {"accountType":"HOSTED_OR_GOOGLE", "Email":self.email,
                 "Passwd":self.password, "service":"xapi", "source":"account"}
        
        resp, content = self.h.request(CLIENT_LOGIN_URI, "POST", urlencode(body), headers=headers)
        
        status = resp["status"]
        #TODO
        # Raise an exception or return the verification data in a dict
        if status != "200":
            if status == "403":
                #TODO deal with captcha user interface
                error_text = content["Error"]
                if error_text == "CaptchaRequired":
                    captcha_token = content["CaptchaToken"]
                    captcha_url = content["CaptchaUrl"]
                    #HTTP/1.0 403 Access Forbidden
                    #Server: GFE/1.3
                    #Content-Type: text/plain
	
                    #Url=http://www.google.com/login/captcha
                    #Error=CaptchaRequired
                    #CaptchaToken=DQAAAGgA...dkI1LK9
                    #CaptchaUrl=Captcha?ctoken=HiteT4b0Bk5Xg18_AcVoP6-yFkHPibe7O9EqxeiI7lUSN
                else:
                    status_text = "{s}: {t}".format(s=status, t=text)
            raise HTTPError('HTTP status code: {s}'.format(s=status_text))
        
        try:
            i = content.rindex('Auth')
        except ValueError:
            raise ValueError("Auth not found in content")
        
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

    def format_prediction_request(self):
        pass
    
    
    def predict(self):
        pass
    #PREDICT
    # Format input as json
    # Invoke query with POSTpp
    # Parse json response

    def delete_model(self):
        """ Delete a previously trained mode. """
        pass
    
def main():
    # TODO
    #verify bucket adn data - boto?
    # make properties of some elements
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
        p.fetch_auth_token()
    except (HTTPError, ValueError) as e:
        sys.stderr.write("auth_token() :{ex}".format(ex=e))
        return 1

    try:
        p.invoke_training()
    except HTTPError as e:
        sys.stderr.write("invoke_training returned: {ex}".format(ex=e))
        return 1

    # TODO Maintain any type of state in a cookie?
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
        
    


if __name__ == "__main__":
    sys.exit(main())