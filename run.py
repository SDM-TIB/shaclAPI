from flask import Flask, request, Response
import logging
from shaclapi import logger as shaclapi_logger

from shaclapi.config import Config
from multiprocessing import Queue
from shaclapi.reduction.ValidationResultTransmitter import ValidationResultTransmitter
from shaclapi.reduction import prepare_validation
from shaclapi.query import Query
from shaclapi.api import unify_target_shape

# Setup Logging
# Use for debugging:
# shaclapi_logger.setup(level=logging.DEBUG, handler=logging.FileHandler('/shaclAPI/examples/api.log'))
# logging.getLogger('werkzeug').disabled = True
# Use for production:
shaclapi_logger.setup(level=logging.INFO)

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

@app.route("/validation", methods=['POST'])
def route_validation():
    """Use the heuristics implemented and activated in the given configuration, to run the validation over the reduced SHACL shape schema. Only returns the number of valid and invalid instances.

    Returns
    -------
    flask.Response
        The response containing the validation results.
    """
    config = Config.from_request_form(request.form)
    queue = Queue()
    result_transmitter = ValidationResultTransmitter(output_queue=queue)

    query = Query.prepare_query(config.query)
    query_starshaped = query.make_starshaped()
    config.target_shape = unify_target_shape(config.target_shape, query_starshaped)

    shape_schema = prepare_validation(config, Query(config.query), result_transmitter)
    shape_schema.validate(config.start_with_target_shape)
    queue.put('EOF')

    val_results = {}
    item = queue.get()
    while item != 'EOF':
        instance = item['instance']
        val_shape = item['validation'][0]
        val_res = item['validation'][1]

        if val_shape not in val_results:
            val_results[val_shape] = {'valid': 0, 'invalid': 0}
        val_results[val_shape]['valid' if val_res else 'invalid'] += 1
        item = queue.get()
    queue.close()
    queue.cancel_join_thread()
    return val_results

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
