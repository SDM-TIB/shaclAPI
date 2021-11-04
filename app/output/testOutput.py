import json
from enum import IntEnum

class ValReport(IntEnum):
    SHAPE = 0
    IS_VALID = 1
    REASON = 2

class TestOutput():
    def __init__(self, output={}):
        self._output = output

    def to_json(self,targetShapeID=None):
        return json.dumps(self.output(targetShapeID))

    def output(self, targetShapeID):
        return self._output
    
    @staticmethod
    def fromJoinedResults(targetShapeID, final_result_queue):
        output = {"validTargets": [], "invalidTargets": [], "advancedValid": [], "advancedInvalid": []}
        instances = dict()
        result = final_result_queue.get()
        while result != 'EOF':
            query_result = result['result']
            for binding in query_result:
                if 'validation' in binding:
                    if binding['validation']:
                        if binding['instance'] not in instances:
                            instances[binding['instance']] = binding['validation']
                            if targetShapeID == binding['validation'][ValReport.SHAPE]:
                                if binding['validation'][ValReport.IS_VALID]:
                                    output['validTargets'].append((binding['instance'], binding['validation'][ValReport.REASON]))
                                else:
                                    output['invalidTargets'].append((binding['instance'], binding['validation'][ValReport.REASON]))
                            else:
                                if binding['validation'][ValReport.IS_VALID]:
                                    output['advancedValid'].append((binding['instance'], binding['validation'][ValReport.REASON]))
                                else:
                                    output['advancedInvalid'].append((binding['instance'], binding['validation'][ValReport.REASON]))
            result = final_result_queue.get()
        return TestOutput(output=output)

    def to_string(self, targetShapeID):
        return str(self.output(targetShapeID))
