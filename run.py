from flask import Flask, request, Response
import time, logging, json
import app.api as api

# Setup Logging
logging.getLogger('werkzeug').disabled = True

logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/endpoint", methods=['GET', 'POST'])
def endpoint():
    '''
    This is just an proxy endpoint to log the communication between the backend and the external sparql endpoint.
    '''
    api.EXTERNAL_SPARQL_ENDPOINT
    logger.debug('Received /endpoint request')
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
        return Response(api_output, mimetype='text/plain')

@app.route("/metrics", methods=['POST'])
def route_metrics():
    api.compute_experiment_metrices(request.form)
    return "Done"

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
