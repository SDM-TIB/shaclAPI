import requests

class ValidationResultTransmitter():
    """
    Class used to transmit validation results from a backend to the api.
    This can be done via an endpoint or using a multiprocessing.Queue.
    """

    def __init__(self, validation_result_endpoint=None, output_queue=None):
        self.output_queue = output_queue
        self.endpoint = validation_result_endpoint
    
    def send(self, instance, shape, valid, reason):
        if self.output_queue != None:
            self.output_queue.put({'instance': instance, 
                        'validation': (shape, valid, reason)})
        elif self.endpoint != None:
            new_val_result={'instance':instance, 'shape': shape, 'validation_result': 'valid' if valid else 'invalid', 'reason': reason}
            requests.post(self.endpoint, data=new_val_result)
        else:
            pass
    
    def use_streaming(self):
        return (self.output_queue != None) or (self.endpoint != None)
        