#! /usr/bin/env python
"""This script launches all of the processes necessary to train a
deep Q-network on a SUMO simulation.

"""
import subprocess
import multiprocessing
import os
import argparse
import logging

from rlglue.agent import AgentLoader
from rlglue.environment import EnvironmentLoader as EnvironmentLoader


def launch_rlglue_agent(parameters, agent_type='neural'):
    """Start the rlglue agent.

    (This function is executed in a separate process using
    multiprocessing.)
    """

    if agent_type == 'neural':
        import rl_glue_sumo_agent
        agent = rl_glue_sumo_agent.NeuralAgent(parameters.discount,
                                              parameters.learning_rate,
                                              parameters.rms_decay,
                                              parameters.rms_epsilon,
                                              parameters.momentum,
                                              parameters.epsilon_start,
                                              parameters.epsilon_min,
                                              parameters.epsilon_decay,
                                              parameters.phi_length,
                                              parameters.replay_memory_size,
                                              parameters.experiment_prefix,
                                              parameters.nn_file,
                                              parameters.pause,
                                              parameters.network_type,
                                              parameters.update_rule,
                                              parameters.batch_accumulator,
                                              parameters.freeze_interval,
                                              parameters.batch_size,
                                              parameters.replay_start_size,
                                              parameters.update_frequency,
                                              parameters.image_resize)
    elif agent_type == '1D':
        import rl_glue_sumo_agent_1D
        agent = rl_glue_sumo_agent_1D.NeuralAgent(parameters.discount,
                                              parameters.learning_rate,
                                              parameters.rms_decay,
                                              parameters.rms_epsilon,
                                              parameters.momentum,
                                              parameters.epsilon_start,
                                              parameters.epsilon_min,
                                              parameters.epsilon_decay,
                                              parameters.phi_length,
                                              parameters.replay_memory_size,
                                              parameters.experiment_prefix,
                                              parameters.nn_file,
                                              parameters.pause,
                                              parameters.network_type,
                                              parameters.update_rule,
                                              parameters.batch_accumulator,
                                              parameters.freeze_interval,
                                              parameters.batch_size,
                                              parameters.replay_start_size,
                                              parameters.update_frequency,
                                              parameters.image_resize)
    elif agent_type == 'fixed':
        import rl_glue_sumo_agent_fixed_timing
        agent = rl_glue_sumo_agent_fixed_timing.FixedTimeAgent(parameters.experiment_prefix, 20)
        
    AgentLoader.loadAgent(agent)

def launch_experiment(parameters):
    """Start the rlglue experiment.

    (This function is executed in a separate process using
    multiprocessing.)
    """
    import rl_glue_sumo_experiment
    experiment = rl_glue_sumo_experiment.SumoExperiment(
        parameters.epochs,
        parameters.steps_per_epoch,
        parameters.steps_per_test)
    experiment.run()

def launch_environment(parameters):
    """Start the sumo-rlglue environment

    (This function is executed in a separate process using
    multiprocessing.)
    """
    import rl_glue_sumo_environment
    environment = rl_glue_sumo_environment.SumoEnvironment()
    EnvironmentLoader.loadEnvironment(environment)

