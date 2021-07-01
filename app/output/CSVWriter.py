import os

class CSVWriter():
    def __init__(self, path):
        self.path = path
        self.fd = None

    def __check_file_exists(self):
        return os.path.isfile(self.path)
    
    def __write_header(self, columns):
        header = ",".join([str(key) for key in columns]) + '\n'
        self.fd.write(header)
    
    def __write_dict(self, input):
        content = ",".join([str(value) for value in input.values()]) + '\n'
        self.fd.write(content)
    
    def __open_fd(self, mode):
        self.fd = open(self.path, mode)
    
    def __close_fd(self):
        self.fd.close()
        self.fd = None
    
    def writeSingle(self, input):
        if self.__check_file_exists():
            self.__open_fd('a')
        else:
            self.__open_fd('w')
            self.__write_header(input.keys())
        self.__write_dict(input)
        self.__close_fd()
    
    def writeMulti(self,input):
        if self.__check_file_exists():
            self.__open_fd('a')
        else:
            self.__open_fd('w')
            self.__write_header(input.keys())
        self.__write_dict(input)
    
    def writeListOfDicts(self,input):
        if self.__check_file_exists():
            self.__open_fd('a')
        else:
            self.__open_fd('w')
            self.__write_header(input[0].keys())
        for item in input:
            self.__write_dict(item)
        self.__close_fd()

    def close(self):
        if self.fd:
            self.__close_fd()





