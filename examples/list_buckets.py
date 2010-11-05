""" Return list of all buckets associated with this auth_token """
import sys
import os
import getopt
from optparse import OptionParser

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from prediction import Storage, HTTPError
except ImportError:
    sys.stderr.write('Error importing Prediction library!!')

def main():
    usage = "%prog [-D] auth_token"
    parser = OptionParser(usage)
    parser.add_option("-D", "--debug", dest="debug", action="store_true",
                      help="Write debug to stdout.")
    
    [options, args] = parser.parse_args()
    if len(args) < 1:
        parser.error('Incorrect number of arguments')
    else:
        auth_token = args[0]
        
    debug = True if options.debug else False

    s = Storage(auth_token)

    try:
        buckets = s.fetch_buckets()
    except HTTPError as e:
        sys.stderr.write("fetch_buckets: {ex}".format(ex=e))
        return 1
    
    for bucket in  buckets:
        print bucket

if __name__ == "__main__":
    sys.exit(main())