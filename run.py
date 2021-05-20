from flask import Flask, request, Response
import time, logging, json, sys

import api
import app.colors as Colors

# Setup Logging
logging.getLogger('werkzeug').disabled = True
logging.basicConfig(filename="api.log", filemode='a', format="[%(asctime)s - %(levelname)s] %(name)s - %(processName)s: %(msg)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/endpoint", methods=['GET', 'POST'])
def endpoint():
    '''
    This is just an proxy endpoint to log the communication between the backend and the external sparql endpoint.
    '''
    api.EXTERNAL_SPARQL_ENDPOINT
    logger.debug(Colors.headline('Received /endpoint request'))
    # Preprocessing of the Query
    if request.method == 'POST':
        query = request.form['query']
    if request.method == 'GET':
        query = request.args['query']

    logger.debug("Received Query: ")
    logger.debug(query)

    start = time.time()
    api.EXTERNAL_SPARQL_ENDPOINT.setQuery(query)
    result = api.EXTERNAL_SPARQL_ENDPOINT.query().convert()
    jsonResult = json.dumps(result)
    end = time.time()

    logger.debug("Got {} result bindings".format(len(result['results']['bindings'])))
    logger.debug("Execution took " + str((end - start)*1000) + ' ms')
    logger.debug(Colors.headline(''))

    return Response(jsonResult, mimetype='application/json')

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
    api_output, config = api.run_multiprocessing(request.form)
    if type(api_output) != str:
        return Response(api_output.to_json(config.target_shape), mimetype='application/json')
    else:
        return api_output

@app.route("/singleprocessing", methods=['POST'])
def run():
    '''
    ONLY COMPATIBLE WITH TRAVSHACL BACKEND!

    Required Arguments:
        - query
        - targetShape
        - external_endpoint
        - schemaDir
    See app/config.py for a full list of available arguments!
    '''
    api_output, config = api.run_singleprocessing(request.form)
    if config.output_format == "test":
        return Response(api_output.to_json(config.target_shape), mimetype='application/json')
    else:
        return Response(str(api_output))

@app.route("/", methods=['GET'])
def hello_world():
    return "Hello World"

@app.route("/start", methods=['GET'])
def start_processes():
    return api.start_processes()

@app.route("/stop", methods=['GET'])
def stop_processes():
    return api.stop_processes()

@app.route("/restart", methods=['GET'])
def restart_processes():
    return api.restart_processes()

# Profiling Code
# from pyinstrument import Profiler
# global_request_count = 0

# def start_profiling():
#     g.profiler = Profiler()
#     g.profiler.start()
#     print(Colors.magenta(Colors.headline('New Validation Task')))

# def stop_profiling():
#     global global_request_count
#     g.profiler.stop()
#     output_html = g.profiler.output_html()
#     global_request_count = global_request_count + 1
#     with open("timing/api_profil{}.html".format(global_request_count - 1),"w") as f:
#         f.write(output_html)
