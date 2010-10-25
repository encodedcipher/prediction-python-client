""" Train a model. """
import sys
import getopt
from optparse import OptionParser

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    import prediction
except ImportError:
    print 'Error importing Prediction library!!'

def main():
    # TODO
    #verify bucket and data - boto?
    # make properties of some elements
    usage = "%prog email password bucket data"
    parser = OptionParser(usage)
    parser.add_option("-D", "--debug", dest="debug", action="store_true",
                      help="Write debug to stdout.")
    
    [options, args] = parser.parse_args()
    if len(args) < 4:
        parser.error('Incorrect number of arguments')
        return -1
    else:
        email = args[0]
        password = args[1]
        bucket = args[2]
        data = args[3]
        
    debug = True if options.debug else False

    p = Prediction(email, password, bucket, data)

    retval = p.fetch_auth_token()
    if retval["Status"] != "200":
        if retval.has_key("Error"):
            error = retval["Error"]
            #TODO What are the other errors?
            if Error == "CaptchaRequired":
                #TODO Deal with captcha
                #CaptchaToken=DQAAAGgA...dkI1LK9
                #CaptchaUrl=Captcha?ctoken=HiteT4b0Bk5Xg18_AcVoP6-yFkHPibe7O9EqxeiI7lUSN
                sys.stderr.write("captcha")
                return 1

    try:
        p.invoke_training()
    except HTTPError as e:
        sys.stderr.write("invoke_training returned: {ex}".format(ex=e))
        return 1
    

if __name__ == "__main__":
    sys.exit(main())