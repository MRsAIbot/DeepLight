"""

Author: Tobias Rijken

This file contains code to evaluate (and visualise) the performance
of a trained DQN on a SUMO traffic simulation

"""

import subprocess, sys
# Symlinked ~/Dropbox/UCL/MSc\ Project/TrafficControl/sumo to /usr/share/
sys.path.append('/usr/share/sumo/tools')
import traci
import math
import matplotlib.pyplot as plt
import q_network
import cPickle
import cv2
import itertools
import numpy as np
import lasagne.layers
import random
import time
import theano
import theano.tensor as T
from collections import defaultdict
from simulation.SimpleT.statespace import State, State1D
# from simulation.SimpleX.statespace import State1D

from sumo_utils import VehicleTimer, checkVehBirth, checkVehKill

class AgentEvaluation(object):
	"""docstring for AgentEvaluation"""

	def __init__(self, nn_file, traffic_net, gui=True, epsilon=0.1, tsne_dataset=False):
		self.nn_file = nn_file
		self.traffic_net = traffic_net
		self.network = self.load_network()
		self.epsilon = epsilon
		self.tsne_dataset = tsne_dataset

		self.IMAGE_HEIGHT = 84
		self.IMAGE_WIDTH = 84
		# self.IMAGE_HEIGHT = 8
		# self.IMAGE_WIDTH = 1

		self.gui = gui

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
			# self.Stages=[self.stage01, self.inter0102, self.stage02, \
			# 	self.inter0203, self.stage03, self.inter0301]
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

		if self.tsne_dataset:
			self._load_layers()
			self.sym_x = T.tensor4('states')
			self.q_last_hidden = lasagne.layers.get_output(self.q_layers[-2], \
				self.sym_x)
			self.states_shared = theano.shared(np.zeros((1,1,self.IMAGE_HEIGHT, \
				self.IMAGE_WIDTH), dtype=theano.config.floatX))
			self.q_vals_fun = theano.function([], self.q_last_hidden, \
				givens={self.sym_x: self.states_shared})
			self.label_list = []

	def load_network(self):
		"""
		Takes the first argument from the command line. This should be a network
		pickle file. The function will unpickle it and return the network.
		"""
		if self.nn_file == None:
			return 0
		else:
			nn_file = self.nn_file
			handle = open(nn_file, 'r')
			network = cPickle.load(handle)
			handle.close()

			return network

	def _load_layers(self):
		self.q_layers = lasagne.layers.get_all_layers(self.network.l_out)
		return 0

	def reshape_output(self, output):
		"""
		Reshapes the output to fit the Theano tensor4
		"""
		reshaped_output = output.reshape((1,1,self.IMAGE_HEIGHT, \
			self.IMAGE_WIDTH))
		reshaped_output = reshaped_output.astype(theano.config.floatX)
		return reshaped_output

	def _resize_observation(self, observation):
		"""
		Preprocesses the numpy array that represents an observation
		"""
		# reshape linear to original image size, skipping the RAM portion
		image = observation.reshape(self.IMAGE_HEIGHT, self.IMAGE_WIDTH)
		# convert from int32s
		image = np.array(image, dtype="uint8")

		return image

	def get_activations(self):
		return self.q_vals_fun()

	def take_action(self, observation):
		"""
		Takes an action following an epsilon greedy policy
		"""
		phi = self._resize_observation(observation)
		int_action = self.network.choose_action(phi, self.epsilon)

		return int_action

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
		plt.title('Distribution of route times')
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
		plt.plot(x, y)
		plt.xlabel('Simulation step')
		plt.ylabel('Action index')
		plt.title('Actions taken')
		plt.show()
		return 0

	def plot_wait_count(self, wait_count_list):
		plt.plot(wait_count_list, 'b')
		plt.xlabel('Simulation step')
		plt.ylabel('Number of waiting vehicles')
		plt.ylim(0,max(wait_count_list)+1)
		plt.show()
		return 0

	def plot_emergency_count(self, emergency_count_list):
		plt.plot(np.cumsum(emergency_count_list), 'b')
		plt.xlabel('Simulation step')
		plt.ylabel('Number of emergency stops')
		# plt.ylim(0,max(emergency_count_list)+1)
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

	def calculate_delay_dict(self, freeflow_dict, route_dict):
		delay_dict = {}
		for k in route_dict.keys():
			delay_dict[k] = [route_dict[k][i] - freeflow_dict[k] for i in \
				range(len(route_dict[k]))]
		return delay_dict

	def calculate_mean_delay(self, delay_dict):
		tmp = []
		for k in delay_dict.keys():
			for l in delay_dict[k]:
				tmp.append(l)
		return np.mean(tmp)
	
	def run(self, save=False):
		# Randomly generate new routes
		routeGenProcess = subprocess.Popen("python %s" % (self.routeScript), shell=True, stdout=sys.stdout)

		# Start SUMO
		sumoProcess = subprocess.Popen("%s -c %s" % (self.sumoBinary, self.sumoConfig), shell=True, stdout=sys.stdout)
		traci.init(self.PORT)

		state = State("1")
		state1d = State1D("1")

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
		licycle = itertools.cycle(range(len(self.Stages)))
		speedDict = defaultdict(float)
		emergency_stop_list = []
		# freeflow_dict = {'eastSouth':40, 'eastWest':42, 'westSouth':40, \
		# 	'westEast':42, 'southEast':40, 'southWest':41}
		freeflow_dict = {'eastSouth':42, 'eastWest':42, 'eastNorth':41, \
			'westEast':42, 'westSouth':41, 'westNorth':42, \
			'southEast':41, 'southWest':42, 'southNorth':42, \
			'northEast':42, 'northWest':41, 'northSouth':42}

		if self.gui:
			self.view = traci.gui.getIDList()[0]

		step = 0
		# stageIndex = 2
		# run simulation until it reaches a terminal state
		while step == 0 or traci.simulation.getMinExpectedNumber() > 0:
			# print "Step: {}".format(step)
			if step == 0:
				observation = state.carState.flatten()
				# observation = state1d.laneState.sum(axis=1)
				# print observation

			# plt.imshow(state.carState, interpolation='nearest')
			# plt.show()

			# stageIndex = self.take_action(observation)
			# if step % 10 == 0:
				# stageIndex = licycle.next()
			# if self.take_action(observation) == 0:
			# 	stageIndex = licycle.next()
			stageIndex = random.choice(range(len(self.Stages)))

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

			# Take a step
			traci.simulationStep()

			currentVehList = traci.vehicle.getIDList()
			state.updateState(currentVehList)
			# state1d.updateState(currentVehList)

			observation = state.carState.flatten()
			# observation = state1d.laneState.sum(axis=1)
			# print observation

			# Get the activations of the last hidden layer
			if self.tsne_dataset:
				# Get high level representation
				o = state.carState
				reshaped_o = self.reshape_output(o)
				self.states_shared.set_value(reshaped_o)
				activations = self.get_activations()
				# Add activations to array
				if hasattr(self, 'activation_X'):
					self.activation_X = np.vstack((self.activation_X, \
						activations))
				else:
					self.activation_X = activations

				# Get value/label
				q_val_outputs = self.network.q_vals(o)
				activation_labels = sum(q_val_outputs)
				self.label_list.append(activation_labels)

				# If value is interesting, save screen shot
				traci.gui.screenshot(self.view, 'tsne/screenshots/step_'+'{}'.format(step)+'.png')

			# Increment wait count and calculate speed diffs
			cumulative_speed_diff = 0
			wait_count = 0
			for car in currentVehList:
				if traci.vehicle.getWaitingTime(car) > 0:
					wait_count += 1
				speed_diff = traci.vehicle.getAllowedSpeed(car) - traci.vehicle.getSpeed(car)
				cumulative_speed_diff += speed_diff
			wait_count_list.append(wait_count)

			# Detect emergency stop
			total_deceleration = 0
			es_count = 0
			for vehicle in currentVehList:
				a = traci.vehicle.getSpeed(vehicle) - speedDict[vehicle]
				if a < -4.5:
					es_count += 1
					total_deceleration += a
				speedDict[vehicle] = traci.vehicle.getSpeed(vehicle)
			emergency_stop_list.append(es_count)

			# Calculate reward
			result = -cumulative_speed_diff + 100 * total_deceleration
			print "Reward: {}".format(result)

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

			"""
			# NOW OBSOLETE
			birthList = checkVehBirth(self.currentVehList, self.previousVehList)

			if birthList != []:
				for veh in birthList:
					self.vehicleDict[veh] = VehicleTimer(veh)

			for key in self.vehicleDict:
				inc = self.vehicleDict[key].incrementWaitingTime()
				totalWaitingTime += inc

			killedVehicles = checkVehKill(vehicleDict)
			for vehicle in killedVehicles:
				del vehicleDict[vehicle]
			"""

			previousVehList = currentVehList
			previous_index = stageIndex
			
			step += 1

		delay_dict = self.calculate_delay_dict(freeflow_dict, routeDict)

		# Produce plots
		self.plot_route_dist(routeDict)
		self.plot_actions(actionList)
		self.plot_route_diagnostics(routeDict)
		self.plot_wait_count(wait_count_list)
		self.plot_travel_time_dist(routeDict)
		self.plot_traffic_light_time(traffic_light_dict)
		self.plot_emergency_count(emergency_stop_list)
		print traffic_light_dict 

		action_frequency = self.action_freq(actionList, step)
		print "Action frequency: {}".format(action_frequency)

		print "Mean delay: {}".format(self.calculate_mean_delay(delay_dict))

		if save:
			with open('eval_1D_LINEAR_T.pkl', 'wb') as f:
				cPickle.dump([routeDict, wait_count_list, \
					traffic_light_dict, action_frequency, \
					emergency_stop_list], f)

		if self.tsne_dataset:
			if not traci.simulation.getMinExpectedNumber() > 0:
				# Pickle
				time_str = time.strftime("_%m-%d-%H-%M_", time.gmtime())
				with open('tsne/activations_X'+ time_str +'.pkl', 'wb') as f:
					cPickle.dump(self.activation_X, f, -1)

				with open('tsne/activations_Y'+ time_str +'.pkl', 'wb') as f:
					temp = np.asarray(self.label_list)
					cPickle.dump(temp, f)


		traci.close()
		sys.stdout.flush()


def main():
	nn_file = sys.argv[1]
	traffic_net = sys.argv[2]
	agent_evaluation = AgentEvaluation(nn_file, traffic_net, gui=True, tsne_dataset=False)
	agent_evaluation.run(save=False)

if __name__ == '__main__':
	main()