from client import run_all as evaluate
from controller import Controller
from controller import run_all
from func_timeout import exit_after
import subprocess
import os 
import time
from joblib import Parallel, delayed
from tqdm import tqdm
import math
import random

DEFAULT_TRACKS = ('forza','eTrack_3','cgTrack_2','wheel')


@exit_after(15)
def evaluate_parameters(parameters, idx, track, debug = False):
    start = time.time()
    try:
        res = evaluate(parameters, idx,track, debug)
    except KeyboardInterrupt:
        elapsed_time = time.time() - start
        if elapsed_time < 14:
            exit(0)
        subprocess.call([os.path.join('bat_files','stop_server.bat')]. str(idx))
        res = {
                'racePos' : 100,
                'damage' : 5000,
                'lapTime' : 1000,
                'distRaced' : 10,
                'error' : True,
                'laplength' : 10,
                'trackPos' : [10000]

            }
    return res

def fit(res):
    return (res['lapTime'] if res['lapTime'] > 50 else 1000) / (res['laplength'] if res['laplength'] !=0 else 10)

def evaluate_batch(batch, keys, available_tracks = DEFAULT_TRACKS):
    res_lst = []
    
    change_track = math.ceil(len(batch) / len(available_tracks))

    with tqdm(total=len(batch)) as pbar:
        for i, individual in enumerate(batch):
            parameters = {} 
            for j, key in enumerate(keys):
                parameters[key] = individual[j]

            res = evaluate_parameters(parameters, 1, available_tracks[i // change_track])
            res_lst.append(res['lapTime']/res['laplength'])
            pbar.update(1)

    return res_lst

def get_samples(x, num_threads):
    samples = []

    sample_size = math.floor(len(x) / num_threads)
    for i in range(num_threads):
        if i == num_threads - 1:
            samples.append(x[i*sample_size : ])
        else:
            samples.append(x[i*sample_size : (i+1) * sample_size])

    return samples

def evaluate_batch_parameters(parameters, idx, debug = False):
    res_lst = []
    for p in tqdm(parameters):
        res = evaluate_parameters(p[0], idx, p[1], debug)
        res_lst.append(res)
    return res_lst

def parallel_evaluation(parameters, debug):

    with Parallel(n_jobs=len(parameters)) as parallel:
        all_res = parallel(delayed(evaluate_batch_parameters)(p,i + 1, debug) for i, p in enumerate(parameters))
    return [value for res in all_res for value in res]

def evaluate_batch_parallel(batch, keys, num_threads = 5, available_tracks = DEFAULT_TRACKS, fitness_function = fit, debug = False):
    parameters = []

    for i in range(len(batch)):
        tmp = {}
        for j, key in enumerate(keys):
            tmp[key] = batch[i][j]
        parameters.append((tmp, random.choice(available_tracks)))

    samples = get_samples(parameters, num_threads)

    res_lst = [fitness_function(res) for res  in parallel_evaluation(samples, debug)]
    return res_lst