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
    def fromJoinedResultQueue(target_var, joined_queue):
        actual_tuple = joined_queue.get()
        output = {"validTargets": [], "invalidTargets": [], "advancedValid": [], "advancedInvalid": []}
        while actual_tuple != 'EOF':
            if actual_tuple['validation'][ValReport.IS_VALID]:
                output["validTargets"].append((actual_tuple[target_var], actual_tuple['validation'][ValReport.REASON]))
            else:
                output["invalidTargets"].append((actual_tuple[target_var], actual_tuple['validation'][ValReport.REASON]))
            actual_tuple = joined_queue.get()
        return TestOutput(None, output=output)

    def to_string(self, targetShapeID):
        return str(self.output(targetShapeID))
