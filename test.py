import json 
import statistics
from client import run_all as evaluate
from tqdm import tqdm 

def compute(track, num_iter_test, file='output_files/best_parameters.json'):
    racePos = []
    damage = []
    vel = []

    results = []
    pfile= open(file,'r')
    parameters= json.load(pfile)
    for _ in tqdm(range(num_iter_test)):
        results.append(evaluate(parameters, 1, track))
    
    for res in results:
        damage.append(res['damage'])
        racePos.append(res['racePos'])
        vel.append(res['distRaced']/res['lapTime'])
    
    return statistics.mean(damage), statistics.stdev(damage), statistics.mean(racePos), statistics.stdev(racePos), statistics.mean(vel), statistics.stdev(vel)


DEFAULT_TRACKS = ['forza','eTrack_3','cgTrack_2','wheel']
for track in DEFAULT_TRACKS:
    results = compute(track, 10, file='output_files/BEST_12GEN_CR0.7_F0.9_85-15/best_parameters.json')
    print("Risultati su trakc: "+track)
    print("Damage: mean", results[0], "stdev", results[1])
    print("RacePos: mean", results[2], "stdev", results[3])
    print("Velocity: mean", results[4], "stdev", results[5])