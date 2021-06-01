from joblib import parallel
from race_problem import RaceProblem
from pymoo.optimize import minimize
from pymoo.factory import get_termination
import numpy as np
from pymoo.algorithms.so_de import DE
import random
import json
import os
import csv

n_pop = 300
n_vars = 48
max_gens = 30
resume = True
NUM_OF_NODES = 1
MAIN_DIRECTORY = 'D:\\Cartella condivisa\\addestramento'
THREADS_NUM = 5
parallel = True

def read_parameters():
    parameters = []

    with open(os.path.join('output_files','parameters.csv'), mode='r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            parameters.append([])
            for i,value in enumerate(row):
                parameters[-1].append(float(value))
    return parameters

def init_population(resume = True):
    if not resume:
        pfile= open('real_parameters','r')
        parameters= json.load(pfile)
        init_pop = []
        for _ in range(n_pop):
            idx= random.randint(0, len(parameters) - 1)
            new_param = list(parameters.values())
            while new_param[idx] == 0:
                idx= random.randint(0, len(parameters) - 1)
            new_param[idx] += random.random() * new_param[idx]
            init_pop.append(new_param)
        init_pop = np.array(init_pop)
    #Resume from the last population
    else:
        init_pop = np.array(read_parameters())
        if len(init_pop) != n_pop:
            raise Exception()
    return init_pop

# problem to be solved
problem = RaceProblem(main_directory=MAIN_DIRECTORY, resume = resume, num_nodes=NUM_OF_NODES, parallel=parallel, num_threads=THREADS_NUM)

termination = get_termination("n_gen", max_gens)

#Init population from the default parameters


algorithm = DE(pop_size=n_pop,  sampling=init_population(resume),variant="DE/rand/1/bin", CR=.7, F=.9, dither="vector", jitter=True,eliminate_duplicates=False)

res = minimize(problem, algorithm, termination, seed=112, verbose=True, save_history=True)
