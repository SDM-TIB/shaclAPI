from multiprocessing import Pipe

class ConnectionAdapter():
    def __init__(self, connection, is_sender) -> None:
        self.is_sender = is_sender
        self.connection = connection
    
    def put(self, item):
        if self.is_sender:
            self.connection.send(item)
        else:
            raise Exception("Receiver is not allowed to send")
    
    def get(self, block=True, timeout=None):
        if not self.is_sender:
            if block and timeout == None:
                return self.connection.recv()
            elif block and timeout != None:
                return self.connection.recv()
            elif not block and timeout == None:
                if self.connection.poll():
                    return self.connection.recv()
                else:
                    raise Exception("Pipe is empty!")
            elif not block and timeout != None:
                if self.connection.poll(timeout):
                    return self.connection.recv()
                else:
                    raise Exception("Pipe is empty!")


class PipeAdapter():
    def __init__(self) -> None:
        conn1, conn2 = Pipe()
        self.sender = ConnectionAdapter(conn1, True)
        self.receiver = ConnectionAdapter(conn2, False)

