import cProfile
import gc
import json
import multiprocessing
import os
import pickle
import time
from typing import List, Literal, Optional, Set

import numpy as np
import pandas as pd
from matplotlib.ticker import ScalarFormatter
from shapely import Polygon, Point
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
import polars as pl
from ValidMesh import ValidMesh

def compute_ps_eudist(gridpoints_xy, source_xy, model, eudist_batch, scale=False):
    """

    :param scale:
    :param eudist_batch:
    :param gridpoints_xy:
    :param source_xy:
    :return:
    """
    # calculate ps and eudist for each gridpoint
    #
    # inputs:
    # gridpoints_xy: ndarray(x,y) shape (n_total_gridpoints, 2)
    # source_xy: ndarray(x,y) shape (2,)
    #
    # outputs:
    # ndarray(ps,eu_dist) shape (n_total_gridpoints,2)

    # create ndarray with the same source_xy value
    source_batch = np.full(gridpoints_xy.shape, source_xy)

    # concatenate along last axis (axis=1)
    #
    # inputs:
    # source_batch & point_batch: (261,2)
    #
    # outputs:
    # src_pt_batch: (261,4)
    src_pt_batch = np.c_[source_batch, gridpoints_xy]
    #
    # inputs:
    # src_pt_batch: (261,4)
    # eudist_batch: (261,1)
    #
    # outputs:
    # X_batch: (261,5)
    X_batch = np.c_[src_pt_batch, eudist_batch]

    # predict ps along last axis (axis=1)
    #
    # outputs:
    # y_pred_batch: (261,)
    y_pred_batch_log = model.predict(X_batch)
    if scale:
        y_pred_batch_log = y_pred_batch_log * 10
    # convert log value to normal number
    y_pred_batch = 10 ** y_pred_batch_log

    # (261,2)
    return np.c_[y_pred_batch, eudist_batch]


