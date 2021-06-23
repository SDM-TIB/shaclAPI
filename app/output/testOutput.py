from app.output.baseResult import BaseResult
import json
from app.output.baseResult import ValReport


class TestOutput():

    def __init__(self, baseResult, output={}):
        self.base: BaseResult = baseResult
        self._output = output

    def to_json(self,targetShapeID):
        return json.dumps(self.output(targetShapeID))

    def output(self, targetShapeID):
        if not self._output:

            transformed_query_results = {binding[self.base.query.target_var[1:]]
                : binding for binding in self.base.query_results}

            # valid dict is left only for test purposes, no need to change the test cases
            self._output = {"validTargets": [], "invalidTargets": [],
                           "advancedValid": [], "advancedInvalid": []}
            for t in self.base.validation_report_triples.keys() & transformed_query_results.keys():
                # 'validation' : (instance shape, is_valid, violating/validating shape)
                if self.base.validation_report_triples[t][ValReport.SHAPE] == targetShapeID:
                    if self.base.validation_report_triples[t][ValReport.IS_VALID] == True:
                        self._output["validTargets"].append(
                            (t, self.base.validation_report_triples[t][ValReport.REASON]))
                    elif self.base.validation_report_triples[t][ValReport.IS_VALID] == False:
                        self._output["invalidTargets"].append(
                            (t, self.base.validation_report_triples[t][ValReport.REASON]))
            for t in self.base.validation_report_triples:
                # 'validation' : (instance's shape, is_valid, violating/validating shape)
                if self.base.validation_report_triples[t][ValReport.SHAPE] != targetShapeID:
                    if self.base.validation_report_triples[t][ValReport.IS_VALID] == True:
                        self._output["advancedValid"].append(
                            (t, self.base.validation_report_triples[t][ValReport.REASON]))
                    elif self.base.validation_report_triples[t][ValReport.IS_VALID] == False:
                        self._output["advancedInvalid"].append(
                            (t, self.base.validation_report_triples[t][ValReport.REASON]))
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
        return TestOutput(None, output=output)

    def to_string(self, targetShapeID):
        return str(self.output(targetShapeID))
