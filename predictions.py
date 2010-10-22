""" Prediction client """
import sys
import os
import httplib2
from urllib import urlencode
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'third_party'))
try:
  # This is where simplejson lives on App Engine
  from django.utils import simplejson
except (ImportError):
  import simplejson


CLIENT_LOGIN_URI = "https://www.google.com/accounts/ClientLogin"
TRAINING_URI = "https://www.googleapis.com/prediction/v1.1/training"

h = httplib2.Http(".cache")

#REQUEST AUTH TOKEN
headers = {"Content-Type":"application/x-www-form-urlencoded"}
data =  {"accountType":"HOSTED_OR_GOOGLE", "Email":"hancock.robert@gmail.com",
  "Passwd":"w1ls0n1136", "service":"xapi", "source":"account"}

resp, content = h.request(CLIENT_LOGIN_URI, "POST", urlencode(data), headers=headers)

# Check code status:200
if resp["status"] != "200":
    print ('Response status code {sc}'.format(sc=resp["status"]))
    sys.exit(1)

# ValueError if not found
try:
    i = content.rindex('Auth')
except ValueError:
    print("Auth not found in content")
authstring = content[i:].strip("\n")
s_auth = authstring.split("=")
auth = s_auth[1]

print auth

#INVOKE TRAINING
headers = {"Content-Type":"application/json", 
           "Authorization":"GoogleLogin auth={a}".format(a=auth)}
data = '{data:{}}'
# Append mybucket and mydata to URI
my_bucket="bobbuzz"
my_data = "buzz.1287754348.5"
my_training_uri = "{t}?data={b}%2F{d}".format(t=TRAINING_URI, b=my_bucket, 
                                              d=my_data)

resp, content = h.request(my_training_uri, "POST", data, headers=headers)
  
print resp['status']


#IS TRAINING COMPLETE?
is_complete_uri="{tui}/{b}%2F{d}".format(tui=TRAINING_URI,
                                         b=my_bucket,
                                         d=my_data)
headers = {"Authorization":"GoogleLogin auth={a}".format(a=auth)}
resp, content = h.request(is_complete_uri, "GET", headers=headers)

status = resp['status'] 
if status != "200":
    print("Is training complete status = {s}".format(s=status))
    sys.exit()
    
# Json response
# parse for  "modelinfo":"Training hasn't completed."
# else
# "modelinfo":"estimated accuracy: 0.xx"
#{"data":{
   #"data":"mybucket/mydata", "modelinfo":"estimated accuracy: 0.xx"}}}
#PREDICT
# Format input as json
# Invoke query with POSTpp
# Parse json response