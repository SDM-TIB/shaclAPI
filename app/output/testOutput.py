from app.output.baseResult import BaseResult
import json


class TestOutput():

    def __init__(self, baseResult):
        self.base: BaseResult = baseResult
        self._output = {}

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
                if self.base.validation_report_triples[t][0] == targetShapeID:
                    if self.base.validation_report_triples[t][1] == True:
                        self._output["validTargets"].append(
                            (t, self.base.validation_report_triples[t][2]))
                    elif self.base.validation_report_triples[t][1] == False:
                        self._output["invalidTargets"].append(
                            (t, self.base.validation_report_triples[t][2]))
            for t in self.base.validation_report_triples:
                # 'validation' : (instance's shape, is_valid, violating/validating shape)
                if self.base.validation_report_triples[t][0] != targetShapeID:
                    if self.base.validation_report_triples[t][1] == True:
                        self._output["advancedValid"].append(
                            (t, self.base.validation_report_triples[t][2]))
                    elif self.base.validation_report_triples[t][1] == False:
                        self._output["advancedInvalid"].append(
                            (t, self.base.validation_report_triples[t][2]))
        return self._output

    def __str__(self):
        pass
