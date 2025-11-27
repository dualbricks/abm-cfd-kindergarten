import random
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np

from Controller import DailyConstants
from Controller.Agent import StudentAgent, StaffAgent, BaseAgent, Principal
from Controller.Constants import ToiletState
from Controller.DailyConstants import ActivityType, EventState, PRINCIPAL_ROOM, StaffStatus, StaffType
from Controller.SeatManager import TableSeatManager, NapSeatManager
from Controller.Singleton import Singleton


class Class:
    def __init__(self, class_id, class_name, class_schedule: list, students=None, staffs=None):
        self.class_id: str = class_id
        self.class_name: str = class_name
        self.class_schedule: List[Tuple[ActivityType, int]] = class_schedule
        self.students: List[StudentAgent] = students
        self.staffs: List[StaffAgent] = staffs
        self.current_event: Tuple[ActivityType, int] = self.class_schedule[0]
        self.current_event_end_time: float = 0.0
        self.leader: [StaffAgent, None] = None
        self.event_state: EventState = EventState.YET_TO_START
        self.prepare_end_time: float = 0.0
        self.clean_up_end_time: float = 0.0
        self.spread_dict = None
        self.seat_manager = TableSeatManager(self.class_id)
        self.nap_manager = NapSeatManager(self.class_id)
        self.agents = []
        self.event_index = 0
        self.prepare_time = 0
        self.clean_up_time = 0
        self.free_staff: List[StaffAgent, None] = []

    def update_current_event(self, sim_time):
        """
        Update the Event state of the current event and also progress to the next event if it is done
        :param sim_time:
        :return:
        """
        if self.event_state == EventState.ALL_FINISHED:
            return
        last_event = False
        PREPARE_DURATION = np.random.normal(120, 30)

        if self.event_index < len(self.class_schedule) - 1:
            next_event = self.class_schedule[self.event_index + 1]
        else:
            last_event = True
        # for first event
        if self.event_state == EventState.YET_TO_START:
            self.pare_time = np.random.normal(PREPARE_DURATION, 3)
            self.prepare_end_time = sim_time + self.prepare_time
            self.clean_up_time = np.random.normal(PREPARE_DURATION, 3)
            self.current_event_end_time = self.prepare_end_time + (
                    self.current_event[1] - self.prepare_time - self.clean_up_time)
            self.clean_up_end_time = self.current_event_end_time + self.clean_up_time
            self.event_state = EventState.PREPARING

        # start the next event
        if self.event_state == EventState.FINISHED:
            if not last_event:
                self.prepare_time = np.random.normal(PREPARE_DURATION, 3)
                self.clean_up_time = np.random.normal(PREPARE_DURATION, 3)
                self.prepare_end_time = sim_time + self.prepare_time
                self.current_event = next_event
                self.event_state = EventState.PREPARING
                self.event_index += 1
            else:
                self.event_state = EventState.ALL_FINISHED

        # Preparation stage of the event
        if self.event_state == EventState.PREPARING and self.can_proceed_to_next_event_state():
            if sim_time > self.prepare_end_time:
                self.current_event_end_time = sim_time + (
                        self.current_event[1] - self.prepare_time - self.clean_up_time)
                self.event_state = EventState.IN_PROGRESS

        # Main event stage
        if self.event_state == EventState.IN_PROGRESS and self.can_proceed_to_next_event_state():
            if sim_time > self.current_event_end_time:
                self.clean_up_end_time = sim_time + self.clean_up_time
                self.event_state = EventState.CLEAN_UP

        # Clean up stage of the event
        if self.event_state == EventState.CLEAN_UP and self.can_proceed_to_next_event_state():
            if sim_time > self.clean_up_end_time:
                self.event_state = EventState.FINISHED

        print("Event State: " + f'{self.class_name} ' + str(self.event_state) + f' Activity: {self.current_event[0]}')

    def can_proceed_to_next_event_state(self):
        for agent in self.agents:
            if agent.toilet_state != ToiletState.NOT_USING:
                return False
        return True

    def get_free_staff(self):
        free_staffs = []
        for staff in self.staffs:
            if staff.is_free():
                free_staffs.append(staff)
        return free_staffs

    def update_class_members(self, students=None, staffs=None):
        self.students = students
        self.staffs = staffs
        self.leader = staffs[0]
        self.agents = self.students + self.staffs

    def find_nearby_grid_from_leader(self, connectivity=8):
        return self.find_nearby_grid(self.leader.current_target, connectivity)

    def find_nearby_grid_by_id(self, idx, connectivity=8):
        return self.find_nearby_grid(idx, connectivity)

    def find_nearby_grid(self, idx, connectivity=8):
        grid = DailyConstants.AREA_DICT[self.class_id]
        nums_rows, nums_cols = DailyConstants.GROUP_SIZE[self.class_id]
        index = DailyConstants.AREA_DICT[self.class_id].index(idx)
        grid_size = DailyConstants.GROUP_SIZE[self.class_id]
        i = index // grid_size[1], index % grid_size[1]
        row, col = i
        neighbors = []

        # 4-connected neighbors (up, down, left, right)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # If 8-connected, include diagonal neighbors
        if connectivity == 8:
            directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < nums_rows and 0 <= new_col < nums_cols:
                index = new_row * nums_cols + new_col
                neighbors.append(grid[index])
        neighbors = [neighbor for neighbor in neighbors if neighbor != -1]
        return neighbors

    def get_evenly_speared_dict(self):
        if self.spread_dict is None:
            self.spread_dict = distribute_evenly_around_class_room(self)
        return self.spread_dict

    def add_free_staff(self, staff):
        self.free_staff.append(staff)

        for staff in self.free_staff:
            staff.class_id = self.class_id
            staff.status = StaffStatus.FREE


