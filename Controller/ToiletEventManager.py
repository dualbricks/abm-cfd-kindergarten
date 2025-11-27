import queue
import random

import Controller.Constants as Constants
from Controller.Agent import BaseAgent
from Controller.DailyConstants import CLASSROOM_5, CLASSROOM_6


class ToiletEventManager:
    def __init__(self):
        self.sinks = dict.fromkeys(Constants.SINK, None)
        self.cubicles = dict.fromkeys(Constants.CUBICLES, None)
        self.assigned_sinks = {}
        self.assigned_cubicles = {}
        self.assigned_queue = queue.Queue(maxsize=len(Constants.DENSITY_AREA_DICT[Constants.TOILET_ENTRANCE]))
        self.toilet_queue = Constants.DENSITY_AREA_DICT[Constants.TOILET_ENTRANCE].copy()
        self.sink_waiting_area_density = []

    def is_cubicle_free(self):
        """
        Check if there is any empty cubicle
        :return:
        """
        return len(self.assigned_cubicles) < len(self.cubicles)

    def is_sink_free(self):
        """
        Check if there is any empty sink
        :return:
        """
        return len(self.assigned_sinks) < len(self.sinks)

    def is_queue_free(self):
        """
        Check if there is available queue
        :return:
        """
        return self.assigned_queue.qsize() < len(self.toilet_queue)

    def free_up_cubicle(self, ped_id):
        """
        Free up the cubicle when the agent is done with their business.
        :param ped_id:
        :return:
        """
        assigned_cubicle = self.assigned_cubicles[ped_id]
        self.assigned_cubicles.pop(ped_id)
        self.cubicles[assigned_cubicle] = None

    def free_up_sink(self, ped_id):
        """
        Free up the sink when the agent is done washing their hands and stuff
        :return:
        """
        assigned_sink = self.assigned_sinks[ped_id]
        self.assigned_sinks.pop(ped_id)
        self.sinks[assigned_sink] = None

    def free_up_queue(self):
        """
        Free up the queue when the agent is done waiting.
        :param ped_id:
        :return:
        """
        self.assigned_queue.get()

    def assign_queue(self, ped_id):
        """
        Assign a queue when there is free slots in the queue
        :param ped_id:
        :return:
        """
        if ped_id in self.assigned_queue.queue:
            return self.toilet_queue[list(self.assigned_queue.queue).index(ped_id)]

        self.assigned_queue.put(ped_id)
        return self.toilet_queue[list(self.assigned_queue.queue).index(ped_id)]

    def assign_cubicle(self, ped_id):
        """
        Assign a cubicle to an agent next in line to the toilet
        :param ped_id:
        :return:
        """

        if ped_id in self.assigned_cubicles.keys():
            return self.assigned_cubicles[ped_id]

        available_cubicles = [key for key, value in self.cubicles.items() if value is None]
        random_cubicle = random.choice(available_cubicles)
        self.assigned_cubicles[ped_id] = random_cubicle
        self.cubicles[random_cubicle] = True
        return random_cubicle

    def assign_sink(self, ped_id):
        """
        Assign a sink to an agent after finishing business
        :param ped_id:
        :return:
        """

        if ped_id in self.assigned_sinks.keys():
            return self.assigned_sinks[ped_id]

        available_sinks = [key for key, value in self.sinks.items() if value is None]
        random_sink = random.choice(available_sinks)
        self.assigned_sinks[ped_id] = random_sink
        self.sinks[random_sink] = True
        return random_sink

    def toilet_event_handling(self, agent: BaseAgent, sim_time):
        """
        Refer to toilet event diagram for the full event flow.
        :param agent:
        :param ped_id:
        :param sim_time:
        :return:
        """

        # start queue if not in queue
        if agent.toilet_state == Constants.ToiletState.WANT_TO_GO_TOILET or agent.toilet_state == Constants.ToiletState.WAITING_FOR_QUEUE:
            if self.is_queue_free() and len(self.sink_waiting_area_density) < 4:
                queue_number = self.assign_queue(agent.ped_id)
                agent.add_target((queue_number, 20), 0)
                agent.change_toilet_state(Constants.ToiletState.IN_QUEUE)
                agent.set_next_target(sim_time)
                agent.set_intermediate_target(agent.current_target)
            else:
                if random.random() <= 0.4 and agent.toilet_state == Constants.ToiletState.WANT_TO_GO_TOILET:
                    agent.set_next_target(sim_time)
                    agent.change_toilet_state(Constants.ToiletState.WAITING_FOR_QUEUE)
                    agent.add_target((agent.current_target, 20), 1)
        # if agent is in queue already
        if agent.toilet_state == Constants.ToiletState.IN_QUEUE:
            # if there is any free cubicle and is at the top of the queue
            # to validate if this function is thread safe
            if self.is_cubicle_free() and self.assigned_queue.queue[0] == agent.ped_id:
                self.free_up_queue()
                cubicle_number = self.assign_cubicle(agent.ped_id)
                agent.add_target((cubicle_number, 10), 0)
                agent.change_toilet_state(Constants.ToiletState.IN_CUBICLE)
                agent.set_next_target(sim_time)
                agent.old_target = agent.current_target
            else:
                # update queue number after others leave queue
                queue_number = self.assign_queue(agent.ped_id)
                agent.add_target((queue_number, 20), 0)
                agent.set_next_target(sim_time)
                agent.old_target = agent.current_target
        # if agent is done with using the toilet
        if (agent.toilet_state == Constants.ToiletState.IN_CUBICLE and agent.is_fulfilled(
                sim_time)) or agent.toilet_state == Constants.ToiletState.WAITING_FOR_SINK:
            if agent.toilet_state != Constants.ToiletState.WAITING_FOR_SINK:
                self.free_up_cubicle(agent.ped_id)
            if self.is_sink_free():
                sink_number = self.assign_sink(agent.ped_id)
                agent.add_target((sink_number, 10), 0)
                if agent.ped_id in self.sink_waiting_area_density:
                    self.sink_waiting_area_density.remove(agent.ped_id)
                agent.change_toilet_state(Constants.ToiletState.IN_SINK)
                agent.set_next_target(sim_time)
            else:
                agent.add_target((Constants.SINK_WAITING_AREA, 10), 0)
                agent.change_toilet_state(Constants.ToiletState.WAITING_FOR_SINK)
                if agent.ped_id not in self.sink_waiting_area_density:
                    self.sink_waiting_area_density.append(agent.ped_id)
                agent.set_next_target(sim_time)
        # handling after sink
        if agent.toilet_state == Constants.ToiletState.IN_SINK and agent.is_fulfilled(sim_time):
            self.free_up_sink(agent.ped_id)

            if agent.class_id in [CLASSROOM_5, CLASSROOM_6]:
                agent.change_toilet_state(Constants.ToiletState.JUST_ENDED)
            else:
                agent.change_toilet_state(Constants.ToiletState.NOT_USING)
            agent.set_next_target(sim_time)
            agent.set_intermediate_target(agent.current_target, reverse=True)
