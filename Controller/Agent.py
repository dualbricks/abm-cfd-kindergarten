from __future__ import annotations

import abc
import random
from typing import TYPE_CHECKING
from queue import PriorityQueue

import numpy as np

from Controller import Constants, DailyConstants

from Controller.Constants import ToiletState
from Controller.DailyConstants import StaffStatus, StudentStatus, ActivityType, AREA_DICT, BREAK_ROOM, KITCHENETTE, \
    EventState, STAFF_NAP_TIME_STATUS, PrincipalStatus, PRINCIPAL_TABLE, EXIT, \
    INTERMEDIATE_TOILET_TARGET, CLASSROOM_5, CLASSROOM_6, INTERMEDIATE_TOILET_TARGET_POS, \
    INTERMEDIATE_TOILET_TARGET_2_POS, INTERMEDIATE_TOILET_TARGET_2, CLASSROOM_3, STAFF_HANGOUT_SPOT_BREAK_ROOM, \
    STAFF_HANGOUT_SPOT_KITCHENETTE, StaffType
from Controller.SeatManager import TableSeatManager, PrincipalRoomManager
from Controller.Singleton import Singleton
from Controller.func import euclidean_distance

if TYPE_CHECKING:
    from Controller.ClassManager import Class, ClassManager


class TargetPriorityQueue(PriorityQueue):
    def __init__(self):
        PriorityQueue.__init__(self)
        self.counter = 0

    def put(self, item, priority):
        PriorityQueue.put(self, (priority, self.counter, item))
        self.counter += 1

    def get(self, *args, **kwargs):
        _, _, item = PriorityQueue.get(self, *args, **kwargs)
        return item


class Agent(object):
    """
    Represents an agent with its current state in the simulation
    """

    def __init__(self, ped_id, chair, targets):
        self.ped_id = ped_id
        self.interest_stack = PriorityQueue()
        self.current_target = chair
        self.chair = chair
        self.targets = targets
        self.toilet_state = Constants.ToiletState.NOT_USING
        # put the targets in the interest stack
        for target in targets:
            if target == Constants.TABLE:
                self.interest_stack.put((1, chair))
            elif target != Constants.TOILET_ENTRANCE:
                self.interest_stack.put((1, target))
            else:
                self.change_toilet_state(Constants.ToiletState.WANT_TO_GO_TOILET)

        self.target_end_time = None
        self.end_status = False
        self.sub_group_end_time = 0.0

    def set_next_target(self, sim_time):
        """
        set top stack destination as walking target
        :return:
        """

        # Empty interest stack when ending
        if sim_time >= Constants.ENDING_TIME and not self.end_status:
            self.target_end_time = sim_time + max(0, np.random.normal(30, 20))
            self.end_status = True
            while not self.interest_stack.empty():
                self.interest_stack.get()
            return
        if not self.interest_stack.empty():
            self.current_target = self.interest_stack.get()[1]
            if self.current_target in Constants.DENSITY_AREA_DICT[Constants.SUBGROUP_R]:
                self.target_end_time = sim_time + max(0, np.random.normal(740, 10))
            elif self.current_target in Constants.DENSITY_AREA_DICT[Constants.SUBGROUP_T]:
                self.target_end_time = sim_time + max(0, np.random.normal(250, 10))
            elif self.current_target in Constants.DENSITY_AREA_DICT[Constants.SUBGROUP_B]:
                self.target_end_time = sim_time + max(0, np.random.normal(150, 10))
            elif self.current_target in Constants.DENSITY_AREA_DICT[Constants.SUBGROUP_RR]:
                self.target_end_time = sim_time + max(0, np.random.normal(740, 10))
            else:
                self.target_end_time = sim_time + max(0, np.random.normal(60, 10))
        else:
            self.current_target = self.chair

    def is_fulfilled(self, sim_time):
        """
        Check if the agent has already fulfilled the interest.
        :param sim_time:
        :return: True if it is fulfilled and set reset targets
        """
        if self.target_end_time is None:
            return True

        return self.target_end_time is not None and sim_time >= self.target_end_time

    def add_target(self, target, priority):
        self.interest_stack.put((priority, target))

    def change_toilet_state(self, state):
        self.toilet_state = state

    def set_return_to_table(self):
        self.current_target = self.chair

    def set_specific_target(self, specific, time_change=None):
        self.current_target = specific
        if time_change:
            self.target_end_time = time_change


