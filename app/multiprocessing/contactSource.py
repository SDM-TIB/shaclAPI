__author__ = 'Kemele M. Endris'

import urllib.parse
import urllib.request
import logging

logger = logging.getLogger(__name__)

"""
Normal contactSource Implementation but queue is filled with an output, which is in a format which is joinable with validation results. Queue_copy contains the normal result but with an id.
Example:
    Input: {var1: instance1, var2: instance2, var3: instance3} 
    Output queue:
           {'instance': instance1, 'var': var1, 'id': UNIQUE_RESULT_ID}, 
           {'instance': instance2, 'var': var2, 'id': UNIQUE_RESULT_ID}, 
           {'instance': instance3, 'var': var3, 'id': UNIQUE_RESULT_ID}
    Output queue_copy:
           {'query_result': {'var1': instance1, 'var2': instance2, 'var3': instance3}, 'id': UNIQUE_RESULT_ID}

"""

def contactSource(queue, queue_copy, endpoint, query, limit=-1):
    # Contacts the datasource (i.e. real endpoint).
    # Every tuple in the answer is represented as Python dictionaries
    # and is stored in a queue.
    # print "in *NEW* contactSource"
    b = None
    cardinality = 0

    server = endpoint

    referer = server
    try:
        server = server.split("http://")[1]
    except:
        try:
            server = server.split("https://")[1]
        except:
            raise Exception("Not a valid endpoint url: {}".format(server))
    if '/' in server:
        (server, path) = server.split("/", 1)
    else:
        path = ""
    host_port = server.split(":")
    port = 80 if len(host_port) == 1 else host_port[1]
    card = 0
    if limit == -1:
        b, card = contactSourceAux(referer, server, path, port, query, queue, queue_copy)
    else:
        # Contacts the datasource (i.e. real endpoint) incrementally,
        # retreiving partial result sets combining the SPARQL sequence
        # modifiers LIMIT and OFFSET.

        # Set up the offset.
        offset = 0

        while True:
            query_copy = query + " LIMIT " + str(limit) + " OFFSET " + str(offset)
            b, cardinality = contactSourceAux(referer, server, path, port, query_copy, queue,queue_copy, offset)
            card += cardinality
            if cardinality < limit:
                break

            offset = offset + limit

    # Close the queue
    # queue.put("EOF")
    # queue_copy.put("EOF")
    return b


def contactSourceAux(referer, server, path, port, query, queue, queue_copy, first_id=0):

    # Setting variables to return.
    b = None
    reslist = 0

    if '0.0.0.0' in server:
        server = server.replace('0.0.0.0', 'localhost')

    js = "application/sparql-results+json"
    params = {'query': query, 'format': js}
    headers = {"User-Agent":
                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
               "Accept": js}
    try:
        data = urllib.parse.urlencode(params)
        data = data.encode('utf-8')
        req = urllib.request.Request(referer, data, headers)
        with urllib.request.urlopen(req) as response:
            resp = response.read()
            resp = resp.decode()
            res = resp.replace("false", "False")
            res = res.replace("true", "True")
            res = eval(res)
            reslist = 0
            if type(res) == dict:
                b = res.get('boolean', None)

                if 'results' in res:
                    # print "raw results from endpoint", res
                    id = first_id
                    for x in res['results']['bindings']:
                        for key, props in x.items():
                            # Handle typed-literals and language tags
                            suffix = ''
                            if props['type'] == 'typed-literal':
                                if isinstance(props['datatype'], bytes):
                                    suffix = "^^<" + props['datatype'].decode('utf-8') + ">"
                                else:
                                    suffix = "^^<" + props['datatype'] + ">"
                            elif "xml:lang" in props:
                                suffix = '@' + props['xml:lang']
                            try:
                                if isinstance(props['value'], bytes):
                                    x[key] = props['value'].decode('utf-8') + suffix
                                else:
                                    x[key] = props['value'] + suffix
                            except:
                                x[key] = props['value'] + suffix
                            queue.put({'var': key, 'instance': x[key], 'id': id})
                        queue_copy.put({'query_result': x, 'id': id})
                        id = id + 1
                        reslist += 1
                    # Every tuple is added to the queue.
                    #for elem in reslist:
                        # print elem
                        #queue.put(elem)

            else:
                logger.warn("the source " + str(server) + " answered in " + res.getheader("content-type") + " format, instead of"
                       + " the JSON format required, then that answer will be ignored")
    except Exception as e:
        raise Exception("Exception while sending request to ", referer, "msg:", e)

    return b, reslist