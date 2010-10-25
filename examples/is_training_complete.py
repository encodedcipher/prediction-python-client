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
        