class BaseAgent(object):
    """
    Base Class for childcare daily activities scenario
    """

    def __init__(self, ped_id, targets, bladder_cap, class_id):
        self.ped_id = ped_id
        self.targets = targets
        self.interest_stack = TargetPriorityQueue()
        self.toilet_state = Constants.ToiletState.NOT_USING
        self.current_target = random.choice([x for x in AREA_DICT[class_id] if x != -1])
        self.bladder_cap = bladder_cap
        self.class_id = class_id
        self.fidget_time = 0.0
        self.status = None
        self.target_end_time = 0.0
        self.next_toilet_time = np.random.normal(self.bladder_cap, 45)
        self.free_time_activity_end_time = 0
        self.set_to_end = False
        self.toilet_change_target_time = 0
        self.old_target = None
        self.current_pos = (0, 0)
        self.reach_intermediate = False
        self.intermediate_targets = []

    def set_next_target(self, sim_time):
        """
        Deprecated since we are controlling using the Class schedule we only need to update the state of the agent.
        This is only used to support toilet manager logic since I have no time to update it
        :return:
        """
        if not self.interest_stack.empty():
            target = self.interest_stack.get()
            self.current_target = target[0]
            self.target_end_time = sim_time + max(0, np.random.normal(target[1], 2))

        if self.toilet_state == ToiletState.NOT_USING or self.toilet_state == ToiletState.JUST_ENDED:
            self.current_target = random.choice([x for x in AREA_DICT[self.class_id] if x != -1])

    def set_intermediate_target(self, target, reverse=False, route_to="T"):
        if route_to == "T":
            self.old_target = target
            if self.class_id == CLASSROOM_5:
                self.intermediate_targets = [(INTERMEDIATE_TOILET_TARGET_2, INTERMEDIATE_TOILET_TARGET_2_POS),
                                             (INTERMEDIATE_TOILET_TARGET, INTERMEDIATE_TOILET_TARGET_POS)]
                self.reach_intermediate = False
                if reverse:
                    self.intermediate_targets.reverse()
            elif self.class_id == CLASSROOM_6:
                self.intermediate_targets = [(INTERMEDIATE_TOILET_TARGET, INTERMEDIATE_TOILET_TARGET_POS)]
                self.reach_intermediate = False
            else:
                self.intermediate_targets = []
                self.reach_intermediate = True
        elif route_to == "K":
            self.old_target = target
            if self.class_id == CLASSROOM_3:
                self.intermediate_targets = [(INTERMEDIATE_TOILET_TARGET, INTERMEDIATE_TOILET_TARGET_POS),
                                             (INTERMEDIATE_TOILET_TARGET_2, INTERMEDIATE_TOILET_TARGET_2_POS)]
                self.reach_intermediate = False
                if reverse:
                    self.intermediate_targets.reverse()
            else:
                self.intermediate_targets = []
                self.reach_intermediate = True

    def is_fulfilled(self, sim_time):
        """
        Deprecated since we are controlling using the Class schedule we only need to update the state of the agent.
        This is only used to support toilet manager logic since I have no time to update it
        :param sim_time:
        :return:
        """
        return self.target_end_time is not None and sim_time >= self.target_end_time

    def add_target(self, target, priority):
        """
        Deprecated since we are controlling using the Class schedule we only need to update the state of the agent.
        This is only used to support toilet manager logic since I have no time to update it
        :param target:
        :param priority:
        :return:
        """
        self.interest_stack.put(target, priority)

    def change_toilet_state(self, state):
        self.toilet_state = state

    def set_specific_target(self, specific, time_change=None):
        self.current_target = specific
        if time_change:
            self.target_end_time = time_change

    def initialise_targets_based_on_schedule(self):
        for i, target in enumerate(self.targets):
            self.add_target(target, i)

    def intermediate_movement_handler(self):
        if len(self.intermediate_targets) > 0:
            current_target = self.intermediate_targets[0]
            if euclidean_distance(self.current_pos,
                                  current_target[1]) <= 1.0 and not self.reach_intermediate:
                self.current_target = self.old_target
                self.intermediate_targets.pop(0)
                if not self.intermediate_targets:
                    if self.toilet_state == ToiletState.JUST_ENDED:
                        self.toilet_state = ToiletState.NOT_USING
                    self.reach_intermediate = True
                else:
                    self.current_target = self.intermediate_targets[0][0]
            elif not self.reach_intermediate:
                self.current_target = current_target[0]

    def update_agent_movement(self, c: Class, sim_time: float):
        if self.need_go_toilet(
                sim_time) and self.toilet_state == ToiletState.NOT_USING:
            self.toilet_state = ToiletState.WANT_TO_GO_TOILET
            self.update_bladder_full_timing(sim_time)

        # if already going toilet no need to update anything
        if self.toilet_state != ToiletState.NOT_USING:
            if c.class_id in [CLASSROOM_5, CLASSROOM_6]:
                if self.toilet_state == ToiletState.IN_QUEUE or self.toilet_state == ToiletState.JUST_ENDED or self.toilet_state == ToiletState.IN_CUBICLE:
                    self.intermediate_movement_handler()
            return

        if c.event_state == EventState.PREPARING:
            self.prepare_event(c, sim_time)
        elif c.event_state == EventState.IN_PROGRESS:
            self.do_event(c, sim_time)
        elif c.event_state == EventState.CLEAN_UP:
            self.clean_up(c, sim_time)
        elif c.event_state == EventState.ALL_FINISHED:
            self.end(c, sim_time)

    def update_bladder_full_timing(self, sim_time: float):
        self.next_toilet_time = sim_time + np.random.normal(self.bladder_cap, 45)

    def need_go_toilet(self, sim_time: float):
        return self.next_toilet_time <= sim_time

    def common_behaviour(self, area, status_condition, new_status, sim_time: float, random_movement=False,
                         fidget_time=35, nearby=False, c: Class = None):
        if self.status != status_condition:
            self.current_target = random.choice(area)
            self.status = new_status
            self.fidget_time = sim_time + np.random.normal(fidget_time, 2)
        elif random_movement and self.toilet_state == ToiletState.NOT_USING:
            if random.random() < 0.2 and sim_time >= self.fidget_time:
                if nearby and self.current_target in AREA_DICT[self.class_id]:
                    self.current_target = random.choice(c.find_nearby_grid_by_id(self.current_target))
                else:
                    self.current_target = random.choice(area)
                self.fidget_time = sim_time + np.random.normal(fidget_time, 2)

    def prepare_event(self, c: Class, sim_time: float):
        if c.current_event[0] == ActivityType.LESSON:
            self.prepare_for_lesson(c, sim_time)

        elif c.current_event[0] == ActivityType.MEAL:
            self.prepare_for_meal(c, sim_time)

        elif c.current_event[0] == ActivityType.NAP:
            self.prepare_for_nap(c, sim_time)

        elif c.current_event[0] == ActivityType.FREE_CHOICE_ACTIVITY:
            self.prepare_free_choice(c, sim_time)

    def do_event(self, c: Class, sim_time: float):
        if c.current_event[0] == ActivityType.LESSON:
            self.do_lesson(c, sim_time)

        elif c.current_event[0] == ActivityType.MEAL:
            self.do_meal(c, sim_time)

        elif c.current_event[0] == ActivityType.NAP:
            self.do_nap(c, sim_time)

        elif c.current_event[0] == ActivityType.FREE_CHOICE_ACTIVITY:
            self.prepare_free_choice(c, sim_time)

    def clean_up(self, c: Class, sim_time: float):
        if c.current_event[0] == ActivityType.LESSON:
            self.clean_up_for_lesson(c, sim_time)

        elif c.current_event[0] == ActivityType.MEAL:
            self.clean_up_for_meal(c, sim_time)

        elif c.current_event[0] == ActivityType.NAP:
            self.clean_up_for_nap(c, sim_time)

        elif c.current_event[0] == ActivityType.FREE_CHOICE_ACTIVITY:
            self.prepare_free_choice(c, sim_time)

    def update_position(self, pos):
        self.current_pos = pos

    @abc.abstractmethod
    def prepare_for_lesson(self, c: Class, sim_time: float):
        """
        For staff, they will get the materials required for the lesson from the break room

        For students, they will start to gather around the teacher and get ready for lesson
        :param c: Class
        :param sim_time: float
        :return:
        """
        pass

    @abc.abstractmethod
    def do_lesson(self, c: Class, sim_time: float):
        """
        For staff, the teacher will be teaching the students, the support staff will walk around the class to monitor the students

        For Students, they will be gathering around the teacher listening to the lessons and occasionally fidget around but still remain close to the teacher

        :param c: Class
        :param sim_time: float
        :return:
        """
        pass

    @abc.abstractmethod
    def clean_up_for_lesson(self, c: Class, sim_time: float):
        """
        For staff, some might put materials back to the break room

        For Students, they will just play around the classroom at the meantime
        :param c: Class
        :param sim_time: float
        :return:
        """
        pass

    @abc.abstractmethod
    def prepare_for_meal(self, c: Class, sim_time: float):
        """
        For Staff, they will go the kitchen to prepare the food.

        For Students, they will go toilet to wash their hands before meal time

        :param c: Class
        :param sim_time: float
        :return:
        """
        pass

    @abc.abstractmethod
    def do_meal(self, c: Class, sim_time: float):
        """
        For staffs, they will be monitoring the students while they eat.

        For Students, they will spread evenly across the classroom to eat.
        :param c: Class
        :param sim_time: float
        :return:
        """
        pass

    @abc.abstractmethod
    def clean_up_for_meal(self, c: Class, sim_time: float):
        """
        For Staffs, they will clean up the classroom and return stuff to the kitchenette area

        For Students, they will wash their hands once again.
        :param c: Class
        :param sim_time: float
        :return:
        """
        pass

    @abc.abstractmethod
    def prepare_for_nap(self, c: Class, sim_time: float):
        """
        For Staffs, during this time they will get stuff from the break room

        For students, wait at classroom for beds
        :param c:
        :param sim_time:
        :return:
        """
        pass

    @abc.abstractmethod
    def do_nap(self, c: Class, sim_time: float):
        """
        For Staffs, they will do their own stuff that can be visiting the principal or preparing for the next activity

        For Students, they will nap
        :param principal_room:
        :param principal:
        :param c:
        :param sim_time:
        :return:
        """
        pass

    @abc.abstractmethod
    def clean_up_for_nap(self, c: Class, sim_time: float):
        """
        For staffs, they will clean up stuff from the classroom
        For students, they will just wake up.
        :param c:
        :param sim_time:
        :return:
        """
        pass

    @abc.abstractmethod
    def prepare_free_choice(self, c: Class, sim_time: float):
        """

        :param c:
        :param sim_time:
        :return:
        """

    @abc.abstractmethod
    def do_free_choice(self, c: Class, sim_time: float):
        """

        :param c:
        :param sim_time:
        :return:
        """

    @abc.abstractmethod
    def clean_up_free_choice(self, c: Class, sim_time: float):
        """

        :param c:
        :param sim_time:
        :return:
        """

    @abc.abstractmethod
    def end(self, c: Class, sim_time: float):
        """
        For students, they leave the place
        For staff, set to free.
        :param c:
        :param sim_time:
        :return:
        """


