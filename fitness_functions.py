import numpy as np

def track_center_fitness(res):
    x1 = 0 if res['distRaced']>=res['laplength'] else  res['laplength'] - res['distRaced']
    return np.mean(np.abs(res['trackPos'])) + x1

def fitness_time(res):
    x1 = 0 if res['distRaced']>=res['laplength'] else res['laplength'] - res['distRaced']
    return res['lapTime'] + x1

def fitness_speed_lap(res):
    x1 = 0 if res['distRaced']>=res['laplength'] else  res['laplength'] - res['distRaced']
    x2 = res['lapTime'] if res['lapTime'] > 50 else 1000
    x3 = res['laplength'] if res['laplength'] !=0 else 10
    return (x2 / x3) + x1

def fitness_1(res, norm_factor = 10):
    x1 = fitness_speed_lap(res)
    x2 = np.mean(np.abs(res['trackPos'])) 
    return x1 + (x2 / norm_factor)

def fitness_2(res, norm_factor = 10):
    x1 = 0 if res['distRaced']>=res['laplength'] else  res['laplength'] - res['distRaced']
    x2 = np.mean(res['speedX'])
    x3 = np.std(res['speedX'])
    x4 = np.mean(np.abs(res['trackPos'])) * 100 
    return x1 -x2 * 0.35 + x3 * 0.325 * x4 * 0.325 