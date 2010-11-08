""" An example of the prediction process from beginning to end. 

We use the language file found at http://code.google.com/apis/predict/docs/language_id.txt
which is also included in the examples directory.

Prior to running this you have uploaded this file to the Google Storage location
that you specify on the command line with bucket and gsobject.
"""

import sys
import os
from optparse import OptionParser
import time

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    import prediction 
except ImportError:
    print 'Error importing Prediction library!!'

    
def main():
    default_iterations = 6
    default_seconds = 30
    usage = "%prog [-Dis] email password bucket gsobject"
    parser = OptionParser(usage)
    parser.add_option("-D", "--debug", dest="debug", action="store_true",
                      help="Write debug to stdout.")
    parser.add_option("-i", "--iterations", dest="iterations", action="store",
                      help="Number of iterations to check if training is complete.  "
                      + "Defalut is {i}.".format(i=default_iterations))
    parser.add_option("-s", "--secs", dest="seconds", action="store",
                      help="Seconds to sleep between iterations.  "
                      +"Default is {s}".format(s=default_seconds))    
    [options, args] = parser.parse_args()
    
    if len(args) < 4:
        parser.error('Incorrect number of arguments')
    else:
        email = args[0]
        password = args[1]
        bucket = args[2]
        gsobject = args[3]
    
    debug = True if options.debug else False
    if options.iterations:
        try:
            iterations = int(options.iterations)
        except ValueError:
            sys.stderr.write("Cannot convert iteration argument {i} to int\n".format(i=options.iterations))
            return 1
    else:
        iterations = default_iterations
    if debug: print("iterations={i}.".format(i=iterations))
        
    if options.seconds:
        try:
            seconds = float(options.seconds)
        except ValueError:
            sys.stderr.write("Cannot convert seconds argument {i} to float\n".format(i=options.seconds))
            return 1
    else:
        seconds = default_seconds
    if debug: print("seconds={s}".format(s=seconds))
      
    # Fetch auth token
    try:
        auth = prediction.Auth(email, password)
        auth_token = auth.fetch_token()
        if debug: print('Auth token: {t}'.format(t=auth_token))
    except prediction.HTTPError:
        if auth_token.captcha.get('CaptchaToken'):
            sys.stderr.write('Deal with captcha!')
        else:
            sys.stderr.write("Prediction http status code: {c}".format(c=auth.http_status))
            return 1
    except ValueError:
        print("Couldn't find the auth token in the HTTP response content.")        
        return 1
    
    # Get prediction object.
    p = prediction.Prediction(auth_token, bucket, gsobject)
    
    # Invoke training.
    try:
        p.invoke_training()
    except prediction.HTTPError as e:
        sys.stderr.write("invoke_training returned: {ex}".format(ex=e))
        return 1
    
    # Wait for training to complete.
    training_complete = False
    iteration = 1
    retval = None
    while not training_complete and iteration <= iterations:
        if debug: print("Iteration {i} of {x}".format(i=iteration,
                                                      x=iterations))        
        try:
            retval = p.training_complete()
        except prediction.HTTPError as e:
            sys.stderr.write(str(e))
            return 1
        
        if retval > -1:
            training_complete = True
            break
        
        if debug: print("Still training.  Sleeping {s} seconds.".format(s=seconds))
        time.sleep(seconds)
        iteration += 1
    
    if training_complete:
        if debug: print("Training complete: Estimated accuracy: {a}".format(a=retval))
    else:
        if debug: print("Training hasn't completed.  retval={r}".format(r=retval))
        return 1
        
    # Make a prediction.
    resp = p.predict("text", "Aujourd'hui, maman est morte. Ou peut-être hier, je ne sais pas.")
    print(resp)
    
if __name__ == "__main__":
    sys.exit(main())    