class StaffAgent(BaseAgent):
    """
    Agent Class for Staff Agent

    https://pmc.ncbi.nlm.nih.gov/articles/PMC3206217/
    """

    def __init__(self, ped_id, class_id, targets, staff_type=StaffType.CLASS, bladder_cap=14400):
        super().__init__(ped_id, targets, bladder_cap, class_id)
        self.status = StaffStatus.FREE
        self.chill_spot = None
        self.staff_type = staff_type

    def is_free(self):
        return self.status == StaffStatus.FREE

    def prepare_for_lesson(self, c: Class, sim_time: float):
        self.common_behaviour(DailyConstants.AREA_DICT[BREAK_ROOM], StaffStatus.PREPARING, StaffStatus.PREPARING,
                              sim_time)

    def do_lesson(self, c: Class, sim_time: float):
        if self.status != StaffStatus.TEACHING:
            if self == c.leader:
                self.current_target = DailyConstants.LEADER_POSITION[self.class_id]
            else:
                self.current_target = random.choice([x for x in AREA_DICT[self.class_id] if x != -1])
                self.fidget_time = sim_time + np.random.normal(30, 5)
            self.status = StaffStatus.TEACHING

        elif self.toilet_state == ToiletState.NOT_USING:
            if sim_time >= self.fidget_time and random.random() < 0.2 and self != c.leader:
                if self.current_target in AREA_DICT[self.class_id]:
                    self.current_target = random.choice(c.find_nearby_grid_by_id(self.current_target))
                else:
                    self.current_target = random.choice([x for x in AREA_DICT[self.class_id] if x != -1])
            self.fidget_time = sim_time + np.random.normal(60, 5)

    def clean_up_for_lesson(self, c: Class, sim_time: float):
        if self.status != StaffStatus.CLEANING_UP and self != c.leader:
            self.current_target = random.choice(DailyConstants.AREA_DICT[BREAK_ROOM])
            self.status = StaffStatus.CLEANING_UP

    def prepare_for_meal(self, c: Class, sim_time: float):
        """
        :param c:
        :param sim_time:
        :return:
        """

        # need to find a way to do the reverse when going back
        if self.class_id == CLASSROOM_3:
            if self.status != StaffStatus.PREPARING:
                target = random.choice(DailyConstants.AREA_DICT[KITCHENETTE])
                self.status = StaffStatus.PREPARING
                self.set_intermediate_target(target, route_to="K")
                self.intermediate_movement_handler()
            else:
                self.intermediate_movement_handler()
        else:
            self.common_behaviour(DailyConstants.AREA_DICT[KITCHENETTE], StaffStatus.PREPARING, StaffStatus.PREPARING,
                                  sim_time)

    def do_meal(self, c: Class, sim_time: float):
        self.common_behaviour(c.find_nearby_grid_by_id(DailyConstants.LEADER_POSITION[self.class_id]),
                              StaffStatus.TEACHING, StaffStatus.TEACHING,
                              sim_time, nearby=True, c=c, random_movement=True)

    def clean_up_for_meal(self, c: Class, sim_time: float):
        if self.class_id == CLASSROOM_3:
            if self.status != StaffStatus.CLEANING_UP:
                target = random.choice(DailyConstants.AREA_DICT[KITCHENETTE])
                self.set_intermediate_target(target, route_to="K")
                self.intermediate_movement_handler()
                self.status = StaffStatus.CLEANING_UP
            else:
                self.intermediate_movement_handler()
        else:
            self.common_behaviour(DailyConstants.AREA_DICT[KITCHENETTE], StaffStatus.CLEANING_UP,
                                  StaffStatus.CLEANING_UP,
                                  sim_time)

    def prepare_for_nap(self, c: Class, sim_time: float):
        """
        Just looking out for the students
        :param c:
        :param sim_time:
        :return:
        """
        self.common_behaviour([x for x in AREA_DICT[self.class_id] if x != -1], StaffStatus.PREPARING,
                              StaffStatus.PREPARING, sim_time, nearby=True, c=c, random_movement=True)

    def do_nap(self, c: Class, sim_time: float):
        """
        The staff can do a few things here:
        1. Visit the principal
        2. Talk with colleagues
        3. Stay in break room
        4. Stay in Classroom to prepare for class
        :param c:
        :param sim_time:
        :return:
        """

        if self.status == StaffStatus.PREPARING:
            self.status = StaffStatus.FREE

        # Choose a random activity to do
        if self.status == StaffStatus.FREE:
            principal = Principal()
            if principal.in_office():
                activities_available = STAFF_NAP_TIME_STATUS
            else:
                activities_available = [x for x in STAFF_NAP_TIME_STATUS if x is not StaffStatus.TALKING]
            random_activity = random.choice(activities_available)
            if random_activity == StaffStatus.TALKING:
                principal_room = PrincipalRoomManager()
                # check if principal is free first if not go to the next loop first
                if principal.in_office() and principal_room.is_seat_available():
                    self.current_target = principal_room.assign_seat(self.ped_id)
                    self.status = StaffStatus.TALKING
                    self.free_time_activity_end_time = sim_time + np.random.normal(450, 60)
            elif random_activity == StaffStatus.CHILLING:
                self.status = StaffStatus.CHILLING
                self.chill_spot = random.choice([STAFF_HANGOUT_SPOT_BREAK_ROOM, STAFF_HANGOUT_SPOT_KITCHENETTE])
                self.common_behaviour(AREA_DICT[self.chill_spot], StaffStatus.CHILLING, StaffStatus.CHILLING, sim_time,
                                      c=c, random_movement=True)
                self.free_time_activity_end_time = sim_time + np.random.normal(900, 90)

            elif random_activity == StaffStatus.BREAK:
                self.status = StaffStatus.BREAK
                self.common_behaviour(AREA_DICT[BREAK_ROOM], StaffStatus.BREAK, StaffStatus.BREAK, sim_time)
                self.free_time_activity_end_time = sim_time + np.random.normal(900, 90)

            elif random_activity == StaffStatus.TEACHING and self.staff_type == StaffType.CLASS:
                self.status = StaffStatus.TEACHING
                self.common_behaviour([x for x in AREA_DICT[self.class_id] if x != -1], StaffStatus.FREE,
                                      StaffStatus.TEACHING, sim_time)
                self.free_time_activity_end_time = sim_time + np.random.normal(1800, 360)

        if self.status == StaffStatus.TALKING:
            principal = Principal()
            if not principal.in_office():
                principal_room = PrincipalRoomManager()
                principal_room.free_seat(self.ped_id)
                self.status = StaffStatus.FREE

        elif self.status == StaffStatus.CHILLING:
            self.common_behaviour(AREA_DICT[self.chill_spot], StaffStatus.CHILLING, StaffStatus.CHILLING, sim_time,
                                  c=c, random_movement=True)

        if sim_time >= self.free_time_activity_end_time:
            if self.status == StaffStatus.TALKING:
                principal_room = PrincipalRoomManager()
                principal_room.free_seat(self.ped_id)
            self.status = StaffStatus.FREE

    def clean_up_for_nap(self, c: Class, sim_time: float):
        """
        At this point all the staff should be back to the classroom
        :param c:
        :param sim_time:
        :return:
        """

        if self.status != StaffStatus.CLEANING_UP:
            if self.status == StaffStatus.TALKING:
                principal_room = PrincipalRoomManager()
                principal_room.free_seat(self.ped_id)
            self.status = StaffStatus.CLEANING_UP

    def end(self, c: Class, sim_time: float):
        if not self.set_to_end:
            self.status = StaffStatus.FREE
            self.set_to_end = True
        self.do_nap(c, sim_time)


