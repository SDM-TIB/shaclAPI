import getopt
import logging
import sys
import time

import shaclapi.logger as shaclapi_logger
from shaclapi.api import run_multiprocessing

shaclapi_logger.setup(level=logging.ERROR)

logger = logging.getLogger(__name__)


def get_options(argv):
    try:
        opts, args = getopt.getopt(argv, "h:c:q:t:s:")
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    config_file = None
    query = None
    test_name = None
    target_shape = None

    for opt, arg in opts:
        if opt == "-h":
            usage()
            sys.exit(0)
        elif opt == "-c":
            config_file = arg
        elif opt == "-q":
            query = "".join(open(arg, "r", encoding="utf8").readlines())
        elif opt == "-t":
            test_name = arg
        elif opt == "-s":
            target_shape = arg

    if not config_file or not query or not test_name or not target_shape:
        print("config:", eval(config_file))
        print("query:", eval(query))
        print("test_name:", eval(test_name))
        print("target_shape:", eval(target_shape))
        usage()
        sys.exit(1)

    config_dict_pre = {'config': config_file,
                       'query': query,
                       'targetShape': target_shape,
                       'test_identifier': test_name,
                       'run_in_serial': True}
    return config_dict_pre


def usage():
    usage_str = "Usage: {program} -c <config.json_file> -q <query_file> -t <test_name> -s <target_shape>\n Where: " \
                "<config.json_file> - path to config file\n" \
                "<query_file> - path to SPARQL query file\n" \
                "<test_name> - query name for stats\n" \
                "<target_shape> - name of the shape belonging to the query"
    print(usage_str.format(program=sys.argv[0]), )


def main(argv):
    pre_config = get_options(argv[1:])
    logger.info(pre_config)

    # Starting the processes of the runners
    try:
        api_output = run_multiprocessing(pre_config)
        time.sleep(1)
        if type(api_output) != str:
            print(api_output.to_json())
        else:
            print(api_output)
    except KeyboardInterrupt:
        print("SIGINT", file=sys.stderr)
        pass
    except Exception as e:
        print(e)
        pass


if __name__ == "__main__":
    main(sys.argv)