def distribute_evenly_around_class_room(c: Class):
    distribution = defaultdict(list)

    temp = c.students.copy()
    random.shuffle(temp)

    for i, agent in enumerate(temp):
        filtered_area = [x for x in DailyConstants.AREA_DICT[c.class_id] if x != -1]
        distribution[filtered_area[i % len(filtered_area)]].append(
            agent.ped_id)
    inverse = {}
    for k, v in distribution.items():
        for x in v:
            inverse.setdefault(x, []).append(k)
    return inverse


class ClassManager(metaclass=Singleton):
    """
    Class Manager to handle class events
    """
    _initialised = False

    def __init__(self):
        if not self._initialised:
            self.agents = {}
            self.classes: Dict[Class, {}] = {}
            self.initialise_classes()
            self.initialise_agents()
            self.free_agents = []
            self._initialised = True

    def reset(self):
        self.agents = {}
        self.classes: Dict[Class, {}] = {}
        self.initialise_classes()
        self.initialise_agents()

    def initialise_classes(self):
        for c in DailyConstants.class_list:
            self.classes[c[0]] = Class(c[0], c[1], class_schedule=DailyConstants.SCHEDULE_DICT[c[0]])

    def initialise_agents(self):
        for c in self.classes.keys():
            student_list = []
            staff_list = []
            for student in DailyConstants.STUDENT_DICT[c]:
                t = StudentAgent(student, c, self.classes[c].class_schedule)
                self.agents[student] = t
                student_list.append(t)
            for staff in DailyConstants.STAFF_DICT[c]:
                t = StaffAgent(staff, c, self.classes[c].class_schedule)
                self.agents[staff] = t
                staff_list.append(t)
            self.update_class_members(c, student_list, staff_list)

        for staff in DailyConstants.STAFF_DICT[DailyConstants.FREE_STAFF_GROUP]:
            c = random.choice(list(self.classes.keys()))
            t = StaffAgent(staff, c, None, StaffType.FREE_ROAMING)

            self.agents[staff] = t
        self.rotate_free_staff()

    def update_class_members(self, c_id, c, s):
        self.classes[c_id].update_class_members(c, s)

    def update_class_movement(self, sim_time):
        c: Class
        agent: BaseAgent
        for c in self.classes.values():
            for agent in c.agents:
                agent.update_agent_movement(c, sim_time)
            for staff in c.free_staff:
                staff.update_agent_movement(c, sim_time)
            c.update_current_event(sim_time)

    def update_free_staff(self, sim_time):
        # Only swap every 1 hour (3600 seconds)
        if sim_time % 3600 != 0:
            return
        self.rotate_free_staff()

    def rotate_free_staff(self):

        class_ids = list(self.classes.keys())

        # Clear current free staff assignments
        for c in self.classes.values():
            c.free_staff.clear()

        free_staff_ids = DailyConstants.STAFF_DICT[DailyConstants.FREE_STAFF_GROUP].copy()
        random.shuffle(free_staff_ids)
        for idx, staff_id in enumerate(free_staff_ids):
            staff = self.agents[staff_id]

            # Initialise rotation index staggered by initial position
            if not hasattr(staff, "_rotation_index"):
                staff._rotation_index = idx % len(class_ids)

            # Move to next class in rotation
            staff._rotation_index = (staff._rotation_index + 1) % len(class_ids)
            assigned_class_id = class_ids[staff._rotation_index]
            self.classes[assigned_class_id].add_free_staff(staff)
