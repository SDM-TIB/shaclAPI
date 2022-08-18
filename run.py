import logging
from flask import Flask, request, Response
from shaclapi import logger as shaclapi_logger

# Setup Logging
# Use for debugging:
# shaclapi_logger.setup(level=logging.DEBUG, handler=logging.FileHandler('/shaclAPI/examples/api.log'))
# logging.getLogger('werkzeug').disabled = True

# Use for production:
shaclapi_logger.setup(level=logging.INFO)

logger = logging.getLogger(__name__)

# Due to the processes starting, when importing something from shaclapi.api, its necessary to call shaclapi_logger.setup(...) before otherwise logging from the processes do not work.
import shaclapi.api as api

app = Flask(__name__)


@app.route('/multiprocessing', methods=['POST'])
def route_multiprocessing():
    """
    Required Arguments:
        - query
        - external_endpoint
        - schemaDir
    See app/config.py for a full list of available arguments!
    """
    api_output = api.run_multiprocessing(request.form)
    if type(api_output) != str:
        return Response(api_output.to_json(), mimetype='application/json')
    else:
        return Response(api_output, mimetype='text/plain')


@app.route('/validation', methods=['POST'])
def route_validation():
    """Use the heuristics implemented and activated in the given configuration, to run the
    validation over the reduced SHACL shape schema. Returns the validation results per instance
    as well as the number of valid and invalid instances per shape.

    Returns
    -------
    flask.Response
        The response containing the validation results.
    """
    return api.validation_and_statistics(request.form)


@app.route('/reduce', methods=['POST'])
def reduced_schema_only():
    from flask import jsonify
    try:
        node_order = api.only_reduce_shape_schema(request.form)
        return jsonify({'shapes': node_order})
    except Exception as e:
        import sys
        import traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        emsg = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        return jsonify({'result': [], 'error': str(emsg)})


@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello World'
