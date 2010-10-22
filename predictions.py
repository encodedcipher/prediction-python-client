""" Prediction client """
import sys
import httplib2
from urllib import urlencode

CLIENT_LOGIN_URI = "https://www.google.com/accounts/ClientLogin"
TRAINING_URI = "https://www.googleapis.com/prediction/v1.1/training"

h = httplib2.Http(".cache")

#Request auth token
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


#Invoke training mehanism post
headers = {"Content-Type":"application/json", 
           "Authorization":"GoogleLogin auth={a}".format(a=auth)}
#START HERE - how should data be formatted - see curl example that works
data = {'data':{}}
# Append mybucket and mydata to URI
my_bucket="bobbuzz"
my_data = "buzz.1287716015.22"
my_training_uri = "{t}?data={b}%2F{d}".format(t=TRAINING_URI, b=my_bucket, 
                                              d=my_data)

resp, content = h.request(my_training_uri, "POST", urlencode(data), headers=headers)
  
print resp
  #https://www.googleapis.com/prediction/v1.1/training?data=mybucket%2F$mydata.