
from os import path

def siblingpath(filepath, filename):
    return path.join(path.dirname(filepath), filename)

