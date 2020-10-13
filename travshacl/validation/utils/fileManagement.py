# -*- coding: utf-8 -*-
import os

def openFile(path, fileName):
    if not os.path.exists(path):
        os.makedirs(path)
    return open(path + fileName, "w", encoding="utf-8")

def closeFile(file):
    file.close()
