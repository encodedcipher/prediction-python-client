import sys
import os
import getopt
from optparse import OptionParser
import time


try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from prediction import Prediction
except ImportError:
    print 'Error importing Prediction library!!'

def main():
    usage = "%prog [-is] auth bucket data"
    parser = OptionParser(usage)
    parser.add_option("-D", "--debug", dest="debug", action="store_true",
                      help="Write debug to stdout.")
    parser.add_option("-i", "--iterations", dest="iterations", action="store",
                      help="Number of iterations to check if training is complete.")
    parser.add_option("-s", "--secs", dest="seconds", action="store",
                      help="Seconds to sleep between iterations")
    
    [options, args] = parser.parse_args()
    if len(args) < 4:
        parser.error('Incorrect number of arguments')
        return -1
    else:
        auth = args[0]
        bucket = args[1]
        data = args[2]
        
    debug = True if options.debug else False
    if options.iterations:
        iterations = int(options.iterations)
    else:
        iterations = 6
    #TODO not required if an auth
    p = Prediction(email, password, bucket, data)

    training_complete = False
    iteration = 1
    retval = None
    while not training_complete and iteration <= iterations:
        try:
            retval =  p.training_complete()
        except prediction.HTTPError as e:
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