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
    default_seconds = 30.0
    
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
  
    p = Prediction(auth_token, bucket, data)

    training_complete = False
    iteration = 1
    retval = None
    while not training_complete and iteration <= iterations:
        if debug: print("Iteration {i} of {x}".format(i=iteration,
                                                      x=iterations))        
        try:
            retval = p.training_complete()
        except HTTPError as e:
            sys.stderr.write(str(e))
            return 1
        
        if retval > -1:
            training_complete = True
            break
        
        if debug: print("Still training.  Sleeping {s} seconds.".format(s=seconds))
        time.sleep(seconds)
        iteration += 1
    
    if training_complete:
        print("Estimated accuracy: {a}".format(a=retval))
    else:
        print("Training hasn't completed.  retval={r}".format(r=retval))
        
        
if __name__ == "__main__":
    sys.exit(main())        