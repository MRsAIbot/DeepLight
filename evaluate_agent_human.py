"""

Author: Tobias Rijken

This file contains code to evaluate (and visualise) the performance
of a trained DQN on a SUMO traffic simulation

"""

import subprocess
import sys
# Symlinked ~/Dropbox/UCL/MSc\ Project/TrafficControl/sumo to /usr/share/
sys.path.append('/usr/share/sumo/tools')
import traci
import math
import matplotlib.pyplot as plt
import q_network
import cPickle
import cv2
import numpy as np
from collections import defaultdict
from simulation.SimpleT.statespace import State
from sumo_utils import VehicleTimer, checkVehBirth, checkVehKill

import threading
import os
import time
import itertools
import Queue

try : # on windows
	from msvcrt import getch
except ImportError : # on unix like systems
	import sys, tty, termios
	def getch() :
		fd = sys.stdin.fileno()
		old_settings = termios.tcgetattr(fd)
		try :
			tty.setraw(fd)
			ch = sys.stdin.read(1)
		finally :
			termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
		return ch

def control(commands):
	while True:
		command = getch()
		commands.put(command)

		if command == "q":
			break

class AgentEvaluation(object):
	"""docstring for AgentEvaluation"""

	def __init__(self, traffic_net, gui=True, epsilon=0.1):
		self.traffic_net = traffic_net
		self.epsilon = epsilon

		# SUMO settings
		self.PORT = 8813
		if gui:
			self.sumoBinary = "sumo-gui"
		else:
			self.sumoBinary = "sumo"

		if self.traffic_net == "simpleT":
			# Admissable traffic light configurations for SimpleT
			self.stage01="GGgrrrrGGG"
			self.inter0102="GGgrrrryyy"
			self.stage02="GGGrrrrrrr"
			self.inter0203="yyyrrrrrrr"
			self.stage03="rrrGGGGrrr"
			self.inter0301="rrryyyyrrr"

			self.Stages=[self.stage01, self.stage02, self.stage03]
			self.sumoConfig = "simulation/SimpleT/simpleT.sumocfg"
			self.routeScript = "simulation/SimpleT/routeGenerator.py"

		elif self.traffic_net == "simpleX":
			# Admissable traffic light configurations for SimpleX
			self.stage01="GGGGggrrrrrrGGGGggrrrrrr"
			self.inter0102="yyyyggrrrrrryyyyggrrrrrr"
			self.stage02="rrrrGGrrrrrrrrrrGGrrrrrr"
			self.inter0203="rrrryyrrrrrrrrrryyrrrrrr"
			self.stage03="rrrrrrGGGGggrrrrrrGGGGgg"
			self.inter0304="rrrrrryyyyggrrrrrryyyygg"
			self.stage04="rrrrrrrrrrGGrrrrrrrrrrGG"
			self.inter0401="rrrrrrrrrryyrrrrrrrrrryy"

			self.Stages=[self.stage01, self.stage02, self.stage03, self.stage04];
			self.sumoConfig = "simulation/SimpleX/simpleX.sumocfg"
			self.routeScript = "simulation/SimpleX/routeGenerator.py"

		self.admissable_index = range(len(self.Stages))

	def calculate_delay(self):
		birthList = checkVehBirth(self.currentVehList, self.previousVehList)
		# print "New born vehicles: {0}".format(birthList)

		totalWaitingTime = 0

		if birthList != []:
			for veh in birthList:
				self.vehicleDict[veh] = VehicleTimer(veh)
		# print "Vehicle dictionary: {0}".format(self.vehicleDict)

		for key in self.vehicleDict:
			inc = self.vehicleDict[key].incrementWaitingTime()
			# print "Delta for car {0}: {1}".format(key, inc)
			totalWaitingTime += inc
			# print "Cum. Waiting time for veh {0}: {1}".format(key, self.vehicleDict[key].cumWaitingTime)
		# print "Total cumulative waiting time: {0}".format(self.totalCumWaitingTime)

		# Return negative reward
		self.totalCumWaitingTime += -totalWaitingTime
		return -totalWaitingTime

	def plot_route_diagnostics(self, routeDict):
		"""
		Plots the mean and median of time duration of every route
		"""
		vectors = []
		labels = []
		for i in routeDict.keys():
			vectors.append(routeDict[i])
			labels.append(i)
		plt.boxplot(vectors)
		plt.xticks(range(1,len(routeDict.keys())+1), labels)
		plt.title('Distribution route times')
		plt.ylabel('Time to complete a route')
		plt.show()

	def plot_route_dist(self, routeDict):
		"""
		Plots a distribution for the different routes
		"""
		route_ids = routeDict.keys()
		max_route = max(list(itertools.chain.from_iterable(routeDict.values())))
		sqrt_factor1 = math.ceil(math.sqrt(len(route_ids)))

		if sqrt_factor1*(sqrt_factor1-1) >= len(route_ids):
			sqrt_factor2 = sqrt_factor1-1

		for i,name in enumerate(route_ids):
			ax = plt.subplot(sqrt_factor2, sqrt_factor1, i+1)
			ax.hist(routeDict[route_ids[i]], bins=10)
			ax.set_title('Route: {}'.format(name))
			ax.set_xlim(0,max_route)

		plt.show()
		return 0

	def plot_travel_time_dist(self, routeDict):
		"""
		Plots the distribution for the travel times regardless of the route
		"""
		temp = [v for k,v in routeDict.items()]
		cum_travel_times = [item for sublist in temp for item in sublist]
		plt.hist(cum_travel_times, bins=10)
		plt.xlabel('Travel times')
		plt.ylabel('Number of vehicles')
		plt.show()
		return 0

	def plot_actions(self, actionList):
		x = np.array(range(1,len(actionList)+1))
		y = np.array(actionList)
		plt.scatter(x, y)
		plt.xlabel('Simulation step')
		plt.ylabel('Action index')
		plt.title('Actions taken')
		plt.show()
		return 0

	def plot_wait_count(self, wait_count_list):
		# plt.plot(wait_count_list, 'bo', wait_count_list, 'b')
		plt.plot(wait_count_list, 'b')
		plt.xlabel('Simulation step')
		plt.ylabel('Number of waiting vehicles')
		plt.ylim(0,max(wait_count_list)+1)
		plt.show()
		return 0

	def plot_traffic_light_time(self, traffic_light_dict):
		"""
		Plots the distribution of seconds each traffic state is active
		"""
		vectors = []
		labels = []
		for i in traffic_light_dict.keys():
			vectors.append(traffic_light_dict[i])
			labels.append(self.Stages[i])
		plt.boxplot(vectors)
		plt.xticks(range(1,len(traffic_light_dict.keys())+1), labels)
		plt.ylabel("Number of seconds")
		plt.show()
		return 0

	def action_freq(self, actionList, time):
		L = [x for x, y in itertools.groupby(actionList)]
		freq = float(len(L))/time
		return freq
	
	def run(self, commands):
		# Randomly generate new routes
		# routeGenProcess = subprocess.Popen("python %s" % (self.routeScript), shell=True, stdout=sys.stdout)

		# Start SUMO
		sumoProcess = subprocess.Popen("%s -c %s" % (self.sumoBinary, self.sumoConfig), shell=True, stdout=sys.stdout)
		traci.init(self.PORT)

		state = State("1")

		# Reset these variables when episodes starts
		mapCarToRoute = {}
		routeDict = defaultdict(list)
		traveltimeDict = defaultdict(int)
		traffic_light_dict = defaultdict(list)
		vehicleDict = {}
		currentVehList = []
		previousVehList = []
		totalCumWaitingTime = 0
		actionList = []
		wait_count_list = []
		previous_index = 0
		traffic_light_counter = 1
		speedDict = defaultdict(float)
		emergency_stop_list = []

		step = 0
		self.last_action = 0
		# run simulation until it reaches a terminal state
		while step == 0 or traci.simulation.getMinExpectedNumber() > 0:
			
			if step == 0:
				observation = state.carState.flatten()

			# TAKE THE HUMAN ACTION HERE
			# print "1"
			try:
				stageIndex = int(commands.get(False))
				# print "2"
			except Queue.Empty, e:
				stageIndex = self.last_action
				# print "3"
			print "Index: {}".format(stageIndex)

			if stageIndex not in self.admissable_index:
				print "admissable_index: {}".format(self.admissable_index)
				stageIndex = self.last_action
			self.last_action = stageIndex
			# print "4"

			# print "Index: {}".format(stageIndex)
			actionList.append(stageIndex)
			# print "stageIndex: {}".format(stageIndex)
			traci.trafficlights.setRedYellowGreenState("1", self.Stages[stageIndex])

			# Count time a specific stage index has been active
			if step == 0:
				previous_index = stageIndex
			if stageIndex == previous_index:
				traffic_light_counter += 1
			else:
				traffic_light_dict[previous_index].append(traffic_light_counter)
				traffic_light_counter = 1

			traci.simulationStep()

			currentVehList = traci.vehicle.getIDList()
			state.updateState(currentVehList)

			observation = state.carState.flatten()

			# Increment wait count
			wait_count = 0
			for car in currentVehList:
				if traci.vehicle.getWaitingTime(car) > 0:
					wait_count += 1
			wait_count_list.append(wait_count)

			# Detect emergency stop
			es_count = 0
			for vehicle in currentVehList:
				a = traci.vehicle.getSpeed(vehicle) - speedDict[vehicle]
				if a < -4.5:
					es_count += 1
				speedDict[vehicle] = traci.vehicle.getSpeed(vehicle)
			emergency_stop_list.append(es_count)

			# Increment traveltime for all cars
			for car in currentVehList:
				if car not in mapCarToRoute.keys():
					mapCarToRoute[car] = traci.vehicle.getRouteID(car)
				traveltimeDict[car] += 1

			# Add traveltime to routeDict, then delete entry from
			# the traveltimeDict
			for car in traveltimeDict.keys():
				if car not in currentVehList:
					route_id = mapCarToRoute[car]
					routeDict[route_id].append(traveltimeDict[car])
					del traveltimeDict[car]
					del mapCarToRoute[car]

			previousVehList = currentVehList
			previous_index = stageIndex
			
			step += 1

		# Produce plots
		# self.plot_route_dist(routeDict)
		# # self.plot_actions(actionList)
		# self.plot_route_diagnostics(routeDict)
		# self.plot_wait_count(wait_count_list)
		# self.plot_travel_time_dist(routeDict)
		# self.plot_traffic_light_time(traffic_light_dict)
		action_frequency = self.action_freq(actionList, step)

		with open('eval_human_X.pkl', 'wb') as f:
			cPickle.dump([routeDict, wait_count_list, \
				traffic_light_dict, action_frequency, \
				emergency_stop_list], f)

		action_frequency = self.action_freq(actionList, step)
		print "Action frequency: {}".format(action_frequency)

		traci.close()
		sys.stdout.flush()


def main():
	commands = Queue.Queue(0)
	traffic_net = sys.argv[1]
	agent_evaluation = AgentEvaluation(traffic_net)

	controller = threading.Thread(None, control, None, (commands,), {})
	evaluator = threading.Thread(None, agent_evaluation.run, None, (commands,), {})
	controller.start()
	evaluator.start()

	# agent_evaluation.run(commands)

if __name__ == '__main__':
	main()