import os
import traceback
import pandas as pd
from contextlib import contextmanager

import logging
logger = logging.getLogger(__name__)

printi_verbose_tree = 0
printi_nompro = None

def printi(loggerf, text, pre=0, post=0):
    global printi_verbose_tree, printi_nompro
    printi_verbose_tree += pre
    if text is not None:
        linea = '{}{}'.format((' '*2)*printi_verbose_tree, text)
        if printi_nompro is not None:
            linea = '[{}] {}'.format(printi_nompro, linea)
        loggerf(linea)
    printi_verbose_tree += post
    return

def printi_reset(verbose_base = 0):
    global printi_verbose_tree
    printi_verbose_tree = verbose_base
    return

def printi_get_base():
    global printi_verbose_tree
    return printi_verbose_tree

def path_split(s):
    head, tail = os.path.split(s)
    if tail == '':
        return [head]
    return path_split(head) + [tail]

def format_traceback(returninfo, add_space_top=False, add_space_bottom=False):
    result = []
    tbs = traceback.format_exception(*returninfo)
    for tbn, tb in enumerate(tbs):
        lineas = tb.split('\n')
        while '' in lineas: del lineas[lineas.index('')]
        for ln, linea in enumerate(lineas):
            if '"' in linea:
                j = linea.index('"') + 1
                k = linea[j:].index('"') + j
                archivo = linea[j:k]
                archivo_path = path_split(archivo)
                for subcarpeta in ['sq-modelo', 'site-packages']:
                    if subcarpeta in archivo_path:
                        archivo = os.sep.join(archivo_path[archivo_path.index(subcarpeta)+1:])
                        break
                linea = '{}{}{}'.format(linea[:j], archivo, linea[k:])
            if (add_space_bottom) and (tbn == len(tbs) - 1) and (ln == len(lineas) - 1): result.append('')
            result.append(linea)
            if (add_space_top) and (tbn == 0) and (ln == 0): result.append('')
    return result

def init():

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    fh = logging.FileHandler('stg_modelo.log')
    fh.setLevel(logging.DEBUG)

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s [%(levelname)-8s] %(name)-15s : %(message)s',
                        datefmt='%d-%m-%Y %H:%M:%S',
                        handlers=[ch,fh])
    return

@contextmanager
def cwd(path):
    oldcwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldcwd)