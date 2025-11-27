from enum import Enum

CHAIRS = [x for x in range(41, 71)]
AGENTS = [2, 5, 40] + [x for x in range(71, 98)]
CUBICLES = [x for x in range(103, 107)]
SINK = [x for x in range(109, 113)]
SINK_WAITING_AREA = 101
TOILET_ENTRANCE = 144
TABLE = 9999
SUBGROUP_R = 102
SUBGROUP_T = 100
SUBGROUP_B = 107
SUBGROUP_RR = 178
DENSITY_AREA_DICT = {
    TOILET_ENTRANCE: [113, 141, 142, 143],
    SUBGROUP_R: [x for x in range(120, 135)] + [149, 150, 151, 152, 153],
    SUBGROUP_T: [x for x in range(114, 120)],
    SUBGROUP_B: [x for x in range(135, 141)] + [98, 99, 145, 146, 147, 148],
    SUBGROUP_RR: [158, 165, 177, 176]

}

ALL_SUBGROUP_IDS = DENSITY_AREA_DICT[SUBGROUP_T] + DENSITY_AREA_DICT[SUBGROUP_B] + DENSITY_AREA_DICT[SUBGROUP_R]
ENDING_TIME = 780

GRID_DENSITY_AREA_DICT = {
    TOILET_ENTRANCE: [113, 141, 142, 143],
    SUBGROUP_R: [120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 149, 150, 151, 152, 153],
    SUBGROUP_T: [114, 115, 116, 117, 118, 119],
    SUBGROUP_B: [135, 138, 139, 136, 137, 140, 98, 99, 145, 146, 147, 148],
    SUBGROUP_RR: [158, 165, 177, 176]
}

SUBGROUP_SIZE = {
    SUBGROUP_T: (2, 3),
    SUBGROUP_B: (3, 4),
    SUBGROUP_R: (4, 5),
    SUBGROUP_RR: (2, 2)
}


# Toilet State

class ToiletState(Enum):
    NOT_USING = 0
    IN_QUEUE = 1
    IN_CUBICLE = 2
    IN_SINK = 3
    WAITING_FOR_SINK = 4
    WANT_TO_GO_TOILET = 5
    WAITING_FOR_QUEUE = 6
    JUST_ENDED = 7

AGENT_SETTINGS = {
    "Group": None,
    "Experiment": None,
    "Starting": None
}

AGENT_HEADING_STARTING = {
    2: (1, 0),
    5: (0, -1),
    40: (0, -1),
    71: (0, -1),
    72: (0, -1),
    73: (0, -1),
    74: (0, -1),
    75: (0, -1),
    76: (0, -1),
    77: (0, -1),
    78: (0, -1),
    79: (0, -1),
    80: (0, -1),
    81: (0, -1),
    82: (0, -1),
    83: (-1, 0),
    84: (0, 1),
    85: (0, 1),
    86: (0, 1),
    87: (0, 1),
    88: (0, 1),
    89: (0, 1),
    90: (0, 1),
    91: (0, 1),
    92: (0, 1),
    93: (0, 1),
    94: (0, 1),
    95: (0, 1),
    96: (0, 1),
    97: (0, 1)
}
