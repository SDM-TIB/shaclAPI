import app.log_utils.logger_init # Has to be the first import!
import time, sys, logging, argparse
from api import run_multiprocessing, stop_processes
from functools import reduce
import json

# Use to reproduce calls to the api.

logger = logging.getLogger(__name__)

def main(pre_config):
    # Starting the processes of the runners
    try:
        api_output, config = run_multiprocessing(pre_config)
        time.sleep(1)
        if type(api_output) != str:
            print(api_output.to_json(config.target_shape))
        else:
            print(api_output)
    except KeyboardInterrupt:
        print("SIGINT", file=sys.stderr)
        pass
    except Exception as e:
        print(e)
        pass
    finally:
        stop_processes()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=json.loads)
    args = parser.parse_args()
    main(args.config)
