import json 
import statistics
from client import run_all as evaluate
from tqdm import tqdm 

def compute(track, num_iter_test, file='output_files/best_parameters.json'):
    racePos = []
    lapTime = []

    results = []
    pfile= open(file,'r')
    parameters= json.load(pfile)
    for _ in tqdm(range(num_iter_test)):
        results.append(evaluate(parameters, 1, track))
    
    for res in results:
        racePos.append(res['racePos'])
        lapTime.append(res['lapTime'])
    
    return statistics.mean(racePos), statistics.stdev(racePos), statistics.mean(lapTime), statistics.stdev(lapTime)

#16 20
DEFAULT_TRACKS = ['forza','eTrack_3','cgTrack_2','wheel']
for track in DEFAULT_TRACKS:
    results = compute(track, 100, file='output_files_best_parameters_opponents/best_parameters_16.0.json')
    print("Risultati su trakc: "+track)
    print("RacePos: mean", results[0], "stdev", results[1])
    print("lapTime: mean", results[2], "stdev", results[3])
