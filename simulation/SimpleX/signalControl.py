#!/usr/bin/env python
"""
@file    signalControl.py
@author  Simon Box
@date    31/01/2013

Code to control the traffic lights in the "simpleT" SUMO model.

"""

import subprocess, sys
# Symlinked ~/Dropbox/UCL/MSc\ Project/TrafficControl/sumo to /usr/share/
sys.path.append('/usr/share/sumo/tools')
import traci
from statespace import State, State1D
import matplotlib.pyplot as plt

##############

def fullprint(*args, **kwargs):
    from pprint import pprint
    import numpy as np
    opt = np.get_printoptions()
    np.set_printoptions(threshold='nan')
    pprint(*args, **kwargs)
    np.set_printoptions(**opt)

def prettyprint(x):
    for row in x:
        print '[%s]' % (' '.join('%d' % i for i in row))

class VehicleTimer(object):
    """docstring for vehicleTimer"""
    def __init__(self, vehid):
        # super(vehicleTimer, self).__init__()
        self.vehid = vehid
        self.route = traci.vehicle.getRoute(vehid)
        self.cumWaitingTime = 0
        self.previousWaitingTime = 0

    # def incrementWaitingTime(self):
    #     currentWaitingTime = traci.vehicle.getWaitingTime(self.vehid)
    #     if currentWaitingTime == 0 and self.previousWaitingTime > 0:
    #         self.cumWaitingTime += self.previousWaitingTime
    #     self.previousWaitingTime = currentWaitingTime

    def incrementWaitingTime(self):
        currentWaitingTime = traci.vehicle.getWaitingTime(self.vehid)
        if currentWaitingTime - self.previousWaitingTime > 0:
            deltaWaitingTime = currentWaitingTime - self.previousWaitingTime
            self.cumWaitingTime += deltaWaitingTime
        else:
            deltaWaitingTime = 0
        # deltaWaitingTime = currentWaitingTime - self.previousWaitingTime
        self.previousWaitingTime = currentWaitingTime
        # if deltaWaitingTime >= 0:
        #     self.cumWaitingTime += deltaWaitingTime
        return deltaWaitingTime

    def passedTrafficLight(self):
        '''
        self -> bool
        '''
        upStreamEdges = ("7:3", "3:1", "2:0", "0:1", "6:5", "5:1")
        downStreamEdges = ("1:3", "1:5", "1:0")
        if traci.vehicle.getRoadID(self.vehid) not in upStreamEdges:
            return True
        else:
            return False


def checkVehBirth(currentVehs, previousVehs):
    return [x for x in currentVehs if x not in previousVehs]

def checkVehKill(vehicleDict):
    killedVehicles = []
    for vehicle in vehicleDict:
        if vehicleDict[vehicle].passedTrafficLight():
            killedVehicles.append(vehicle)
    return killedVehicles

##############

PORT = 8813

# stage01="GGgrrrrGGG"
# inter0102="GGgrrrryyy"
# stage02="GGGrrrrrrr"
# inter0203="yyyrrrrrrr"
# stage03="rrrGGGGrrr"
# inter0301="rrryyyyrrr"

stage01="GGGGggrrrrrrGGGGggrrrrrr"
inter0102="yyyyggrrrrrryyyyggrrrrrr"
stage02="rrrrGGrrrrrrrrrrGGrrrrrr"
inter0203="rrrryyrrrrrrrrrryyrrrrrr"
stage03="rrrrrrGGGGggrrrrrrGGGGgg"
inter0304="rrrrrryyyyggrrrrrryyyygg"
stage04="rrrrrrrrrrGGrrrrrrrrrrGG"
inter0401="rrrrrrrrrryyrrrrrrrrrryy"

Stages=[stage01,stage02, stage03, stage04];

sumoBinary = "sumo-gui"
sumoConfig = "simpleX.sumocfg"

sumoProcess = subprocess.Popen("%s -c %s" % (sumoBinary, sumoConfig), shell=True, stdout=sys.stdout)

traci.init(PORT)

#################
vehicleDict = {}

