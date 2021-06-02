import os 
import csv
import json
from tqdm import tqdm
import math
import time
from client import run_all as evaluate
from func_timeout import exit_after
import subprocess
from evaluation import *
from fitness_functions import *

MAIN_DIRECTORY = '\\\\DESKTOP-9HTHA06\\Cartella condivisa\\addestramento'
ASSIGNED_IDX = 1
INPUT_FILE = str(ASSIGNED_IDX) + '_input.csv'
OUTPUT_FILE = str(ASSIGNED_IDX) + '_output.csv'
PFILE= open('real_parameters','r')
AVAIBLES_TRACK = ('forza', 'eTrack_3', 'cgTrack_2', 'wheel')
TRACK_TO_USE = ['eTrack_3']
debug = False
parallel = True
THREADS_NUM = 4
fitness_function = fitness_1

keys= json.load(PFILE).keys()

def read_file(filename):
    parameters = []
    with open(filename, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for i, row in enumerate(csv_reader):
                parameters.append([])
                for value in row:
                    parameters[-1].append(float(value))
    os.remove(filename)
    return parameters

def write_results(filename, results):
    print('Writing results...')
    with open(filename, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for res in results:
            writer.writerow([res])

def wait_parameters():
    print('Waiting new parameters...')
    while True:
        if os.path.isfile(os.path.join(MAIN_DIRECTORY, INPUT_FILE)):
            parameters = read_file(os.path.join(MAIN_DIRECTORY, INPUT_FILE))
            print(str(len(parameters)) + ' parameters received.')
            if parallel:
                results = evaluate_batch_parallel(parameters, 
                                                    keys, 
                                                    num_threads=THREADS_NUM, 
                                                    available_tracks=TRACK_TO_USE, 
                                                    debug=debug,
                                                    fitness_function=fitness_function)
            else:
                results = evaluate_batch(parameters, keys)
            return results
        time.sleep(1)


if __name__ == '__main__':
    while True:
        results = wait_parameters()
        write_results(os.path.join(MAIN_DIRECTORY, OUTPUT_FILE),  results)