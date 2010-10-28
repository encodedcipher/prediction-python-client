import sys
import os
import getopt
from optparse import OptionParser
import time

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from prediction import Prediction, HTTPError
except ImportError:
    print 'Error importing Prediction library!'

def main():
    default_iterations = 6
    default_seconds = 30
    
    usage = "%prog [-Dis] auth_token bucket data"
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
    if len(args) < 3:
        parser.error('Incorrect number of arguments')
        return 1
    else:
        auth_token = args[0]
        bucket = args[1]
        data = args[2]
        
    debug = True if options.debug else False
    if options.iterations:
        try:
            iterations = int(options.iterations)
        except ValueError:
            sys.stderr.write("Cannot convert iteration argument {i} to int\n".format(i=options.iterations))
            return 1
    else:
        iterations = 6
        
    if options.seconds:
        try:
            seconds = float(options.seconds)
        except ValueError:
            sys.stderr.write("Cannot convert seconds argument {i} to float\n".format(i=options.seconds))
            return 1
    else:
        seconds = 30.0
  
            
    #TODO not required if an auth
    p = Prediction(auth_token, bucket, data)

    training_complete = False
    iteration = 1
    retval = None
    while not training_complete and iteration <= iterations:
        try:
            retval =  p.training_complete()
        except HTTPError as e:
            sys.stderr.write(e)
            return 1
        
        if ":" in retval:
            training_complete = True
        if debug: print("Still training, Iteration {i} of {x}".format(i=iteration,
                                                                      x=iterations))
        if options.seconds:
            time.sleep(float(options.seconds))
        else:
            time.sleep(30.0)
        iteration += 1
    
    if not retval:
        return 0
    elif "hasn't completed" in retval:
        print("Training hasn't completed")
    else:
        print("Estimated accuracy: {a}".format(a=retval))
        
if __name__ == "__main__":
    sys.exit(main())        