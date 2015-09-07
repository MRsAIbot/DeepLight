"""
Author: Tobias Rijken

This file contains the classes that define different state spaces

"""

import math
import numpy as np
import traci

class State(object):
	"""docstring for State"""
	def __init__(self, junctionID):
		super(State, self).__init__()
		self.junctionID = junctionID
		self.netBoundary = self._getNetBoundary()
		self.carState = np.zeros((84,84))
		self.lightState = np.zeros((84,84))
		# self.scalingFactor = self.netBoundary[1][0]/84
		self.scalingFactor = abs(self.netBoundary[1][0]-self.netBoundary[0][0])/84
		self.lightLocation = self._loadLightLocation(self.junctionID)
		self.scaledLightLocationX = int(self.lightLocation[0]/self.scalingFactor)
		self.scaledLightLocationY = int(self.lightLocation[1]/self.scalingFactor)
		self.lightShape = self._loadLightShape(self.junctionID)
		self.lightStates = ["GGgrrrrGGG", "GGGrrrrrrr", "rrrGGGGrrr"]
		self.lightRYGState = self._getLightRYGState(self.junctionID)
		# self.lightIndex = self.lightStates.find(self.lightRYGState)+1
		self.vehicleDict = {}

	def updateState(self, vehicleList):
		self._updateCarState(vehicleList)
		# self._scale()
		# self._updateTFLState()

	# def _updateCarState(self, vehicleList):
	# 	self._loadCarLocation(vehicleList)
	# 	self.carState = np.zeros((84,84))
	# 	for car in self.vehicleDict:
	# 		X = self.vehicleDict[car][0]//self.scalingFactor
	# 		print self.vehicleDict[car][0]
	# 		print X
	# 		Y = self.vehicleDict[car][1]//self.scalingFactor
	# 		print self.vehicleDict[car][1]
	# 		print Y
	# 		self.carState[X][Y] = 1

	def _updateCarState(self, vehicleList):
		self._loadCarLocation(vehicleList)
		self.carState = np.zeros((84,84))
		for car in self.vehicleDict:
			X = (self.vehicleDict[car][0]-self.netBoundary[0][0])//self.scalingFactor
			Y = (self.vehicleDict[car][1]-self.netBoundary[0][1])//self.scalingFactor
			self.carState[X][Y] = 1

	def _updateTFLState(self):
		self.lightRYGState = self._getLightRYGState(self.junctionID)
		lightStateIndex = self.lightStates.index(self.lightRYGState)+1
		# print "Light state index: {}".format(lightStateIndex)
		self.lightState[self.scaledLightLocationX][self.scaledLightLocationY] = lightStateIndex

	def _scale(self):
		pass

	def _getNetBoundary(self):
		return traci.simulation.getNetBoundary()

	def _loadLightLocation(self, junctionID):
		return traci.junction.getPosition(junctionID)

	def _loadLightShape(self, junctionID):
		return traci.junction.getShape(junctionID)

	def _getLightRYGState(self, junctionID):
		return traci.trafficlights.getRedYellowGreenState(junctionID)

	def _loadCarLocation(self, vehicleList):
		self.vehicleDict = {}
		for vehicle in vehicleList:
			self.vehicleDict[vehicle] = traci.vehicle.getPosition(vehicle)

	def _garbagaCollect(self, vehicleList):
		'''
		NOW OBSOLETE
		Removes references to vehicles when they leave the simulation
		'''
		for vehicle in self.vehicleDict:
			if vehicle not in vehicleList:
				del self.vehicleDict[vehicle]

class State1D(object):
	"""docstring for State1D"""
	def __init__(self, junctionID):
		self.junctionID = junctionID
		self.netBoundary = self._getNetBoundary()
		self.lanes = traci.lane.getIDList()
		self.upstreamLanes = ("3:1_0", "3:1_1", "0:1_0", "0:1_1", "5:1_0")
		self.laneDict = self._getLaneDict(self.upstreamLanes)
		self.laneState = self._initialise1Dstate()
		self.carState = np.zeros((84,84))
		self.lightState = np.zeros((84,84))
		self.scalingFactor = self.netBoundary[1][0]/84
		self.lightLocation = self._loadLightLocation(self.junctionID)
		self.scaledLightLocationX = int(self.lightLocation[0]/self.scalingFactor)
		self.scaledLightLocationY = int(self.lightLocation[1]/self.scalingFactor)
		self.lightShape = self._loadLightShape(self.junctionID)
		self.lightStates = ["GGgrrrrGGG", "GGGrrrrrrr", "rrrGGGGrrr"]
		self.lightRYGState = self._getLightRYGState(self.junctionID)
		# self.lightIndex = self.lightStates.find(self.lightRYGState)+1
		self.vehicleDict = {}

	def updateState(self, vehicleList):
		self._updateLaneState(vehicleList)
		# self._scale()
		# self._updateTFLState()

	def _updateCarState(self, vehicleList):
		self._loadCarLocation(vehicleList)
		self.carState = np.zeros((84,84))
		for car in self.vehicleDict:
			X = self.vehicleDict[car][0]//self.scalingFactor
			Y = self.vehicleDict[car][1]//self.scalingFactor
			self.carState[X][Y] = 1

	def _updateLaneState(self, vehicleList):
		self.laneState = self._initialise1Dstate()
		shortestLane = min(self.laneDict.itervalues())
		for car in vehicleList:
			carLaneID = traci.vehicle.getLaneID(car)
			if carLaneID in self.upstreamLanes:
				distance = self._distanceToLaneEnd(car)
				if distance < shortestLane - 1:
					l = self.upstreamLanes.index(carLaneID)
					d = int(math.floor(distance)/2)
					self.laneState[l][d] = 1

	def _distanceToLaneEnd(self, car):
		"""
		Returns the distance from the car to the end of the lane
		"""
		carLaneID = traci.vehicle.getLaneID(car)
		return traci.lane.getLength(carLaneID) - traci.vehicle.getLanePosition(car)

	def _updateTFLState(self):
		self.lightRYGState = self._getLightRYGState(self.junctionID)
		lightStateIndex = self.lightStates.index(self.lightRYGState)+1
		# print "Light state index: {}".format(lightStateIndex)
		self.lightState[self.scaledLightLocationX][self.scaledLightLocationY] = lightStateIndex

	def _getLaneDict(self, lanes):
		return {lanes[i]: traci.lane.getLength(lanes[i]) for i in range(len(lanes))}

	def _initialise1Dstate(self):
		laneCount = len(self.upstreamLanes)
		return np.zeros((laneCount, 84))

	def _scale(self):
		pass

	def _getNetBoundary(self):
		return traci.simulation.getNetBoundary()

	def _loadLightLocation(self, junctionID):
		return traci.junction.getPosition(junctionID)

	def _loadLightShape(self, junctionID):
		return traci.junction.getShape(junctionID)

	def _getLightRYGState(self, junctionID):
		return traci.trafficlights.getRedYellowGreenState(junctionID)

	def _loadCarLocation(self, vehicleList):
		self.vehicleDict = {}
		for vehicle in vehicleList:
			self.vehicleDict[vehicle] = traci.vehicle.getPosition(vehicle)

	def _garbagaCollect(self, vehicleList):
		'''
		NOW OBSOLETE
		Removes references to vehicles when they leave the simulation
		'''
		for vehicle in self.vehicleDict:
			if vehicle not in vehicleList:
				del self.vehicleDict[vehicle]
		

def main():
	a = State()
	print a.carState
	print a.lightState

if __name__ == '__main__':
	main()