previousVehList = []

totalCumWaitingTime = 0

state = State("1")
print "Traffic light ID: {}".format(state.junctionID)
print "Traffic light location: {}".format(state.lightLocation)
print "Traffic light X: {}".format(state.scaledLightLocationX)
print "Traffic light Y: {}".format(state.scaledLightLocationY)
print "Traffic light shape: {}".format(state.lightShape)
print "Net Boundary: {}".format(state.netBoundary)
print "Traffic light state: {}".format(state.lightRYGState)
# print "Traffic light index: {}".format(state.lightIndex)
print "Traffic light state: {}".format(state.lightState[42][39])
# prettyprint(state.lightState)

# state1D = State1D("1")
# print "Traffic lanes: {}".format(state1D.lanes)
# print "Lanestete shape: {}".format(state1D.laneState.shape)

##################

# print traci.trafficlights.getCompleteRedYellowGreenDefinition("1")
# print traci.trafficlights.getRedYellowGreenState("1")

step = 0
lastSwitch=0;
stageIndex = 0;
while step == 0 or traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep(step=0.001) # what happens if parameter 'step' is changed?
    timeNow = traci.simulation.getCurrentTime()    
    if timeNow-lastSwitch > 30000:
        if stageIndex==0:
            stageIndex = 1
        elif stageIndex == 1:
            stageIndex = 2
        elif stageIndex == 2:
            stageIndex = 3
        else:
            stageIndex = 0
        traci.trafficlights.setRedYellowGreenState("1", Stages[stageIndex])
        lastSwitch = timeNow # Added by Tobias
    

    ############# PLAYING AROUND ###############
    # State space
    
    currentVehList = traci.vehicle.getIDList()
    print currentVehList
    print previousVehList

    """
    state1D.updateState(currentVehList)
    prettyprint(state1D.laneState)
    plt.imshow(state1D.laneState, interpolation='nearest')
    plt.show()
    """
    state.updateState(currentVehList)
    print "Vehicle in state: {}".format(state.vehicleDict)
    print "Traffic light state: {}".format(state.lightState[42][39])
    # prettyprint(state.lightState)
    print "Car state: "
    prettyprint(state.carState)
    plt.imshow(state.carState, interpolation='nearest')
    plt.show()

    birthList = checkVehBirth(currentVehList, previousVehList)
    print "New born vehicles: {0}".format(birthList)

    if birthList != []:
        for veh in birthList:
            vehicleDict[veh] = VehicleTimer(veh)
    print "Vehicle dictionary: {0}".format(vehicleDict)

    for key in vehicleDict:
        inc = vehicleDict[key].incrementWaitingTime()
        print "Delta for car {0}: {1}".format(key, inc)
        totalCumWaitingTime += inc
        print "Cum. Waiting time for veh {0}: {1}".format(key, vehicleDict[key].cumWaitingTime)
    print "Total cumulative waiting time: {0}".format(totalCumWaitingTime)


    # Cumulative reward

    cum_speed_diff = 0
    for vehicle in currentVehList:
        # print "Road ID for vehicle {0}: {1}".format(vehicle, traci.vehicle.getRoadID(vehicle))
        # print "Location of vehicle {0}: {1}".format(vehicle, traci.vehicle.getPosition(vehicle))
        # Reward
        speed_diff = traci.vehicle.getAllowedSpeed(vehicle) - traci.vehicle.getSpeed(vehicle)
        # print "Speed difference for vehicle {0}: {1}".format(vehicle, speed_diff)
        cum_speed_diff += speed_diff
    # print "Cumulative speed difference: {0}".format(cum_speed_diff)

    # Kill death vehicles
    killedVehicles = checkVehKill(vehicleDict)
    for vehicle in killedVehicles:
        # totalCumWaitingTime += vehicleDict[vehicle].cumWaitingTime
        del vehicleDict[vehicle]

    # print "Total cumulative waiting time: {0}".format(totalCumWaitingTime)

    previousVehList = currentVehList
    


    #############################################

    step += 1

traci.close()
sys.stdout.flush()
