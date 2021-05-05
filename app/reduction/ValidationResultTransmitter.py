import requests
import time

class ValidationResultTransmitter():
    """
    Class used to transmit validation results from a backend to the api.
    This can be done via an endpoint or using a multiprocessing.Queue.
    """

    def __init__(self, validation_result_endpoint=None, output_queue=None, first_val_time_queue=None, log_stats=False):
        self.output_queue = output_queue
        self.endpoint = validation_result_endpoint
        self.timestamp_of_first_result_send = False
        self.first_val_time_queue = first_val_time_queue
        self.log_stats = log_stats
    
    def send(self, instance, shape, valid, reason):
        if (not self.timestamp_of_first_result_send) and self.log_stats:
            self.timestamp_of_first_result_send = True
            self.first_val_time_queue.put(time.time())

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
        