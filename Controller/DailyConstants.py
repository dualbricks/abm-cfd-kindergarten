import json
import math
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from tabulate import tabulate
from ProjectConstants import PROJECT_PATH

class ActivityType(Enum):
    LARGE_GROUP = 0
    LESSON = 1
    MEAL = 2
    NAP = 3
    FREE_CHOICE_ACTIVITY = 4
    OUT_DOOR = 5


class EventState(Enum):
    PREPARING = 0
    IN_PROGRESS = 1
    CLEAN_UP = 2
    FINISHED = 3
    YET_TO_START = 4
    ALL_FINISHED = 5


class StaffStatus(Enum):
    FREE = 0
    TEACHING = 1
    PREPARING = 2
    OTHERS = 3
    CLEANING_UP = 4
    CHILLING = 5
    BREAK = 6
    TALKING = 7


class PrincipalStatus(Enum):
    FREE = 0
    IN_OFFICE = 1
    SUPERVISING = 2
    CHILL = 3


class StudentStatus(Enum):
    FREE = 0
    LEARNING = 1
    EATING = 2
    OTHERS = 3
    PREPARING = 4
    CLEANING_UP = 5
    NAPPING = 6


class StaffType(Enum):
    CLASS = 0
    FREE_ROAMING = 1


CUBICLES = [x for x in range(103, 107)]
SINK = [x for x in range(109, 113)]
SINK_WAITING_AREA = 101
TOILET_ENTRANCE = 144

KITCHENETTE = 8000
PRINCIPAL_ROOM = 8001
BREAK_ROOM = 8002
CLASSROOM_3 = 217
CLASSROOM_4 = 218
CLASSROOM_5 = 219
CLASSROOM_6 = 102
FREE_STAFF_GROUP = 500
STAFF_HANGOUT_SPOT_BREAK_ROOM = 8003
STAFF_HANGOUT_SPOT_KITCHENETTE = 8004
class_list = [(CLASSROOM_3, "K1"), (CLASSROOM_4, "N2"), (CLASSROOM_5, "N1"), (CLASSROOM_6, "K2")]
ENDING_TIME = 900
PREPARE_DURATION = 45
PRINCIPAL_TABLE = 70
EXIT = 2000
INTERMEDIATE_TOILET_TARGET = 2001
INTERMEDIATE_TOILET_TARGET_2 = 2002
INTERMEDIATE_TOILET_TARGET_POS = (0, 0)
INTERMEDIATE_TOILET_TARGET_2_POS = (0, 0)


json_path = f"{PROJECT_PATH}/target_center_daily_with_table.json"
with open(json_path) as f:
    target_dict = json.load(f)
    INTERMEDIATE_TOILET_TARGET_POS = target_dict[str(INTERMEDIATE_TOILET_TARGET)]
    INTERMEDIATE_TOILET_TARGET_2_POS = target_dict[str(INTERMEDIATE_TOILET_TARGET_2)]

STUDENT_DICT = {
    CLASSROOM_3: [x for x in range(180, 200)],
    CLASSROOM_4: [x for x in range(202, 217)],
    CLASSROOM_5: [x for x in range(83, 95)],
    CLASSROOM_6: [x for x in range(95, 101)] + [x for x in range(114, 120)] + [x for x in range(135, 141)] + [x for x in
                                                                                                              range(145,
                                                                                                                    149)] + [
                     165, 158, 107]
}

STAFF_DICT = {
    CLASSROOM_3: [178, 179],
    CLASSROOM_4: [200, 201],
    CLASSROOM_5: [82, 251],
    CLASSROOM_6: [176, 177],
    FREE_STAFF_GROUP: [250, 252, 253, 254]
}

STAFF_NAP_TIME_STATUS = [StaffStatus.BREAK, StaffStatus.CHILLING, StaffStatus.TALKING, StaffStatus.TEACHING]

