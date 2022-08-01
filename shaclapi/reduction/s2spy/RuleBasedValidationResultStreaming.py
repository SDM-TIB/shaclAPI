from SHACL2SPARQLpy.RuleBasedValidation import RuleBasedValidation


class RuleBasedValidationResultStreaming(RuleBasedValidation):

    def __init__(self, endpoint, node_order, shapesDict, logOutput,
                 validTargetsOutput, invalidTargetsOutput, statsOutput, tracesOutput, result_transmitter):
        super().__init__(endpoint, node_order, shapesDict, logOutput,
                         validTargetsOutput, invalidTargetsOutput, statsOutput, tracesOutput)
        self.result_transmitter = result_transmitter
        
    def registerTarget(self, t, isValid, depth, logMessage, focusShape, state):
        super().registerTarget(t, isValid, depth, logMessage, focusShape, state)
        self.result_transmitter.send(instance=t.arg, shape=t.pred, valid=isValid, reason=logMessage)
    
    def exec(self):
        super().exec()
        self.result_transmitter.done()
