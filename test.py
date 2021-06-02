from client import run_all as evaluate
from func_timeout import exit_after
import subprocess
import os 
import time
from joblib import Parallel, delayed
from tqdm import tqdm
import math
import random
import threading
import itertools as it
import numpy as np

DEFAULT_TRACKS = ('forza','eTrack_3','cgTrack_2','wheel')
shared_res_lst = []
shared_batch = []
shared_keys = []
current_idx = 0
batch_lock = threading.Condition()
res_lock = threading.Condition()


@exit_after(30)
def evaluate_parameters(parameters, idx, track, kill_process = True):
    start = time.time()
    try:
        res = evaluate(parameters, idx,track)
    except KeyboardInterrupt:
        elapsed_time = time.time() - start
        if elapsed_time < 29:
            exit(0)
        if kill_process:
            subprocess.call([os.path.join('bat_files','stop_server.bat')])
        res = {
                'racePos' : 100,
                'damage' : 5000,
                'lapTime' : 1000,
                'distRaced' : 10,
                'error' : True,
                'laplength' : 10,
                'trackPos' : [100]

            }
    return res


def parallel_evaluation(parameters):

    with Parallel(n_jobs=len(parameters)) as parallel:
        all_res = parallel(delayed(evaluate_parameters)(parameters[i][0],i + 1, parameters[i][1], False) for i in range(len(parameters)))
    for res in all_res:
        if 'error' in res:
            subprocess.call([os.path.join('bat_files','stop_server.bat')])
    return all_res
    

def evaluate_batch_parallel(batch, keys, num_threads = 5, available_tracks = DEFAULT_TRACKS):
    res_lst = []
    
    change_track = math.ceil(len(batch) / len(available_tracks))
    
    for i in tqdm(range(0, len(batch), num_threads)):
        max_element = min(num_threads, len(batch) - i)
        parameters = []
        
        for idx in range(max_element):     
            tmp = {}
            for j, key in enumerate(keys):
                tmp[key] = batch[i + idx][j]
            parameters.append((tmp, random.choice(available_tracks)))

        if len(available_tracks) > 1:
            res_lst.extend([(res['lapTime'] if res['lapTime'] > 50 else 1000) / (res['laplength'] if res['laplength'] !=0 else 10) for res  in parallel_evaluation(parameters)])
        else:
            res_lst.extend([np.sum(np.abs(res['trackPos'])) for res  in parallel_evaluation(parameters)])
    return res_lst

def compute_result(idx):
    global shared_batch, shared_res_lst, current_idx
    while len(shared_batch) > 0:
        batch_lock.acquire()
        parameters = shared_batch.pop(0)
        my_id = current_idx
        current_idx += 1
        batch_lock.notify_all()
        batch_lock.release()
        tmp = {}
        for j, key in enumerate(shared_keys):
            tmp[key] = parameters[j]
        res = evaluate_parameters(tmp, idx, random.choice(DEFAULT_TRACKS))
        shared_res_lst[my_id] = (res['lapTime'] if res['lapTime'] > 50 else 1000) / (res['laplength'] if res['laplength'] !=0 else 10)

def evaluate_batch_parallel_faster(batch, keys, num_threads = 5, available_tracks = DEFAULT_TRACKS):
    global shared_batch, shared_res_lst, shared_keys
    from controller import Controller
    from controller import run_all as evaluate

    num_threads = 2
    shared_batch = list(batch)
    shared_res_lst = [None for _ in range(len(batch))]
    shared_keys = keys

    threads = [threading.Thread(target=compute_result, args=[i+1]) for i in range(num_threads)]
    for th in threads:
        th.daemon=True
        th.start()

    for th in threads:
        th.join()

    return shared_keys

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