class StudentAgent(BaseAgent):
    """
    Agent Class for Student Agent

    https://www.medicalnewstoday.com/articles/how-long-can-you-hold-in-your-pee#capacity
    """

    def __init__(self, ped_id, class_id, targets, bladder_cap=7200):
        super().__init__(ped_id, targets, bladder_cap, class_id)
        self.status = StudentStatus.FREE

    def prepare_for_lesson(self, c: Class, sim_time: float):
        self.common_behaviour(c.find_nearby_grid_by_id(DailyConstants.LEADER_POSITION[self.class_id]),
                              StudentStatus.PREPARING, StudentStatus.PREPARING, sim_time, c=c, random_movement=True,
                              nearby=True)

    def do_lesson(self, c: Class, sim_time: float):
        self.common_behaviour(c.find_nearby_grid_by_id(DailyConstants.LEADER_POSITION[self.class_id]),
                              StudentStatus.LEARNING, StudentStatus.LEARNING, sim_time, c=c, random_movement=True,
                              nearby=True)

    def clean_up_for_lesson(self, c: Class, sim_time: float):
        self.common_behaviour([x for x in AREA_DICT[self.class_id] if x != -1],
                              StudentStatus.CLEANING_UP, StudentStatus.CLEANING_UP, sim_time, c=c, random_movement=True,
                              nearby=True)

    def prepare_for_meal(self, c: Class, sim_time: float):
        # go toilet
        if self.status != StudentStatus.PREPARING:
            self.toilet_state = ToiletState.WANT_TO_GO_TOILET
            self.update_bladder_full_timing(sim_time)
            self.status = StudentStatus.PREPARING
        else:
            #     self.common_behaviour([x for x in AREA_DICT[self.class_id] if x != -1], StudentStatus.PREPARING,
            #                           StudentStatus.PREPARING, sim_time, True, c=c, nearby=True)
            self.current_target = c.nap_manager.assign_seat(self.ped_id)

    def do_meal(self, c: Class, sim_time: float):
        if self.status != StudentStatus.EATING:
            self.status = StudentStatus.EATING
            self.current_target = c.seat_manager.assign_seat(self.ped_id)

    def clean_up_for_meal(self, c: Class, sim_time: float):
        # need go toilet again to clean up
        if self.status != StudentStatus.CLEANING_UP:
            self.status = StudentStatus.CLEANING_UP
            self.toilet_state = ToiletState.WANT_TO_GO_TOILET
            self.update_bladder_full_timing(sim_time)
            c.seat_manager.free_seat(self.ped_id)
        else:
            self.common_behaviour([x for x in AREA_DICT[self.class_id] if x != -1], StudentStatus.CLEANING_UP,
                                  StudentStatus.CLEANING_UP, sim_time, True, c=c, nearby=True)

    def prepare_for_nap(self, c: Class, sim_time: float):
        self.common_behaviour([x for x in AREA_DICT[self.class_id] if x != -1], StudentStatus.PREPARING,
                              StudentStatus.PREPARING, sim_time, True, c=c, nearby=True)

    def do_nap(self, c: Class, sim_time: float):
        if self.status != StudentStatus.NAPPING or self.toilet_state == ToiletState.NOT_USING:
            self.status = StudentStatus.NAPPING
            self.current_target = c.nap_manager.assign_seat(self.ped_id)

    def clean_up_for_nap(self, c: Class, sim_time: float):
        if self.status != StudentStatus.CLEANING_UP:
            c.nap_manager.free_seat(self.ped_id)
        self.common_behaviour([x for x in AREA_DICT[self.class_id] if x != -1], StudentStatus.CLEANING_UP,
                              StudentStatus.CLEANING_UP, sim_time, True, c=c, nearby=True)

    def prepare_free_choice(self, c: Class, sim_time: float):

        """
        Nothing to prepare...

        :param c:
        :param sim_time:
        :return:
        """
        pass

    def do_free_choice(self, c: Class, sim_time: float):
        if self.status == StudentStatus.FREE:
            random_activity = random.choice([StudentStatus.LEARNING, StudentStatus.OTHERS])
            if random_activity == StudentStatus.LEARNING:
                self.current_target = c.seat_manager.assign_seat(self.ped_id)
                self.status = StudentStatus.LEARNING
            elif random_activity == StudentStatus.OTHERS:
                self.current_target = random.choice([x for x in AREA_DICT[c.class_id] if x != -1])
                self.status = StudentStatus.OTHERS
            self.free_time_activity_end_time = sim_time + np.random.normal(300, 20)
        if sim_time > self.free_time_activity_end_time:
            if self.status == StudentStatus.LEARNING:
                c.seat_manager.free_seat(self.ped_id)
            self.status = StudentStatus.FREE

    def clean_up_free_choice(self, c: Class, sim_time: float):
        if self.status != StudentStatus.CLEANING_UP:
            if self.status == StudentStatus.LEARNING:
                c.seat_manager.free_seat(self.ped_id)
        self.common_behaviour([x for x in AREA_DICT[self.class_id] if x != -1], StudentStatus.CLEANING_UP,
                              StudentStatus.CLEANING_UP, sim_time, True, c=c, nearby=True)

    def end(self, c: Class, sim_time: float):
        if not self.set_to_end:
            self.free_time_activity_end_time = sim_time + np.random.normal(270, 180)
            self.set_to_end = True

        # leave at random timing
        if sim_time >= self.free_time_activity_end_time:
            self.current_target = EXIT

        else:
            self.common_behaviour([x for x in AREA_DICT[self.class_id] if x != -1], StudentStatus.FREE,
                                  StudentStatus.FREE, sim_time, True, c=c, nearby=True)


