import random

from Controller.DailyConstants import CHAIR_DICT, NAP_POSITION_DICT
from Controller.Singleton import Singleton


class TableSeatManager:
    """
    Tracks seating
    """

    def __init__(self, class_id):
        self.seats = {}
        self.assigned_seats = {}
        self.class_id = class_id
        self.initialize_seats()

    def initialize_seats(self):
        self.seats = dict.fromkeys(CHAIR_DICT[self.class_id], None)

    def assign_seat(self, ped_id):

        if ped_id in self.assigned_seats.keys():
            return self.assigned_seats[ped_id]

        if len(self.assigned_seats) < len(self.seats):
            available_seats = [key for key, value in self.seats.items() if value is None]
            random_seat = random.choice(available_seats)
            self.assigned_seats[ped_id] = random_seat
            self.seats[random_seat] = True
            return random_seat
        else:
            raise KeyError("Should have enough seats!!!", ped_id, self.class_id)

    def free_seat(self, ped_id):
        assigned_seat = self.assigned_seats[ped_id]
        self.assigned_seats.pop(ped_id)
        self.seats[assigned_seat] = None

    def is_seat_available(self):
        return len(self.assigned_seats) < len(self.seats)


class NapSeatManager(TableSeatManager):
    """
    Same as Tables but different set of targets
    """

    def __init__(self, class_id):
        super().__init__(class_id)
        self.initialize_seats()

    def initialize_seats(self):
        self.seats = dict.fromkeys(NAP_POSITION_DICT[self.class_id], None)


class PrincipalRoomManager(TableSeatManager, metaclass=Singleton):
    _initialised = False

    def __init__(self, class_id=None):
        if not self._initialised:
            super().__init__(class_id)
            self.initialize_seats()
            PrincipalRoomManager._initialised = True

    def reset(self):
        self.seats = {}
        self.assigned_seats = {}
        self.initialize_seats()
    def is_empty(self):
        return len(self.assigned_seats.keys()) == 0
