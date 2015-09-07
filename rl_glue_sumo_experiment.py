"""
This is an RLGlue experiment to collect data from the SUMO simulator

(Based on the sample_experiment.py from the Rl-glue python codec examples.)


Author: Tobias Rijken

"""
import rlglue.RLGlue as RLGlue
import logging

class SumoExperiment(object):
    def __init__(self, num_epochs, epoch_length, test_length):
        self.num_epochs = num_epochs
        self.epoch_length = epoch_length
        self.test_length = test_length
        self.steps_taken = 0

    def run(self):
        """
        Run the desired number of training epochs, a testing epoch
        is conducted after each training epoch.
        """
        RLGlue.RL_init()

        for epoch in range(1, self.num_epochs + 1):
            self.run_epoch(epoch, self.epoch_length, "training")
            RLGlue.RL_agent_message("finish_epoch " + str(epoch))
            RLGlue.RL_env_message("finish_epoch " + str(epoch))

            if self.test_length > 0:
                RLGlue.RL_agent_message("start_testing")
                RLGlue.RL_env_message("start_testing")
                self.run_epoch(epoch, self.test_length, "testing")
                RLGlue.RL_agent_message("finish_testing " + str(epoch))
                RLGlue.RL_env_message("finish_testing " + str(epoch))
        
    def run_epoch(self, epoch, num_steps, prefix):
        """ Run one 'epoch' of training or testing, where an epoch is defined
        by the number of steps executed.  Prints a progress report after
        every trial

        Arguments:
        num_steps - steps per epoch
        prefix - string to print ('training' or 'testing')

        """
        steps_left = num_steps
        while steps_left > 0:
            logging.info(prefix + " epoch: " + str(epoch) + " steps_left: " +
                         str(steps_left))

            terminal = RLGlue.RL_episode(steps_left)
            if not terminal:
                RLGlue.RL_agent_message("episode_end")
                RLGlue.RL_env_message("episode_end")
            steps_left -= RLGlue.RL_num_steps()

    # def run(self):
    #     RLGlue.RL_init()

    #     for epoch in range(1, self.num_epochs + 1):
    #         self.run_epoch(episode=epoch, prefix="training")
    #         RLGlue.RL_agent_message("finish_epoch " + str(epoch))
    #         RLGlue.RL_env_message("finish_epoch " + str(epoch))

    #         if self.test_length > 0:
    #             RLGlue.RL_agent_message("start_testing")
    #             RLGlue.RL_env_message("start_testing")
    #             self.run_epoch(episode=epoch, prefix="testing")
    #             RLGlue.RL_agent_message("finish_testing " + str(epoch))
    #             RLGlue.RL_env_message("finish_testing " + str(epoch))

    #     RLGlue.RL_cleanup()

    # def run_epoch(self, episode, prefix):
    #     logging.info(prefix + " epoch: " + str(episode) + " steps_taken: " + str(self.steps_taken))
    #     terminal = RLGlue.RL_episode(0)
    #     if not terminal:
    #         RLGlue.RL_agent_message("episode_end")
    #         RLGlue.RL_env_message("episode_end")
    #     self.steps_taken += RLGlue.RL_num_steps()



def main():
    experiment = SumoExperiment(
        num_epochs=100,
        epoch_length=50000,
        test_length=10000)
    experiment.run()

if __name__ == '__main__':
    main()