class Principal(StaffAgent, metaclass=Singleton):
    """
    Principal agent ( only one)
    """
    _initialised = False

    def __init__(self, ped_id=None, class_id=None, targets=None):
        if not self._initialised:
            super().__init__(ped_id, class_id, targets)
            Principal._initialised = True
            self.status = PrincipalStatus.FREE
            self.chill_spot = None
            self.interested_class = None

    def reset(self):
        self.status = PrincipalStatus.FREE
        self.chill_spot = None
        self.interested_class = None
        self.interest_stack = TargetPriorityQueue()
        self.toilet_state = Constants.ToiletState.NOT_USING
        self.fidget_time = 0.0
        self.status = None
        self.target_end_time = 0.0
        self.next_toilet_time = np.random.normal(self.bladder_cap, 45)
        self.free_time_activity_end_time = 0
        self.set_to_end = False
        self.toilet_change_target_time = 0
        self.old_target = None
        self.current_pos = (0, 0)
        self.reach_intermediate = False
        self.intermediate_targets = []

    def update_agent_movement(self, c: Class, sim_time: float):
        # Check if the agent needs to go toilet and can only go during doing event phase
        if self.need_go_toilet(
                sim_time) and self.toilet_state == ToiletState.NOT_USING:
            self.toilet_state = ToiletState.WANT_TO_GO_TOILET
            self.update_bladder_full_timing(sim_time)

        if self.toilet_state == ToiletState.JUST_ENDED:
            self.current_target = PRINCIPAL_TABLE
            self.toilet_state = ToiletState.NOT_USING

        # if already going toilet no need to update anything
        if self.toilet_state != ToiletState.NOT_USING:
            return

        # Supervising work here
        if self.status == PrincipalStatus.FREE:
            random_activity = random.choice(
                [PrincipalStatus.IN_OFFICE, PrincipalStatus.SUPERVISING, PrincipalStatus.CHILL])

            if random_activity == PrincipalStatus.IN_OFFICE:
                self.status = PrincipalStatus.IN_OFFICE
                self.current_target = PRINCIPAL_TABLE
                self.free_time_activity_end_time = sim_time + np.random.normal(1800, 120)

            elif random_activity == PrincipalStatus.SUPERVISING:
                self.interested_class = self.class_id
                self.status = PrincipalStatus.SUPERVISING
                self.free_time_activity_end_time = sim_time + np.random.normal(450, 60)
            elif random_activity == PrincipalStatus.CHILL:
                self.chill_spot = random.choice([STAFF_HANGOUT_SPOT_BREAK_ROOM, STAFF_HANGOUT_SPOT_KITCHENETTE])
                self.status = PrincipalStatus.CHILL
                self.free_time_activity_end_time = sim_time + np.random.normal(900, 90)

        if sim_time >= self.free_time_activity_end_time:
            if self.status == PrincipalStatus.IN_OFFICE:
                pm = PrincipalRoomManager()
                # if there is somebody in the office
                if not pm.is_empty():
                    return
            self.status = PrincipalStatus.FREE
        elif self.status == PrincipalStatus.CHILL:
            self.common_behaviour(AREA_DICT[self.chill_spot], PrincipalStatus.CHILL, PrincipalStatus.CHILL, sim_time,
                                  c=c, random_movement=True)
        elif self.status == PrincipalStatus.SUPERVISING:
            self.common_behaviour([x for x in AREA_DICT[self.interested_class] if x != -1], PrincipalStatus.SUPERVISING,
                                  PrincipalStatus.SUPERVISING, sim_time,
                                  c=c, random_movement=True)

    def update_interested_class(self, cm):
        classes = [c.class_id for c in cm.classes.values() if c.event_state != EventState.ALL_FINISHED]
        if classes:
            self.class_id = random.choice(classes)

    def is_free(self):
        return self.status == PrincipalStatus.FREE

    def in_office(self):
        return self.status == PrincipalStatus.IN_OFFICE and self.toilet_state == ToiletState.NOT_USING
