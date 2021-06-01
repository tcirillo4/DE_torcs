from client import run_all as evaluate
from func_timeout import exit_after
import subprocess
import os 
import time
from joblib import Parallel, delayed
from tqdm import tqdm
import math

@exit_after(15)
def evaluate_parameters(parameters, idx, track, kill_process = True):
    start = time.time()
    try:
        res = evaluate(parameters, idx,track)
    except KeyboardInterrupt:
        elapsed_time = time.time() - start
        if elapsed_time < 14:
            exit(0)
        if kill_process:
            subprocess.call([os.path.join('bat_files','stop_server.bat')])
        res = {
                'racePos' : 100,
                'damage' : 5000,
                'lapTime' : 1000,
                'distRaced' : 10,
                'error' : True

            }
    return res

def parallel_evaluation(parameters):

    with Parallel(n_jobs=len(parameters)) as parallel:
        all_res = parallel(delayed(evaluate_parameters)(parameters[i][0],i + 1, parameters[i][1]) for i in range(len(parameters)))
    for res in all_res:
        if 'error' in res:
            subprocess.call([os.path.join('bat_files','stop_server.bat')])
    return all_res

def evaluate_batch_parallel(batch, keys, num_threads = 5, available_tracks = ('forza', 'eTrack_3', 'cgTrack_2', 'wheel')):
    res_lst = []
    
    change_track = math.ceil(len(batch) / len(available_tracks))
    
    for i in tqdm(range(0, len(batch), num_threads)):
        max_element = min(num_threads, len(batch) - i)
        parameters = []

        for idx in range(max_element):     
            tmp = {}
            for j, key in enumerate(keys):
                tmp[key] = batch[i][j]
            parameters.append((tmp, available_tracks[(i + idx) // change_track]))

        res_lst.extend([res['lapTime'] / res['distRaced'] for res  in parallel_evaluation(parameters)])

    return res_lst


def evaluate_batch(batch, keys, available_tracks = ('forza', 'eTrack_3', 'cgTrack_2', 'wheel')):
    res_lst = []
    
    change_track = math.ceil(len(batch) / len(available_tracks))

    with tqdm(total=len(batch)) as pbar:
        for i, individual in enumerate(batch):
            parameters = {} 
            for j, key in enumerate(keys):
                parameters[key] = individual[j]

            res = evaluate_parameters(parameters, 1, available_tracks[i // change_track])
            res_lst.append(res['lapTime']/res['distRaced'])
            pbar.update(1)

    return res_lst
