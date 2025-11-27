import math
import random
import json
import sys
from typing import List

from Controller import Constants, DailyConstants
from Controller.Constants import TOILET_ENTRANCE, DENSITY_AREA_DICT, SUBGROUP_R, SUBGROUP_B, SUBGROUP_T, CHAIRS, \
    TABLE
from Controller.DailyConstants import TABLE_DICT





def random_simple_routing():
    """
    Randomly chooses route based on Boon Long's design
    :return: [route]
    """
    possible_targets = [TOILET_ENTRANCE, SUBGROUP_R, SUBGROUP_B, SUBGROUP_T, TABLE]

    length = random.randint(1, len(possible_targets))
    random_route_ids = []
    count = 0
    while count < length:
        target = random.choice(possible_targets)
        if target not in random_route_ids:
            random_route_ids.append(target)
        count += 1
    random_route = []
    for target in random_route_ids:
        if target != TOILET_ENTRANCE and target != TABLE:
            target = random.choice(DENSITY_AREA_DICT[target])
        random_route.append(target)
    return random_route


def random_grouping_routing(grouping):
    target_dict = {}

    possible_targets = [TOILET_ENTRANCE, SUBGROUP_R, SUBGROUP_B, SUBGROUP_T, TABLE]
    random.shuffle(possible_targets)
    for index, g in enumerate(grouping):
        length = random.randint(1, len(possible_targets))
        random_route_ids = []
        if length:
            random_route_ids = random.sample(possible_targets, length)

        for i, target in enumerate(random_route_ids):
            if target != TOILET_ENTRANCE and target != TABLE:
                random_route_ids[i] = random.choice(DENSITY_AREA_DICT[target])
        for a in g:
            target_dict[a] = random_route_ids

    return target_dict


def split_into_random_groups(agents, min_size=5, max_size=5):
    random.shuffle(agents)  # Shuffle agents to randomize order
    groups = []
    i = 0

    while i < len(agents):
        # Determine the group size randomly within the range
        group_size = random.randint(min_size, max_size)
        # Ensure the last group doesn't exceed the remaining agents
        if max_size >= len(agents) - i >= min_size:
            group_size = len(agents) - i
        group = agents[i:i + group_size]
        groups.append(group)
        i += group_size

    return groups


def create_target_center_dictionary(filename, output_filename):
    target_list = {}
    with open(filename) as f:
        d = json.load(f)
        t = d["targets"]
        for target in t:
            target_list[target["id"]] = (round(target["shape"]["x"] + target["shape"]["width"] / 2, 2),
                                         round(target["shape"]["y"] + target["shape"]["height"] / 2, 2))
        print(target_list)

    with open(output_filename, "w") as f:
        json.dump(target_list, f, indent=4)


def target_id_converter(target_list):
    for i, target in enumerate(target_list):
        if target != TOILET_ENTRANCE and target != TABLE:
            target_list[i] = random.choice(DENSITY_AREA_DICT[target])
    return target_list


def find_grid_index(target_id, subgroup_id):
    index = Constants.GRID_DENSITY_AREA_DICT[subgroup_id].index(target_id)
    grid_size = Constants.SUBGROUP_SIZE[subgroup_id]
    return index // grid_size[1], index % grid_size[1]


def find_nearby_grid(i, subgroup_id, connectivity=8):
    grid = Constants.GRID_DENSITY_AREA_DICT[subgroup_id]
    nums_rows, nums_cols = Constants.SUBGROUP_SIZE[subgroup_id]
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
    return neighbors


def calculate_coordinates_for_table(file_name, output, table_ids, starting_id=4000, chair_dim=(0.2, 0.2)):
    with open(file_name) as f:
        d = json.load(f)

    # get table attributes

    tables = []

    for obs in d["obstacles"]:
        if obs["id"] in table_ids:
            tables.append(obs)

    ordered_dict = {id_: index for index, id_ in enumerate(table_ids)}

    sorted_tables = sorted(tables, key=lambda obj: ordered_dict.get(obj["id"], float("inf")))

    print(sorted_tables)
    targets = d["targets"]

    new_targets = [t for t in targets if t["id"] < 4000]
    for table in sorted_tables:

        # if long side of the table is horizontal
        if table["shape"]["width"] >= 1.0:
            chairs, starting_id = get_chair_objs_for_table((table["shape"]["x"], table["shape"]["y"]), "h", starting_id)
        else:
            chairs, starting_id = get_chair_objs_for_table((table["shape"]["x"], table["shape"]["y"]), "v", starting_id)
        for chair in chairs:
            new_targets.append(chair)

    d["targets"] = new_targets
    with open(output, "w") as f:
        json.dump(d, f, indent=4)


