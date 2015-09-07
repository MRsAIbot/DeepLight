"""
This file contains code to plot diagnostics that were saved to a pickle file.
We will use this to plot the data from the human-controlled agent. This is a
simple hack around an issue with trying to plot data in multi-threading after
the experiment

Example usage:

python plot_diagnostics data.pkl

"""
import cPickle
import itertools
import math
import matplotlib.pyplot as plt
import numpy as np
import sys

from evaluate_agent import AgentEvaluation

def main():
	with open(sys.argv[1], 'rb') as f:
		tmp = cPickle.load(f)
		routeDict = tmp[0]
		wait_count_list = tmp[1]
		traffic_light_dict = tmp[2]
		action_frequency = tmp[3]

	AE = AgentEvaluation(None, 'simpleT')

	AE.plot_route_dist(routeDict)
	AE.plot_route_diagnostics(routeDict)
	AE.plot_wait_count(wait_count_list)
	AE.plot_travel_time_dist(routeDict)
	AE.plot_traffic_light_time(traffic_light_dict)
	print "Action frequency: {}".format(action_frequency)

if __name__ == '__main__':
	main()