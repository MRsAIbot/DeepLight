"""
Author: Tobias Rijken
"""

import numpy as np
from pprint import pprint

import sys
sys.path.append('/usr/share/sumo/tools')
import traci

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
        self.routeID = traci.vehicle.getRouteID(vehid)
        self.cumWaitingTime = 0
        self.previousWaitingTime = 0
        self.travelTime = 0

    def incrementTravelTime(self):
        self.travelTime += 1
        return 0

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