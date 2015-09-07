"""
This file contains code to plot diagnostics from different agents.

Example usage:

python plot_comparison.py data1.pkl data2.pkl data3.pkl ...

"""
from collections import OrderedDict
import cPickle
import itertools
import math
import matplotlib.pyplot as plt
import numpy as np
import sys

def plot_wait_count(self, wait_count_list):
	# plt.plot(wait_count_list, 'bo', wait_count_list, 'b')
	plt.plot(wait_count_list, 'b')
	plt.xlabel('Simulation step')
	plt.ylabel('Number of waiting vehicles')
	plt.ylim(0,max(wait_count_list)+1)
	plt.show()
	return 0

def plot_cumulative_waiting(data_dict):
	for k,v in data_dict.items():
		plt.plot(np.cumsum(v[1]), label=k[5:-4])
	plt.xlabel('Simulation step')
	plt.ylabel('Total time spent waiting (seconds)')
	plt.legend(loc=2)
	plt.ylim(0,60000)
	plt.show()
	return 0

def plot_cumulative_es(data_dict):
	for k,v in data_dict.items():
		plt.plot(np.cumsum(v[4]), label=k[5:-7])
	plt.xlabel('Simulation step')
	plt.ylabel('Total number of emergency stops')
	plt.legend(loc=2)
	plt.xlim(0,10000)
	# plt.ylim(0,60000)
	plt.show()
	return 0

def load_pkl_file(filename):
	with open(filename, 'rb') as f:
		tmp = cPickle.load(f)
		routeDict = tmp[0]
		wait_count_list = tmp[1]
		traffic_light_dict = tmp[2]
		action_frequency = tmp[3]
	return tmp

def calculate_delay_dict(freeflow_dict, route_dict):
		delay_dict = {}
		for k in route_dict.keys():
			delay_dict[k] = [route_dict[k][i] - freeflow_dict[k] for i in \
				range(len(route_dict[k]))]
		return delay_dict

def calculate_mean_delay(delay_dict):
	tmp = []
	for k in delay_dict.keys():
		for l in delay_dict[k]:
			tmp.append(l)
	return np.mean(tmp)

def print_mean_delays(data_dict, ff_dict):
	for k,v in data_dict.items():
		delay_dict = calculate_delay_dict(ff_dict, v[0])
		print "Mean delay of {}: {}".format(k, calculate_mean_delay(delay_dict))
	return 0

def main():
	# freeflow_dict = {'eastSouth':40, 'eastWest':42, 'westSouth':40, \
	# 		'westEast':42, 'southEast':40, 'southWest':41}
	freeflow_dict = {'eastSouth':42, 'eastWest':42, 'eastNorth':41, \
			'westEast':42, 'westSouth':41, 'westNorth':42, \
			'southEast':41, 'southWest':42, 'southNorth':42, \
			'northEast':42, 'northWest':41, 'northSouth':42}
	pkl_files = sys.argv[1:]
	pkl_dict = OrderedDict()
	for f in pkl_files:
		v = load_pkl_file(f)
		pkl_dict[f] = v
	plot_cumulative_waiting(pkl_dict)
	plot_cumulative_es(pkl_dict)
	print_mean_delays(pkl_dict, freeflow_dict)
	

if __name__ == '__main__':
	main()