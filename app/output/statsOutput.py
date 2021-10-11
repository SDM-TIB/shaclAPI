import json

class StatsOutput():
    def __init__(self, output={}):
        self._output = output
    
    def to_json(self, targetShapeID=None):
        return json.dumps(self._output)
    
    @property
    def output(self):
        return self._output
    