class PassiveScalarModel(object):

    def __init__(self, n_coors=2, length_grid=0.1, n_receivers=29, n_agents=30, sim_duration_seconds=900,
                 translation_vector=(-11.65, -4.5),
                 target_locations="../target_center2.json"):
        self.translation_vector = translation_vector
        self.sim_duration_seconds = sim_duration_seconds
        self.n_agents = n_agents
        self.n_coors = n_coors
        self.length_grid = length_grid
        self.n_receivers = n_agents - 1
        self.n_gridpoints_per_agent = (self.n_coors * 2 + 1) ** 2
        self.n_total_gridpoints = self.n_gridpoints_per_agent * self.n_receivers
        self.target_locations = target_locations
        self.meshes = ValidMesh()
        self.meshes.set_polygon()

    def align_grid_points(self, receiver_xy):

        n_coord = (self.n_coors * 2 + 1)
        x_min = 0.5 * self.length_grid
        y_min = -self.n_coors * self.length_grid
        points_xy = []
        for i in range(n_coord):
            for j in range(n_coord):
                point_x = x_min + self.length_grid * i
                point_y = y_min + self.length_grid * j
                points_xy.append([round(point_x, 4), round(point_y, 4)])

        # get direction of agent
        heading_x = np.array(receiver_xy[:, 2])
        heading_y = np.array(receiver_xy[:, 3])
        theta = np.arctan2(heading_y, heading_x)

        # Rotational Matrix
        c, s = np.cos(theta), np.sin(theta)
        R = np.array([[c, -s], [s, c]])

        rotated_grid_xy = np.dot(np.array(points_xy), R.T)
        rotated_grid_xy += np.array(receiver_xy[:, :2])
        output_arr = np.transpose(rotated_grid_xy, (1, 0, 2)).reshape((self.n_total_gridpoints, 2))
        return output_arr

    def process_data_vector(self, data, save=None):
        target_dict = {}
        with open(self.target_locations) as f:
            target_dict = json.load(f)

        # add new columns for directional vectors

        df = pd.DataFrame(data)

        # Sort by pedestrianId and timeStep
        # df = df.sort_values(by=["timeStep", "pedestrianId"])

        target_ids = df["targetId-PID8"].astype(int)
        valid_targets = target_ids != -1
        invalid_targets = target_ids == -1
        Vx = np.zeros(len(df))
        Vy = np.zeros(len(df))

        # Extract positions where targetId is valid
        valid_indices = np.where(valid_targets)[0]
        target_positions = np.array([target_dict.get(str(tid), (0, 1)) for tid in target_ids[valid_targets]])
        # Vx_starting = [x[0] for x in list(AGENT_HEADING_STARTING.values())]
        # Vy_starting = [x[1] for x in list(AGENT_HEADING_STARTING.values())]
        Vx_starting = [0] * self.n_agents
        Vy_starting = [0] * self.n_agents
        # Compute direction vectors for valid target IDs
        Vx[valid_indices] = target_positions[:, 0] - df.loc[valid_targets, "x_offset-PID7"].values
        Vy[valid_indices] = target_positions[:, 1] - df.loc[valid_targets, "y_offset-PID7"].values
        Vx[invalid_targets] = Vx_starting * 2
        Vy[invalid_targets] = Vy_starting * 2
        df["Vx"], df["Vy"] = Vx, Vy
        # translation to match ps model
        df.drop(["targetId-PID8"], inplace=True, axis=1)

        # Room boundaries (x_min, x_max, y_min, y_max)
        staff_room = (8.8, 11.75, 0, 4.0)
        principal_room = (11.9, 14.95, 0, 4.0)
        kitchen_1 = (19.15, 20.75, 8.25, 9.85)
        kitchen_2 = (20.75, 23.65, 8.25, 10.6)
        toilet = (7.3, 11.5, 9.05, 12.05)
        x = df["x_offset-PID7"].values
        y = df["y_offset-PID7"].values
        # Boolean masks for each room
        in_staff = (x > staff_room[0]) & (x < staff_room[1]) & (y > staff_room[2]) & (y < staff_room[3])
        in_principal = (x > principal_room[0]) & (x < principal_room[1]) & (y > principal_room[2]) & (
                y < principal_room[3])
        in_kitchen_1 = (x > kitchen_1[0]) & (x < kitchen_1[1]) & (y > kitchen_1[2]) & (y < kitchen_1[3])
        in_kitchen_2 = (x > kitchen_2[0]) & (x < kitchen_2[1]) & (y > kitchen_2[2]) & (y < kitchen_2[3])
        in_toilet = (x > toilet[0]) & (x < toilet[1]) & (y > toilet[2]) & (y < toilet[3])
        # Start with "BigRoom" as default
        room_labels = np.full(len(df), 0, dtype=int)

        # Assign room names using masks
        room_labels[in_staff] = 1
        room_labels[in_principal] = 2
        room_labels[in_kitchen_1] = 3
        room_labels[in_kitchen_2] = 3
        room_labels[in_toilet] = 4
        df["room"] = room_labels

        if save:
            df.to_csv(save, index=False, sep=";")
        # convert into numpy
        data = df.to_numpy()
        # translation to match ps model
        data[:, 2] = data[:, 2] + self.translation_vector[0]
        data[:, 3] = data[:, 3] + self.translation_vector[1]
        np.set_printoptions(suppress=True)
        del df
        return data

    def compute_ps_pl(self, filename, model, outputfile1, outputfile2, save=True, check_dim=False, new_model=None,
                      student_model=None, batch_size=10000, output_format: Literal["parquet", "csv", "both"] = "csv",
                      raw=None, source_save=None):
        # Temporary buffers to accumulate batch data
        batch_data = {
            'frame': [],
            'id': [],
            'room': [],
            'pos_x': [],
            'pos_y': [],
            'eu_dist': [],
            'dist': [],
            'ps_raw': [],
            'valid': [],
            'ps_at_point': [],
            'dist_at_point': []
        }
        temp_files = []
        # Output parquet intermediate file (streamed append)
        intermediate_parquet = outputfile1.replace('.csv', '_intermediate.parquet')

        if os.path.exists(intermediate_parquet):
            os.remove(intermediate_parquet)

        def flush_batch(batch_idx):
            if not batch_data['frame']:
                return
            df_batch = pl.DataFrame(batch_data)
            temp_file = intermediate_parquet.replace(".parquet", f"_batch{batch_idx}.parquet")
            df_batch.write_parquet(temp_file)
            temp_files.append(temp_file)
            for key in batch_data:
                batch_data[key].clear()

            del df_batch

        batch_count = 0
        b_frames = 0
        data = pd.read_csv(filename, delim_whitespace=True)
        n_frames = data["timeStep"].unique()

        # frame, id, x,y,x_heading, y_heading, room
        processed_data = self.process_data_vector(data)

        # free original dataframe
        del data
        # 0: prepare position data
        # read the position of emitter
        time_now = time.time()
        source_data = processed_data[:, 1].astype(int) == 2
        source_data = processed_data[source_data]
        source_df = pl.DataFrame(source_data,
                                 schema=['frame', 'id', 'pos_x', 'pos_y', 'x_heading', 'y_heading', 'room'])
        if source_save:
            if output_format in ["parquet", "both"]:
                source_df.write_parquet(source_save.replace(".csv", ".parquet"))
            if output_format in ["csv", "both"]:
                source_df.write_csv(source_save, separator=';')
        del source_df
        for f in n_frames:

            # Extract all rows for this timestep
            frame_mask = processed_data[:, 0] == f
            frame_data = processed_data[frame_mask]

            # Find source agent (agentId == 2)
            source_mask = frame_data[:, 1].astype(int) == 2
            if not np.any(source_mask):
                continue

            source_row = frame_data[source_mask][0]
            source_xy = source_row[2:4].astype(float)

            source_room = source_row[-1]

            # Get receivers (all agents except source)
            receivers_mask = ~source_mask
            receivers_data = frame_data[receivers_mask]
            receivers_xy = receivers_data[:, 2:6].astype(float)
            receivers_room = receivers_data[:, -1]
            n_receivers = len(receivers_data)
            self.n_total_gridpoints = self.n_gridpoints_per_agent * n_receivers
            gridpoints_xy = self.align_grid_points(receivers_xy)
            temp_ps_eudist = np.zeros((self.n_total_gridpoints, 2))  # [PS_value, eu_dist]
            source_batch = np.full((self.n_total_gridpoints, 2), source_xy)
            src_pt_batch = np.c_[source_batch, gridpoints_xy]
            temp_ps_eudist[:, 1] = np.linalg.norm(src_pt_batch[:, :2] - src_pt_batch[:, 2:], axis=1)
            valid_gridpoints = np.ones(self.n_total_gridpoints, dtype=bool)

            # Expand receiver_room info to match grid points
            expanded_receivers_room = np.repeat(receivers_room, self.n_gridpoints_per_agent)
            expanded_receiver_ids = np.repeat(receivers_data[:, 1], self.n_gridpoints_per_agent)
            # Case 0: BigRoom (e.g. source_room == 0 or 4)
            if source_room == 0 or source_room == 4:
                idx_0 = expanded_receivers_room == 0
                idx_4 = expanded_receivers_room == 4

                mesh_0 = self.meshes.valid_meshes[0]
                mesh_4 = self.meshes.valid_meshes[4]

                if mesh_0 is not None and np.any(idx_0):
                    valid_gridpoints[idx_0] = [self.meshes.get_valid_mesh((x, y), mesh_0) for x, y in
                                               gridpoints_xy[idx_0]]

                if mesh_4 is not None and np.any(idx_4):
                    valid_gridpoints[idx_4] = [
                        self.meshes.get_valid_mesh((x, y), mesh_4) for x, y in gridpoints_xy[idx_4]
                    ]

                valid_mask = valid_gridpoints & (idx_0 | idx_4)

                if np.any(valid_mask):
                    receiver_ids_mask = np.isin(expanded_receiver_ids,
                                                [82, 176, 177, 178, 179, 200, 201, 251, 250, 252, 253, 254])
                    staff_mask = valid_mask & receiver_ids_mask
                    student_mask = valid_mask & ~receiver_ids_mask
                    if student_model:
                        if np.any(staff_mask):
                            filtered_xy = gridpoints_xy[staff_mask]
                            filtered_eudist = temp_ps_eudist[staff_mask, 1]
                            out = compute_ps_eudist(filtered_xy, source_xy, model, filtered_eudist)
                            temp_ps_eudist[staff_mask] = out

                        if np.any(student_mask):
                            filtered_xy = gridpoints_xy[student_mask]
                            filtered_eudist = temp_ps_eudist[student_mask, 1]
                            out = compute_ps_eudist(filtered_xy, source_xy, student_model, filtered_eudist)
                            temp_ps_eudist[student_mask] = out
                    else:
                        filtered_xy = gridpoints_xy[valid_mask]
                        filtered_eudist = temp_ps_eudist[valid_mask, 1]
                        out = compute_ps_eudist(filtered_xy, source_xy, model, filtered_eudist)
                        temp_ps_eudist[valid_mask] = out

            # Case 3: Kitchen (use new model)
            elif source_room == 3:
                idx_3 = expanded_receivers_room == 3

                mesh_3 = self.meshes.valid_meshes[3]

                if mesh_3 is not None and np.any(idx_3):
                    valid_gridpoints[idx_3] = [self.meshes.get_valid_mesh((x, y), mesh_3) for x, y in
                                               gridpoints_xy[idx_3]]
                valid_mask = valid_gridpoints & idx_3
                if np.any(valid_mask):
                    filtered_xy = gridpoints_xy[valid_mask]
                    filtered_eudist = temp_ps_eudist[valid_mask, 1]
                    out = compute_ps_eudist(filtered_xy, source_xy, new_model,
                                            filtered_eudist, True)
                    temp_ps_eudist[valid_mask] = out

            # Case 2: principal room— static value
            elif source_room == 2:
                idx_2 = expanded_receivers_room == 2

                mesh_2 = self.meshes.valid_meshes[2]

                if mesh_2 is not None and np.any(idx_2):
                    valid_gridpoints[idx_2] = [self.meshes.get_valid_mesh((x, y), mesh_2) for x, y in
                                               gridpoints_xy[idx_2]]
                temp_ps_eudist[:, 0] = np.where(idx_2, 0.000165, 0.0)

            # Case 1: staff room — static value
            elif source_room == 1:
                idx_1 = expanded_receivers_room == 1

                mesh_1 = self.meshes.valid_meshes[1]

                if mesh_1 is not None and np.any(idx_1):
                    valid_gridpoints[idx_1] = [self.meshes.get_valid_mesh((x, y), mesh_1) for x, y in
                                               gridpoints_xy[idx_1]]
                temp_ps_eudist[:, 0] = np.where(idx_1, 0.000162, 0.0)
            # Broadcast frame index
            # reset n_receivers
            temp_frame = np.full(self.n_total_gridpoints, f)

            # Repeat each receiver’s ID, x, y for each gridpoint
            receiver_ids = receivers_data[:, 1].astype(int)  # shape: (n_receivers,)
            receiver_xs = receivers_xy[:, 0]  # shape: (n_receivers,)
            receiver_ys = receivers_xy[:, 1]

            temp_id = np.repeat(receiver_ids, self.n_gridpoints_per_agent)
            temp_x = np.repeat(receiver_xs, self.n_gridpoints_per_agent)
            temp_y = np.repeat(receiver_ys, self.n_gridpoints_per_agent)
            source_xy_batch = np.full((len(receivers_xy), 2), source_xy)
            receiver_dist = np.linalg.norm(receivers_xy[:, :2] - source_xy_batch, axis=1)
            temp_dist = np.repeat(receiver_dist, self.n_gridpoints_per_agent)
            # change the dist where they are not in the same room
            temp_dist[expanded_receivers_room != source_room] = np.inf

            # Distance from source to each receiver (single point)

            receiver_ps = np.zeros(len(receivers_xy))

            # Compute ps_at_point for each receiver based on source_room logic
            if source_room == 0 or source_room == 4:

                idx_0 = receivers_room == 0
                idx_4 = receivers_room == 4

                valid_mask = idx_0 | idx_4
                if np.any(valid_mask):
                    receiver_ids_mask = np.isin(receiver_ids,
                                                [82, 176, 177, 178, 179, 200, 201, 251, 250, 252, 253, 254])
                    staff_mask = valid_mask & receiver_ids_mask
                    student_mask = valid_mask & ~receiver_ids_mask
                    if student_model:
                        if np.any(staff_mask):
                            receiver_ps[staff_mask] = compute_ps_eudist(
                                receivers_xy[staff_mask, :2], source_xy, model, receiver_dist[staff_mask]
                            )[:, 0]
                        if np.any(student_mask):
                            receiver_ps[student_mask] = compute_ps_eudist(
                                receivers_xy[student_mask, :2], source_xy, student_model,
                                receiver_dist[student_mask]
                            )[:, 0]
                    else:
                        receiver_ps[valid_mask] = compute_ps_eudist(receivers_xy[valid_mask, :2], source_xy, model,
                                                                    receiver_dist[valid_mask])[:, 0]

            elif source_room == 3:
                mask = receivers_room == 3
                receiver_ps[mask] = compute_ps_eudist(receivers_xy[mask, :2], source_xy, new_model, receiver_dist[mask],
                                                      True)[:,
                                    0]

            elif source_room == 2:
                receiver_ps = np.where(receivers_room == 2, 0.000165, 0.0)

            elif source_room == 1:
                receiver_ps = np.where(receivers_room == 1, 0.000162, 0.0)

            # Repeat ps_at_point for each grid point of the receiver
            ps_at_point_expanded = np.repeat(receiver_ps, self.n_gridpoints_per_agent)
            receiver_dist_expanded = np.repeat(receiver_dist, self.n_gridpoints_per_agent)
            # Flatten PS and EuDist arrays
            batch_data['frame'].extend(temp_frame)
            batch_data['id'].extend(temp_id)
            batch_data['room'].extend(expanded_receivers_room)
            batch_data['pos_x'].extend(temp_x)
            batch_data['pos_y'].extend(temp_y)
            batch_data['eu_dist'].extend(temp_ps_eudist[:, 1])
            batch_data['dist'].extend(temp_dist)
            batch_data['ps_raw'].extend(temp_ps_eudist[:, 0])
            batch_data['valid'].extend(valid_gridpoints)
            batch_data['ps_at_point'].extend(ps_at_point_expanded)
            batch_data['dist_at_point'].extend(receiver_dist_expanded)
            # Periodically flush batch to parquet to save memory

            if b_frames >= batch_size:
                flush_batch(batch_count)
                b_frames = 0
                batch_count += 1
                print(f, "/", len(n_frames), "done, ", "time: ", time.time() - time_now)
            b_frames += 1
        flush_batch(batch_count)
        results_temp = pl.read_parquet(temp_files)
        if raw:
            if output_format in ["parquet", "both"]:
                results_temp.write_parquet(raw.replace(".csv", ".parquet"))
            if output_format in ["csv", "both"]:
                results_temp.write_csv(raw, separator=';')
        # Compute mean per (frame, id)
        group_means = (
            results_temp
            .filter(pl.col("valid") == True)
            .group_by(["frame", "id"])
            .agg(pl.col("ps_raw").mean().alias("ps_estimated"))
        )

        # Filter unique (frame, id) and join with means
        results_frame = (
            results_temp.unique(subset=["frame", "id"])
            .join(group_means, on=["frame", "id"], how="left")
        )
        results_frame = results_frame.drop(["ps_raw", "eu_dist", "valid"])

        del results_temp, group_means

        # Agent-level summary
        results_agent = (
            results_frame
            .group_by("id")
            .agg(pl.col("ps_estimated").sum())
        )
        if save:
            if output_format in ["parquet", "both"]:
                results_frame.write_parquet(outputfile1.replace(".csv", ".parquet"))
            if output_format in ["csv", "both"]:
                results_frame.write_csv(outputfile1, separator=';')
            results_agent.write_csv(outputfile2, separator=';')

        for f in temp_files:
            os.remove(f)
        gc.collect()
        return results_frame, results_agent


if __name__ == '__main__':
    pass