def process_args(args, defaults, description):
    """
    Handle the command line.

    args     - list of command line arguments (not including executable name)
    defaults - a name space with variables corresponding to each of
               the required default command line values.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-r', '--rom', dest="rom", default=defaults.ROM,
                        help='ROM to run (default: %(default)s)')
    parser.add_argument('-e', '--epochs', dest="epochs", type=int,
                        default=defaults.EPOCHS,
                        help='Number of training epochs (default: %(default)s)')
    parser.add_argument('-s', '--steps-per-epoch', dest="steps_per_epoch",
                        type=int, default=defaults.STEPS_PER_EPOCH,
                        help='Number of steps per epoch (default: %(default)s)')
    parser.add_argument('-t', '--test-length', dest="steps_per_test",
                        type=int, default=defaults.STEPS_PER_TEST,
                        help='Number of steps per test (default: %(default)s)')
    parser.add_argument('--merge', dest="merge_frames", default=False,
                        action="store_true",
                        help='Tell ALE to send the averaged frames')
    parser.add_argument('--display-screen', dest="display_screen",
                        action='store_true', default=False,
                        help='Show the game screen.')
    parser.add_argument('--experiment-prefix', dest="experiment_prefix",
                        default=None,
                        help='Experiment name prefix '
                        '(default is the name of the game)')
    parser.add_argument('--frame-skip', dest="frame_skip",
                        default=defaults.FRAME_SKIP, type=int,
                        help='Every how many frames to process '
                        '(default: %(default)s)')
    parser.add_argument('--glue-port', dest="glue_port", type=int,
                        default=defaults.RLGLUE_PORT,
                        help='rlglue port (default: %(default)s)')

    parser.add_argument('--update-rule', dest="update_rule",
                        type=str, default=defaults.UPDATE_RULE,
                        help=('deepmind_rmsprop|rmsprop|sgd ' +
                              '(default: %(default)s)'))
    parser.add_argument('--batch-accumulator', dest="batch_accumulator",
                        type=str, default=defaults.BATCH_ACCUMULATOR,
                        help=('sum|mean (default: %(default)s)'))
    parser.add_argument('--learning-rate', dest="learning_rate",
                        type=float, default=defaults.LEARNING_RATE,
                        help='Learning rate (default: %(default)s)')
    parser.add_argument('--rms-decay', dest="rms_decay",
                        type=float, default=defaults.RMS_DECAY,
                        help='Decay rate for rms_prop (default: %(default)s)')
    parser.add_argument('--rms-epsilon', dest="rms_epsilon",
                        type=float, default=defaults.RMS_EPSILON,
                        help='Denominator epsilson for rms_prop ' +
                        '(default: %(default)s)')
    parser.add_argument('--momentum', type=float, default=defaults.MOMENTUM,
                        help=('Momentum term for Nesterov momentum. '+
                              '(default: %(default)s)'))
    parser.add_argument('--discount', type=float, default=defaults.DISCOUNT,
                        help='Discount rate')
    parser.add_argument('--epsilon-start', dest="epsilon_start",
                        type=float, default=defaults.EPSILON_START,
                        help=('Starting value for epsilon. ' +
                              '(default: %(default)s)'))
    parser.add_argument('--epsilon-min', dest="epsilon_min",
                        type=float, default=defaults.EPSILON_MIN,
                        help='Minimum epsilon. (default: %(default)s)')
    parser.add_argument('--epsilon-decay', dest="epsilon_decay",
                        type=float, default=defaults.EPSILON_DECAY,
                        help=('Number of steps to minimum epsilon. ' +
                              '(default: %(default)s)'))
    parser.add_argument('--phi-length', dest="phi_length",
                        type=int, default=defaults.PHI_LENGTH,
                        help=('Number of recent frames used to represent ' +
                              'state. (default: %(default)s)'))
    parser.add_argument('--max-history', dest="replay_memory_size",
                        type=int, default=defaults.REPLAY_MEMORY_SIZE,
                        help=('Maximum number of steps stored in replay ' +
                              'memory. (default: %(default)s)'))
    parser.add_argument('--batch-size', dest="batch_size",
                        type=int, default=defaults.BATCH_SIZE,
                        help='Batch size. (default: %(default)s)')
    parser.add_argument('--network-type', dest="network_type",
                        type=str, default=defaults.NETWORK_TYPE,
                        help=('nips_cuda|nips_dnn|nature_cuda|nature_dnn' +
                              '|linear (default: %(default)s)'))
    parser.add_argument('--freeze-interval', dest="freeze_interval",
                        type=int, default=defaults.FREEZE_INTERVAL,
                        help=('Interval between target freezes. ' +
                              '(default: %(default)s)'))
    parser.add_argument('--update-frequency', dest="update_frequency",
                        type=int, default=defaults.UPDATE_FREQUENCY,
                        help=('Number of actions before each SGD update. '+
                              '(default: %(default)s)'))
    parser.add_argument('--replay-start-size', dest="replay_start_size",
                        type=int, default=defaults.REPLAY_START_SIZE,
                        help=('Number of random steps before training. ' +
                              '(default: %(default)s)'))
    parser.add_argument('--image-resize', dest="image_resize",
                        type=str, default=defaults.IMAGE_RESIZE,
                        help=('crop|scale (default: %(default)s)'))
    parser.add_argument('--nn-file', dest="nn_file", type=str, default=None,
                        help='Pickle file containing trained net.')
    parser.add_argument('--pause', type=float, default=0,
                        help='Amount of time to pause display while testing.')


    parameters = parser.parse_args(args)
    if parameters.experiment_prefix is None:
        name = os.path.splitext(os.path.basename(parameters.rom))[0]
        parameters.experiment_prefix = name

    return parameters


def launch(args, defaults, description, traffic_situation, agent_type='neural'):
    """
    Start all of the processes necessary for a single training run.
    """

    logging.basicConfig(level=logging.INFO)
    parameters = process_args(args, defaults, description)

    os.environ["RLGLUE_PORT"] = str(parameters.glue_port)

    close_fds = True

    # Start RLGLue--------------
    rl_glue_process = subprocess.Popen(['rl_glue'], env=os.environ,
                                       close_fds=close_fds)

    # Start SUMO-----------------
    if agent_type == "1D":
        command = ['python', 'rl_glue_sumo_environment_1D.py', traffic_situation]
    else:
        command = ['python', 'rl_glue_sumo_environment.py', traffic_situation]
    sumo_process = subprocess.Popen(command, env=os.environ, close_fds=close_fds)
    # sumo_process = multiprocessing.Process(target=launch_environment, args=(parameters,))

    # Start SUMO Experiment---------------
    experminent_process = multiprocessing.Process(target=launch_experiment,
                                                  args=(parameters,))
    experminent_process.start()

    # Start SUMO Agent--------------
    agent_process = multiprocessing.Process(target=launch_rlglue_agent,
                                            args=(parameters, agent_type,))
    agent_process.start()

    rl_glue_process.wait()
    sumo_process.wait()
    experminent_process.join()
    agent_process.join()


if __name__ == '__main__':
    pass