TABLE_DICT = {
    CLASSROOM_3: [234, 236, 235, 237],
    CLASSROOM_4: [240, 217, 241, 218],
    CLASSROOM_5: [233, 232, 231],
    CLASSROOM_6: [227, 228, 229, 230, 243, 242]
}

CHAIR_DICT = {
    CLASSROOM_3: [4000, 4001, 4002, 4003, 4004, 4005, 4006, 4007, 4008, 4009, 4010, 4011, 4012, 4013, 4014, 4015, 4016,
                  4017, 4018, 4019, 4020, 4021, 4022, 4023],
    CLASSROOM_4: [4024, 4025, 4026, 4027, 4028, 4029, 4030, 4031, 4032, 4033, 4034, 4035, 4036, 4037, 4038, 4039, 4040,
                  4041, 4042, 4043, 4044, 4045, 4046, 4047],
    CLASSROOM_5: [4048, 4049, 4050, 4051, 4052, 4053, 4054, 4055, 4056, 4057, 4058, 4059, 4060, 4061, 4062, 4063, 4064,
                  4065],
    CLASSROOM_6: [4066, 4067, 4068, 4069, 4070, 4071, 4072, 4073, 4074, 4075, 4076, 4077, 4078, 4079, 4080, 4081, 4082,
                  4083, 4084, 4085, 4086, 4087, 4088, 4089, 4090, 4091, 4092, 4093, 4094, 4095, 4096, 4097, 4098, 4099,
                  4100, 4101],
    PRINCIPAL_ROOM: [71, 72]
}
AREA_DICT = {
    TOILET_ENTRANCE: [113, 141, 142, 143],
    CLASSROOM_3: [5, 25, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49],
    CLASSROOM_4: [x for x in range(58, 70)] + [x for x in range(219, 225)],
    CLASSROOM_5: [81, 50, 52, 53, 54, 56, -1, 51, -1, -1, 55, 57],
    CLASSROOM_6: [120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 149, 150, 151, 152, 153],
    KITCHENETTE: [76, 77, 78, 80, 79],
    BREAK_ROOM: [75, 73, 74],
    PRINCIPAL_ROOM: [71, 72],
    STAFF_HANGOUT_SPOT_BREAK_ROOM: [102, 225, 226, 238, 239, 244],
    STAFF_HANGOUT_SPOT_KITCHENETTE: [247, 245, 246, 247, 248, 249]
}

NAP_POSITION_DICT = {
    CLASSROOM_3: [6000, 6001, 6002, 6003, 6004, 6005, 6006, 6007, 6008, 6009, 6010, 6011, 6012, 6013, 6014, 6015, 6016,
                  6017, 6018, 6019, 6020, 6021, 6022, 6023, 6024, 6025, 6026, 6027, 6028, 6029, 6030, 6031, 6032, 6033,
                  6034, 6035, 6036, ],
    CLASSROOM_4: [6037, 6038, 6039, 6040, 6041, 6042, 6043, 6044, 6045, 6046, 6047, 6048, 6049, 6050,
                  6051, 6052, 6053, 6054, 6055, 6056, 6057, 6058, 6059, 6060, 6061, 6062, 6063, 6064, 6065, 6066, 6067,
                  6068, 6069, 6070, 6071, 6072, 6073, 6074, 6075, 6076, 6077, 6078, 6079, 6080, 6081, 6082, 6083,
                  6085, 6086, 6087, 6088, 6089, 6090, 6091, 6092, 6093, 6094, 6095, 6096, 6097, 6098, 6099],
    CLASSROOM_5: [6100, 6101, 6102, 6103, 6104, 6105, 6106, 6107, 6108, 6109, 6110, 6111, 6112,
                  6113, 6114, 6115, 6116, 6117, 6118, 6119, 6120, 6121, 6122, 6123, 6124, 6125, 6126, 6127, 6128, ],
    CLASSROOM_6: [6129, 6130, 6131, 6132, 6133, 6134, 6135, 6136, 6137, 6138, 6139, 6140, 6141, 6142, 6143, 6144,
                  6145, 6146, 6147, 6148, 6149, 6150, 6151, 6152, 6153, 6154, 6155, 6156, 6157, 6158, 6159,
                  6160, 6161, 6162, 6163, 6164, 6165, 6166, 6167, 6168, 6169, 6170, 6171, 6172, 6173, 6174,
                  6175, 6176, 6177, 6178, 6179, 6180, 6181, 6182, 6183, 6184, 6185, 6186, 6187, 6188, 6189, 6190, 6191]
}
GROUP_SIZE = {
    CLASSROOM_3: (3, 4),
    CLASSROOM_4: (3, 6),
    CLASSROOM_5: (2, 6),
    CLASSROOM_6: (4, 5),
    STAFF_HANGOUT_SPOT_BREAK_ROOM: (3, 2),
    STAFF_HANGOUT_SPOT_KITCHENETTE: (2, 3)
}

