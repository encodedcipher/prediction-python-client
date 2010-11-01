""" Fetch auth token. """
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
    #auth = Auth(email, password, boto_config="/usr/local/src/prediction-python-client/.boto")
            
    print('Auth token: {t}'.format(t=auth.token))
    print('\nKeep this token.handy in case you want to reuse the session later!')
except HTTPError:
    if auth.captcha.get('CaptchaToken'):
        print('Deal with captcha!')
    else:
        print("Prediction http status code: {c}".format(c=auth.http_status))
except ValueError:
    print("Couldn't find the auth token in the HTTP response content.")
except:        
    print('-' * 50)
    traceback.print_exc()
    print('-' * 50)
    