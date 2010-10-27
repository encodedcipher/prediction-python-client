""" Delete a model. """
import sys
import os
import getopt
from optparse import OptionParser

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from prediction import Prediction, HTTPError
except ImportError:
    print 'Error importing Prediction library!!'

def main():
    # TODO
    #verify bucket and data - boto?
    # make properties of some elements
    usage = "%prog auth_token bucket data"
    parser = OptionParser(usage)
    parser.add_option("-D", "--debug", dest="debug", action="store_true",
                      help="Write debug to stdout.")
    
    [options, args] = parser.parse_args()
    if len(args) < 3:
        parser.error('Incorrect number of arguments')
        return -1
    else:
        auth_token = args[0]
        bucket = args[1]
        data = args[2]
        
    debug = True if options.debug else False

    p = Prediction(auth_token, bucket, data)
    
    p.delete_model
    
#An empty response is returned if a model exists and is successfully deleted, 
#and a 400 error if the model does not exist