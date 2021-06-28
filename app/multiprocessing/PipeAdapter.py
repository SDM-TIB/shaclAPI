from multiprocessing import Pipe

class ConnectionAdapter():
    '''
    The idea is to use a Connection Object with the functions of a Queue.
    '''

    def __init__(self, connection, is_sender) -> None:
        self.is_sender = is_sender
        self.connection = connection
        self.closed = False
    
    def put(self, item):
        if item == 'EOF' and self.closed:
            return
        if self.is_sender and not self.closed:
            self.connection.send(item)
            if item == 'EOF':
                self.connection.close()
                self.closed = True
        else:
            raise Exception("Receiver is not allowed to send or Connection is closed!")
    
    def get(self, block=True, timeout=None):
        result = None
        if not self.is_sender and not self.closed:
            if block and timeout == None:
                result = self.connection.recv()
            elif block and timeout != None:
                result = self.connection.recv()
            elif not block and timeout == None:
                if self.connection.poll():
                    result = self.connection.recv()
                else:
                    raise Exception("Pipe is empty!")
            elif not block and timeout != None:
                if self.connection.poll(timeout):
                    result = self.connection.recv()
                else:
                    raise Exception("Pipe is empty!")
        else:
            raise Exception("Sender is not allowed to receive or Connection is closed!")
        if result == 'EOF':
            self.connection.close()
            self.closed = True
        return result


class PipeAdapter():
    def __init__(self) -> None:
        conn1, conn2 = Pipe()
        self.sender = ConnectionAdapter(conn1, True)
        self.receiver = ConnectionAdapter(conn2, False)

class QueueAdapter():
    def __init__(self, context):
        queue = context.Queue()
        self.sender = queue
        self.receiver = queue
