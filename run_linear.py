#! /usr/bin/env python
"""
Execute a training run of deep-Q-Leaning with parameters that
are consistent with:

Playing Atari with Deep Reinforcement Learning
NIPS Deep Learning Workshop 2013

"""

import launcher
import sys

class Defaults:
    # ----------------------
    # RLGlue Parameters
    # ----------------------
    RLGLUE_PORT = 4096
    
    # ----------------------
    # Experiment Parameters
    # ----------------------
    STEPS_PER_EPOCH = 50000
    EPOCHS = 100
    STEPS_PER_TEST = 10000
    
    # ----------------------
    # SUMO Parameters
    # ----------------------
    BASE_ROM_PATH = "../roms/"
    ROM = 'SUMO'
    FRAME_SKIP = 4
    
    # ----------------------
    # Agent/Network parameters:
    # ----------------------
    UPDATE_RULE = 'sgd'
    BATCH_ACCUMULATOR = 'mean'
    LEARNING_RATE = .0002 # .0002
    DISCOUNT = .95
    RMS_DECAY = .99 # (Rho)
    RMS_EPSILON = 1e-6
    MOMENTUM = 0
    EPSILON_START = 1.0
    EPSILON_MIN = .1
    EPSILON_DECAY = 1000000
    PHI_LENGTH = 1
    UPDATE_FREQUENCY = 1
    REPLAY_MEMORY_SIZE = 1000000
    BATCH_SIZE = 32
    NETWORK_TYPE = "linear"
    FREEZE_INTERVAL = -1
    REPLAY_START_SIZE = 100
    IMAGE_RESIZE = 'crop'


if __name__ == "__main__":
    launcher.launch(sys.argv[1:], Defaults, __doc__, traffic_situation='simpleX', agent_type='1D')