def get_chair_objs_for_table(table_pos, direction, starting_id=4000):
    t_x = table_pos[0]
    t_y = table_pos[1]
    if direction == "h":
        chair_offsets = [(t_x - 0.1 - 0.2, t_y + 0.1), (t_x + 1.0 + 0.1, t_y + 0.1), (t_x + 0.15, t_y + 0.5 + 0.2),
                         (t_x + 0.7, t_y + 0.5 + 0.2), (t_x + 0.15, t_y - 0.2 - 0.1), (t_x + 0.7, t_y - 0.2 - 0.1)]
    else:
        chair_offsets = [(t_x + 0.15, t_y + 1.0 + 0.2), (t_x + 0.15, t_y - 0.2 - 0.1), (t_x - 0.2 - 0.1, t_y + 0.15),
                         (t_x - 0.2 - 0.1, t_y + 0.7), (t_x + 0.5 + 0.2, t_y + 0.15), (t_x + 0.2 + 0.5, t_y + 0.7)]

    chairs = []

    for chair_offset in chair_offsets:
        chair = {
            "id": starting_id,
            "shape": {
                "x": chair_offset[0],
                "y": chair_offset[1],
                "width": 0.2,
                "height": 0.2,
                "type": "RECTANGLE"
            },
            "visible": True,
            "absorber": {
                "enabled": False,
                "deletionDistance": 0.1
            },
            "waiter": {
                "enabled": True,
                "distribution": {
                    "type": "org.vadere.state.attributes.distributions.AttributesConstantDistribution",
                    "updateFrequency": 7200.0
                },
                "individualWaiting": True
            },
            "leavingSpeed": -1.0,
            "parallelEvents": 0
        }
        starting_id += 1
        chairs.append(chair)

    return chairs, starting_id


def isCollided(r1, r2):
    """
    Check if two rectangles are collided
    by checking on the following conditions:
    Is the RIGHT edge of r1 to the RIGHT of the LEFT edge of r2?
    Is the LEFT edge of r1 to the LEFT of the RIGHT edge of r2?
    Is the BOTTOM edge of r1 BELOW the TOP edge of r2?
    Is the TOP edge of r1 ABOVE the BOTTOM edge of r2?
    :param Rec2: Rectangle
    :return:
    bool value true if collided
    """
    r1x, r1y, r1w, r1h = r1

    r2x, r2y, r2w, r2h = r2

    if (r1x + r1w >= r2x and
            r1x <= r2x + r2w and
            r1y + r1h >= r2y and
            r1y <= r2y + r2h):
        return True
    return False


def get_napping_positions(targets, tables, grid_ids, starting_id=6000):
    grids = []

    for grid in targets:
        if grid["id"] in grid_ids:
            grids.append(grid)

    ordered_dict = {id_: index for index, id_ in enumerate(grid_ids)}

    sorted_grids = sorted(grids, key=lambda obj: ordered_dict.get(obj["id"], float("inf")))

    small_square_size = 0.2
    spacing = 0.4
    positions = []
    new_nap_positions = []
    for grid in sorted_grids:
        # Iterate over possible positions in the 1m x 1m square
        for i in range(2):  # 2 positions along x (0, 0.6)
            for j in range(2):  # 2 positions along y (0, 0.6)
                x = grid["shape"]["x"] + i * (small_square_size + spacing)
                y = grid["shape"]["y"] + j * (small_square_size + spacing)
                is_valid = all(not isCollided((x, y, 0.2, 0.2), (
                    r2["shape"]["x"], r2["shape"]["y"], r2["shape"]["width"], r2["shape"]["height"])) for r2 in tables)
                if is_valid:
                    positions.append((x, y))
    nap_positions_ids = []
    for position in positions:
        nap = {
            "id": starting_id,
            "shape": {
                "x": position[0],
                "y": position[1],
                "width": 0.2,
                "height": 0.2,
                "type": "RECTANGLE"
            },
            "visible": False,
            "absorber": {
                "enabled": False,
                "deletionDistance": 0.1
            },
            "waiter": {
                "enabled": True,
                "distribution": {
                    "type": "org.vadere.state.attributes.distributions.AttributesConstantDistribution",
                    "updateFrequency": 7200.0
                },
                "individualWaiting": True
            },
            "leavingSpeed": -1.0,
            "parallelEvents": 0
        }
        nap_positions_ids.append(nap["id"])
        new_nap_positions.append(nap)
        starting_id += 1

    return new_nap_positions, starting_id, nap_positions_ids


def calculate_coordinates_for_nap_positions(filename, output, grid_ids_array, starting_id=6000):
    with open(filename) as f:
        d = json.load(f)

    targets = d["targets"]
    class_rooms = [DailyConstants.CLASSROOM_3, DailyConstants.CLASSROOM_4, DailyConstants.CLASSROOM_5,
                   DailyConstants.CLASSROOM_6]
    new_targets = [x for x in targets if x["id"] < 6000]
    tables = [t for t in d["obstacles"]]

    for idx, grid_ids in enumerate(grid_ids_array):
        t_temp = [t for t in tables if t["id"] in TABLE_DICT[class_rooms[idx]]]
        positions, starting_id, ids = get_napping_positions(targets, t_temp, grid_ids, starting_id)
        print(ids)
        new_targets.extend(positions)

    d["targets"] = new_targets

    with open(output, "w") as f:
        json.dump(d, f, indent=4)


def toggle_visibility_for_class_room(filename, output, grid_ids: List, visible=False):
    with open(filename) as f:
        d = json.load(f)

    targets = d["targets"]
    class_room_targets = [x for xs in grid_ids for x in xs]
    for t in targets:
        if t["id"] in class_room_targets:
            t["visible"] = visible

    with open(output, "w") as f:
        json.dump(d, f, indent=4)


def give_group_membership(filename, output, agent_groups):
    idx = 7000

    with open(filename) as f:
        d = json.load(f)

    peds = d["dynamicElements"]

    for agents in agent_groups:
        for agent in agents:
            for index, ped in enumerate(peds):
                if ped["attributes"]["id"] == agent:
                    peds[index]["groupIds"] = [idx]
        idx += 1

    with open(output, "w") as f:
        json.dump(d, f, indent=4)


def euclidean_distance(pos1, pos2):
    return math.dist(pos1, pos2)


if __name__ == "__main__":
    pass