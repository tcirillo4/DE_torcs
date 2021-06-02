import numpy as np

def track_center_fitness(res):
    x1 = 0 if res['distRaced']>=res['laplength'] else  res['laplength'] - res['distRaced']
    return np.sum(np.abs(res['trackPos'])) + x1

def fitness_time(res):
    x1 = 0 if res['distRaced']>=res['laplength'] else res['laplength'] - res['distRaced']
    return res['lapTime'] + x1

def fitness_speed(res):
    x1 = 0 if res['distRaced']>=res['laplength'] else  res['laplength'] - res['distRaced']
    x2 = res['lapTime'] if res['lapTime'] > 50 else 1000
    x3 = res['laplength'] if res['laplength'] !=0 else 10
    return (x2 / x3) + x1

def fitness_1(res):
    x1 = fitness_speed(res)
    x2 = np.sum(np.abs(res['trackPos']))
    return x1 + x2