LEADER_POSITION = {
    CLASSROOM_3: 40,
    CLASSROOM_4: 61,
    CLASSROOM_5: 51,
    CLASSROOM_6: 122
}

SCHEDULE_DICT = {
    CLASSROOM_3: [(ActivityType.MEAL, 1800), (ActivityType.LESSON, 1800), (ActivityType.LESSON, 3600),
                  (ActivityType.LESSON, 3600), (ActivityType.LESSON, 3600)],

    CLASSROOM_4: [(ActivityType.LESSON, 1800), (ActivityType.LESSON, 2700), (ActivityType.LESSON, 3600), (ActivityType.LESSON, 1200),
                  (ActivityType.LESSON, 2400),
                  (ActivityType.LESSON, 900), (ActivityType.MEAL, 1800),
                  (ActivityType.NAP, 9000),
                  (ActivityType.MEAL, 1800), (ActivityType.LESSON, 3600),
                  (ActivityType.LESSON, 1800),
                  (ActivityType.FREE_CHOICE_ACTIVITY, 3600)],

    CLASSROOM_5: [(ActivityType.LESSON, 1800), (ActivityType.LESSON, 2700), (ActivityType.LESSON, 3600),
                  (ActivityType.LESSON, 1200), (ActivityType.LESSON, 3300), (ActivityType.MEAL, 1800), (ActivityType.NAP, 9000),
                  (ActivityType.MEAL, 1800), (ActivityType.LESSON, 1800), (ActivityType.MEAL, 1800),
                  (ActivityType.LESSON, 900), (ActivityType.LESSON, 900), (ActivityType.FREE_CHOICE_ACTIVITY, 3600)],

    CLASSROOM_6: [(ActivityType.MEAL, 1800), (ActivityType.LESSON, 1800), (ActivityType.LESSON, 3600),
                  (ActivityType.LESSON, 3600), (ActivityType.LESSON, 3600)],
}

def test():
    for key in STUDENT_DICT.keys():
        print(len(STUDENT_DICT[key]))
        print("------------------------------------")


def get_targets_from_table():
    sequence = [TABLE_DICT[CLASSROOM_3], TABLE_DICT[CLASSROOM_4], TABLE_DICT[CLASSROOM_5], TABLE_DICT[CLASSROOM_6]]
    print(sequence)
    starting_id = 4000

    for tables in sequence:
        temp = []
        for table in tables:
            temp.extend([x for x in range(starting_id, starting_id + 6)])
            starting_id += 6

        print(temp)



def get_schematic_schedule_for_each_classroom():
    # Start time
    start_time = datetime.strptime("08:30", "%H:%M")

    # Print tables
    for classroom, activities in SCHEDULE_DICT.items():
        print(f"\nSchedule for {classroom}")
        table = []
        current_time = start_time
        for activity, duration in activities:
            end_time = current_time + timedelta(seconds=duration)
            table.append([
                current_time.strftime("%H%M"),
                end_time.strftime("%H%M"),
                activity
            ])
            current_time = end_time
        print(tabulate(table, headers=["Start", "End", "Activity"], tablefmt="grid"))

if __name__ == "__main__":
    get_schematic_schedule_for_each_classroom()