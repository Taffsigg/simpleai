# coding=utf-8
from utils import FifoList, BoundedPriorityQueue, Inverse_transform_sampler
from models import (SearchNode, SearchNodeHeuristicOrdered,
                    SearchNodeStarOrdered, SearchNodeCostOrdered,
                    SearchNodeValueOrdered)
import copy
import math
import random
from itertools import count


def breadth_first_search(problem, graph_search=False):
    return _search(problem,
                   FifoList(),
                   graph_search=graph_search)


def depth_first_search(problem, graph_search=False):
    return _search(problem,
                   [],
                   graph_search=graph_search)


def limited_depth_first_search(problem, depth_limit, graph_search=False):
    return _search(problem,
                   [],
                   graph_search=graph_search,
                   depth_limit=depth_limit)


def iterative_limited_depth_first_search(problem, graph_search=False):
    return _iterative_limited_search(problem,
                                     limited_depth_first_search,
                                     graph_search=graph_search)


def uniform_cost_search(problem, graph_search=False):
    return _search(problem,
                   BoundedPriorityQueue(),
                   graph_search=graph_search,
                   node_factory=SearchNodeCostOrdered)


def greedy_search(problem, graph_search=False):
    return _search(problem,
                   BoundedPriorityQueue(),
                   graph_search=graph_search,
                   node_factory=SearchNodeHeuristicOrdered)


def astar_search(problem, graph_search=False):
    return _search(problem,
                   BoundedPriorityQueue(),
                   graph_search=graph_search,
                   node_factory=SearchNodeStarOrdered)


def _all_expander(fringe, problem):
    for node in fringe:
        fringe.extend(node.expand())


def beam_search(problem, beam_size=100, iterations_limit=0):
    return _local_search(problem,
                         _all_expander,
                         iterations_limit=iterations_limit,
                         fringe_size=beam_size)


def _first_expander(fringe, problem):
    fringe.extend(fringe[0].expand())


def beam_search_best_first(problem, beam_size=100, iterations_limit=0):
    return _local_search(problem,
                         _first_expander,
                         iterations_limit=iterations_limit,
                         fringe_size=beam_size)


def hill_climbing(problem, iterations_limit=0):
    return _local_search(problem,
                         _first_expander,
                         iterations_limit=iterations_limit,
                         fringe_size=1)


def _random_best_expander(fringe, problem):
    current = fringe[0]
    betters = [n for n in current.expand()
               if problem.value(n) > problem.value(current)]
    if betters:
        random.shuffle(betters)
        fringe.append(betters[0])


def hill_climbing_stochastic(problem, iterations_limit=0):
    '''Stochastic hill climbing, where a random neighbor is chosen among
       those that have a better value'''
    return _local_search(problem,
                         _random_best_expander,
                         iterations_limit=iterations_limit,
                         fringe_size=1)


def hill_climbing_random_restarts(problem, restarts_limit, iterations_limit=0):
    restarts = 0
    best = None
    while restarts < restarts_limit:
        new = hill_climbing(problem, iterations_limit=iterations_limit)
        if not best or problem.value(best) < problem.value(new):
            best = new

        restarts += 1

    return best


# Quite literally copied from aima
def simulated_annealing(problem, schedule=None):
    if not schedule:
        schedule = _exp_schedule()
    current = SearchNode(problem.initial_state,
                         problem=problem)
    for t in count():
        T = schedule(t)
        if T == 0:
            return current
        neighbors = current.expand()
        if not neighbors:
            return current
        succ = random.choice(neighbors)
        delta_e = problem.value(succ.state) - problem.value(current.state)
        if delta_e > 0 or random.random() < math.exp(delta_e / T):
            current = succ


def genetic_search(problem, limit=1000, pmut=0.1, populationsize=100):
    population = [problem.generate_random_state()
                  for _ in xrange(populationsize)]
    for _ in xrange(limit):
        new = []
        fitness = [problem.value(x) for x in population]
        sampler = Inverse_transform_sampler(fitness, population)
        for _ in population:
            node1 = sampler.sample()
            node2 = sampler.sample()
            child = problem.crossover(node1, node2)
            if random.random() < pmut:
                # Noooouuu! she is... he is... *IT* is a mutant!
                child = problem.mutate(child)
            new.append(child)
        population = new
    best = max(population, key=lambda x: problem.value(x))
    return SearchNode(state=best, problem=problem)


def _iterative_limited_search(problem, search_method, graph_search=False):
    solution = None
    limit = 0

    while not solution:
        solution = search_method(problem, limit, graph_search)
        limit += 1

    return solution


def _search(problem, fringe, graph_search=False, depth_limit=None,
            node_factory=SearchNode):
    memory = set()
    fringe.append(node_factory(state=problem.initial_state,
                               problem=problem))

    while fringe:
        node = fringe.pop()
        if problem.is_goal(node.state):
            return node
        if depth_limit is None or node.depth < depth_limit:
            childs = []
            for n in node.expand():
                if graph_search:
                    if n.state not in memory:
                        memory.add(n.state)
                        childs.append(n)
                else:
                    childs.append(n)

            for n in childs:
                fringe.append(n)


def _local_search(problem, fringe_expander, iterations_limit=0, fringe_size=1):
    fringe = BoundedPriorityQueue(fringe_size)
    fringe.append(SearchNodeValueOrdered(state=problem.initial_state,
                                         problem=problem))

    iterations = 0
    run = True
    best = None
    while run:
        old_best = fringe[0]
        fringe_expander(fringe, problem)
        best = fringe[0]

        iterations += 1

        if iterations_limit and iterations >= iterations_limit:
            run = False
        elif problem.value(old_best) >= problem.value(best):
            run = False

    return best


# Math literally copied from aima-python
def _exp_schedule(k=20, lam=0.005, limit=100):
    "One possible schedule function for simulated annealing"
    def f(t):
        if t < limit:
            return k * math.exp(-lam * t)
        return 0
    return f
