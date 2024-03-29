""" 
Fetch the authorization token using your Google account.  
    If you specify only your email and password a new auth token is returned.
    If you specify a .boto file and the token is in the file, the value in the file
    is returned.
    If you specify the keyword argument newtoken=True, a new token is generated,
    written to the .boto file, and returned.  This requires a valid value for botoconfig.
"""
import sys
import os
import getopt
from optparse import OptionParser
import traceback

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from prediction import Auth, HTTPError
except ImportError:
    print 'Error importing Prediction library!!'

usage = "%prog email password"
parser = OptionParser(usage)
[options, args] = parser.parse_args()
if len(args) < 2:
    parser.error('Incorrect number of arguments')
else:
    email = args[0]
    password = args[1]
        
try:
    
    auth = Auth(email, password)
    #auth = Auth(email, password, botoconfig="/home/rhancock/.boto")
    #auth = Auth(email, password, botoconfig="/home/rhancock/.boto", newtoken=True)
    token = auth.fetch_token()
    
    print('Auth token: {t}'.format(t=token))
    print('\nKeep this token.handy in case you want to reuse the session later!')
except HTTPError:
    if auth.captcha.get('CaptchaToken'):
        sys.stderr.write('Deal with captcha!')
    else:
        sys.stderr.write("Prediction http status code: {c}".format(c=auth.http_status))
except ValueError:
    print("Couldn't find the auth token in the HTTP response content.")
except:        
    print('-' * 50)
    traceback.print_exc()
    print('-' * 50)
    