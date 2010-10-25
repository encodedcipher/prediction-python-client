def main():
    usage = "%prog auth bucket data"
    parser = OptionParser(usage)
    parser.add_option("-D", "--debug", dest="debug", action="store_true",
                      help="Write debug to stdout.")
    
    [options, args] = parser.parse_args()
    if len(args) < 4:
        parser.error('Incorrect number of arguments')
        return -1
    else:
        auth = args[0]
        bucket = args[1]
        data = args[2]
        
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

    #TODO Maintain any type of state in a cookie? auth, bucket, data
    training_complete = False
    while not training_complete:
        retval =  p.training_complete()
        if ":" not in retval:
            training_complete = False
        if debug: print("Still training")
        time.sleep(30.0)
    
    if "HTTP" in retval:
        print("training_complete() returned HTTP status code: {c}".format(c=retval))
        return 1
    else:
        print("Estimated accuracy: {a}".format(a=retval))
        