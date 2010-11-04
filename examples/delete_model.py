""" Delete a model. """
import sys
import os
import getopt
from optparse import OptionParser

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from prediction import Prediction, HTTPError, NotFoundError
except ImportError:
    print 'Error importing Prediction library!!'

def main():
    usage = "%prog auth_token bucket data"
    parser = OptionParser(usage)
    
    [options, args] = parser.parse_args()
    if len(args) < 3:
        parser.error('Incorrect number of arguments')
        return -1
    else:
        auth_token = args[0]
        bucket = args[1]
        data = args[2]
        
    p = Prediction(auth_token, bucket, data)
    
    try:
        p.delete_model()
    except (NotFoundError, HTTPError) as e:
        print e
        return 1
        
    print("Deleted bucket:{b}, object:{o}".format(b=bucket, o=data))
    
if __name__ == "__main__":
    sys.exit(main())