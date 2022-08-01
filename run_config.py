import argparse
import json
import logging
import sys
import time

import shaclapi.logger as shaclapi_logger
from shaclapi.api import run_multiprocessing

shaclapi_logger.setup(level=logging.DEBUG)

logger = logging.getLogger(__name__)


def main(pre_config):
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
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=json.loads)
    args = parser.parse_args()
    main(args.config)
