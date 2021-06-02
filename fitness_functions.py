import numpy as np

def track_center_fitness(res):
    return np.sum(np.abs(res['trackPos']))

def fitness_1(res):
    x1 = res['lapTime'] if res['lapTime'] > 50 else 1000
    x2 = res['laplength'] if res['laplength'] !=0 else 10
    x3 = 0 if res['distRaced']>=res['laplength'] else 1000
    return (x1 / x2) + np.mean(np.abs(res['trackPos'])) + x3