def grey(string):
    return '\033[02m' + string + '\033[0m'


def magenta(string):
    return '\033[95m' + string + '\033[00m'


def green(string):
    return '\033[92m' + string + '\033[00m'

def blue(string):
    return '\033[34m' + string + '\033[00m'

def headline(string):
    length = len('--------------------------------------------------------------')
    str_len = len(string)
    remaining_length = length - str_len
    if not remaining_length % 2 == 0:
        string = string + ' '
        remaining_length = remaining_length - 1    
    return '-'* int(remaining_length/2) + string + '-'*int(remaining_length/2)
