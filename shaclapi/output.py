import json


class Output:
    def __init__(self, output):
        self.output = output

    def to_json(self):
        return json.dumps(self.output)
