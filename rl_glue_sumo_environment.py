"""
This uses the skeleton_environment.py file from the Python-codec of rl-glue
as a starting point.

The class implements an environment based on the rl-glue framework and the
Simulation of Urban MObility (SUMO).

Author: Tobias Rijken
"""

import itertools
import random
import sys
from collections import defaultdict
from rlglue.environment.Environment import Environment
from rlglue.environment import EnvironmentLoader as EnvironmentLoader
from rlglue.types import Observation
from rlglue.types import Action
from rlglue.types import Reward_observation_terminal

import subprocess
# Symlinked ~/Dropbox/UCL/MSc\ Project/TrafficControl/sumo to /usr/share/
sys.path.append('/usr/share/sumo/tools')
import traci
from simulation.SimpleT.statespace import State
from sumo_utils import VehicleTimer, checkVehBirth, checkVehKill
import matplotlib.pyplot as plt


class SumoEnvironment(Environment):
	"""docstring for SumoEnvironment"""
	def __init__(self, traffic_situation):
		super(SumoEnvironment, self).__init__()

		if traffic_situation == 'simpleT':
			# Actions for SimpleT
			self.stage01="GGgrrrrGGG"
			self.inter0102="GGgrrrryyy"
			self.stage02="GGGrrrrrrr"
			self.inter0203="yyyrrrrrrr"
			self.stage03="rrrGGGGrrr"
			self.inter0301="rrryyyyrrr"

			# self.Stages=[self.stage01, self.stage02, self.stage03];
			self.Stages = [self.stage01, self.inter0102, self.stage02, \
				self.inter0203, self.stage03, self.inter0301]
			self.sumoConfig = "simulation/SimpleT/simpleT.sumocfg"
			self.routeScript = "simulation/SimpleT/routeGenerator.py"

		elif traffic_situation == 'simpleX':
			# Actions for SimpleX
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

		self.sumoBinary = "sumo"

		self.vehicleDict = {}
		self.currentVehList = []
		self.previousVehList = []
		self.totalCumWaitingTime = 0
		self.speedDict = defaultdict(float)
		self.licycle = itertools.cycle(range(len(self.Stages)))
		self.stageIndex = 0 # Initialise stage index

		self.traciPORT = 8813

	def env_init(self):
		# return "VERSION RL-Glue-3.0 PROBLEMTYPE episodic DISCOUNTFACTOR 1.0 OBSERVATIONS INTS (0 1)  ACTIONS INTS (0 {})  REWARDS (-1.0 1.0)  EXTRA rl_glue_sumo_environment(Python) by Tobias Rijken.".format(len(self.Stages)-1)
		return "VERSION RL-Glue-3.0 PROBLEMTYPE episodic DISCOUNTFACTOR 1.0 OBSERVATIONS INTS (0 1)  ACTIONS INTS (0 1)  REWARDS (-1.0 1.0)  EXTRA rl_glue_sumo_environment(Python) by Tobias Rijken."

	def env_start(self):
		# Randomly generate new routes
		routeGenProcess = subprocess.Popen("python %s" % (self.routeScript), shell=True, stdout=sys.stdout)

		# Start SUMO
		sumoProcess = subprocess.Popen("%s -c %s --no-warnings" % (self.sumoBinary, self.sumoConfig), shell=True, stdout=sys.stdout)

		traci.init(self.traciPORT)
		self.state = State("1")

		# Reset these variables when episodes starts
		self.vehicleDict = {}
		self.currentVehList = []
		self.previousVehList = []
		self.totalCumWaitingTime = 0

		returnObs = Observation()
		returnObs.intArray = self.state.carState.flatten()
		self.simStep = 1

		return returnObs

	def env_step(self, thisAction):
		# Process action
		# self.stageIndex = thisAction.intArray[0]
		if thisAction.intArray[0] == 0:
			self.stageIndex = self.licycle.next()
		# print "stageIndex: {}".format(self.stageIndex)
		traci.trafficlights.setRedYellowGreenState("1", self.Stages[self.stageIndex])

		traci.simulationStep()
		self.simStep += 1
		# print "Simulation step: {}".format(self.simStep)

		self.currentVehList = traci.vehicle.getIDList()
		self.state.updateState(self.currentVehList)

		episodeTerminal=0

		# Check if state is terminal
		if traci.simulation.getMinExpectedNumber() == 0:
			theObs = Observation()
			theObs.intArray=self.state.carState.flatten()
			episodeTerminal=1
			traci.close()
		
		theObs=Observation()
		theObs.intArray=self.state.carState.flatten()
		
		returnRO=Reward_observation_terminal()
		returnRO.r=self.calculate_reward()
		# returnRO.r=self.calculate_delay()
		# print "Reward: {}".format(returnRO.r)
		returnRO.o=theObs
		returnRO.terminal=episodeTerminal

		killedVehicles = checkVehKill(self.vehicleDict)
		for vehicle in killedVehicles:
			del self.vehicleDict[vehicle]

		self.previousVehList = self.currentVehList
		
		return returnRO

	def env_cleanup(self):
		pass

	def env_message(self, in_message):
		"""
		The experiment will cause this method to be called.  Used
		to restart the SUMO environment. Otherwise, the system will
		be terminated because multiple SUMO sessions will be listening
		to the same port.
		"""

		#WE NEED TO DO THIS BECAUSE agent_end is not called
		# we run out of steps.
		if in_message.startswith("episode_end"):
			traci.close()
		elif in_message.startswith("finish_epoch"):
			traci.close()
		elif in_message.startswith("start_testing"):
			pass
		elif in_message.startswith("finish_testing"):
			traci.close()
		else:
			return "I don't know how to respond to your message"

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

	def calculate_speed_diff(self):
		"""
		Returns the cumulative speed difference between the allowed speed
		and the car's speed for every car
		"""
		cumulative_speed_diff = 0
		for car in self.currentVehList:
			speed_diff = traci.vehicle.getAllowedSpeed(car) - traci.vehicle.getSpeed(car)
			cumulative_speed_diff += speed_diff
		return -cumulative_speed_diff

	def identify_emergency_stop(self):
		"""
		Identifies if an emergency stop occurs and sums the decelerations
		of all the cars that make an emergency stop
		"""
		total_deceleration = 0
		for vehicle in self.currentVehList:
			a = traci.vehicle.getSpeed(vehicle) - self.speedDict[vehicle]
			if a < -4.5:
				total_deceleration += a
			self.speedDict[vehicle] = traci.vehicle.getSpeed(vehicle)
		return total_deceleration

	def calculate_reward(self, tau=100):
		"""
		Return a weighted sum of the speed diff reward and the emergency
		stop reward
		"""
		result = self.calculate_speed_diff() + \
			tau * self.identify_emergency_stop()
		return result

def main():
	EnvironmentLoader.loadEnvironment(SumoEnvironment(sys.argv[1]))

if __name__ == '__main__':
	main()