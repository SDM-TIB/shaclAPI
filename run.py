from flask import Flask, request, Response
import logging
from shaclapi import logger as shaclapi_logger

# Setup Logging
logging.getLogger('werkzeug').disabled = True

shaclapi_logger.setup(level=logging.ERROR)

logger = logging.getLogger(__name__)

import shaclapi.api as api

app = Flask(__name__)

@app.route("/multiprocessing", methods=['POST'])
def route_multiprocessing():
    '''
    Required Arguments:
        - query
        - targetShape
        - external_endpoint
        - schemaDir
    See app/config.py for a full list of available arguments!
    '''
    api_output = api.run_multiprocessing(request.form)
    if type(api_output) != str:
        return Response(api_output.to_json(), mimetype='application/json')
    else:
        return Response(api_output, mimetype='text/plain')

@app.route("/", methods=['GET'])
def hello_world():
    return "Hello World"

@app.route("/start", methods=['GET'])
def start_processes():
    api.start_processes()
    return "Done"

@app.route("/stop", methods=['GET'])
def stop_processes():
    api.stop_processes()
    return "Done"


@app.route("/restart", methods=['GET'])
def restart_processes():
    api.restart_processes()
    return "Done"


# Profiling Code
# from pyinstrument import Profiler
# global_request_count = 0

# def start_profiling():
#     g.profiler = Profiler()
#     g.profiler.start()

# def stop_profiling():
#     global global_request_count
#     g.profiler.stop()
#     output_html = g.profiler.output_html()
#     global_request_count = global_request_count + 1
#     with open("timing/api_profil{}.html".format(global_request_count - 1),"w") as f:
#         f.write(output_html)
