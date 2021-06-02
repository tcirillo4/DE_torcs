
from pymoo.factory import Problem
import numpy as np
import matplotlib.pyplot as plt
import client 
import json
import time
import csv
import os
from tqdm import tqdm
import math
import subprocess
import time
from joblib import Parallel, delayed
from evaluation import *

from pymoo.operators.sampling.latin_hypercube_sampling import LatinHypercubeSampling
from func_timeout import exit_after

computation_weights =  {
    1 : {0 : 1},
    2 : {0 : .68, 1 : .32},
    3 : {0 : .5, 1 : .25, 2 : .25},
    4 : {0 : .32, 1 : .17, 2 : .24, 3 : .27}
}

INPUT_FILE = '_output.csv'
OUTPUT_FILE = '_input.csv'


def send_parameters(filename, parameters):
    with open(filename, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for res in parameters:
            writer.writerow(res)

def read_file(filename):
    results = []
    with open(filename, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
                results.append(float(row[0]))
    os.remove(filename)
    return results

def write_parameters(x):
    with open(os.path.join('output_files','parameters.csv'), 'w', newline='') as csv_file: 
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerows(x)

def write_best_parameters(parameters):
    with open(os.path.join('output_files','best_parameters.json'), 'w') as file:
        json.dump(parameters, file)

def generate_samples(x, nodes):
    samples = [(0, math.ceil(len(x) * computation_weights[nodes][0]))]

    for i in range(1, nodes):
        if i == nodes - 1:
            samples.append((samples[i-1][1], len(x)))
        else:
            add = math.floor(len(x) * computation_weights[nodes][i])
            samples.append((samples[i-1][1], samples[i-1][1] + add))

    return samples

def wait_results(nodes, main_directory):
    res_lst = []
    for i in range(1, nodes):
        print('Waiting results from node ' + str(i) + '...')
        while True:
            if os.path.isfile(os.path.join(main_directory, str(i) + INPUT_FILE)):
                res = read_file(os.path.join(main_directory, str(i) + INPUT_FILE))
                print(str('Results from node ' + str(i) + ' received.'))
                res_lst += res
                break
            else:
                time.sleep(1)
    return res_lst


class RaceProblem(Problem):

    def __init__(self, main_directory, fitness_function, tracks, resume = True, num_nodes = 4, parallel = True, num_threads = 5):
        super().__init__(n_var=48, n_obj=1, xl =  np.full(48, -10000), xu=  np.full(48, 10000))
        pfile= open('real_parameters','r')
        self.parameters= json.load(pfile)
        self.resume = resume
        self.main_directory = main_directory
        self.num_nodes = num_nodes
        self.parallel = parallel
        self.fitness = fitness_function
        self.tracks = tracks
        if self.parallel:
            self.num_threads = num_threads
        if not resume:
            with open(os.path.join('output_files','results.csv') , 'w'): pass
        

    def _evaluate(self, x, out, *args, **kwargs):
        res_lst = []
        write_parameters(x)

        samples = generate_samples(x, self.num_nodes)

        for i in range(1, self.num_nodes):
            send_parameters(os.path.join(self.main_directory, str(i) + OUTPUT_FILE), x[samples[i][0] : samples[i][1]])
        
        if self.parallel:
            res = evaluate_batch_parallel(x[samples[0][0] : samples[0][1]], list(self.parameters.keys()), self.num_threads, available_tracks=self.tracks, fitness_function= self.fitness)
        else:
            res = evaluate_batch(x[samples[0][0] : samples[0][1]], list(self.parameters.keys()))

        res_lst.extend(res)

        res = wait_results(self.num_nodes, self.main_directory)

        res_lst.extend(res)
        
        with open(os.path.join('output_files','results.csv'), 'a', newline='') as f: 
            f.write(str(min(res_lst)) + '\n')

        best_p = x[np.argmin(res_lst)]

        for i, key in enumerate(list(self.parameters.keys())):
            self.parameters[key] = best_p[i]

        write_best_parameters(self.parameters)

        DEFAULT_TRACKS = ('forza','eTrack_3','cgTrack_2','wheel')
        for track in DEFAULT_TRACKS:
            print('TRACK: ' + track)
            print(evaluate(self.parameters, 1, track))

        out['F'] = np.array(res_lst)

