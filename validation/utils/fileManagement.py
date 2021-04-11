# -*- coding: utf-8 -*-
import os

def openFile(path, fileName):
    return open(path + fileName, "w")

def closeFile(file):
    file.close()
