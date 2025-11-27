from aiofiles import os

from PassiveScalarModel import PassiveScalarModel
import pickle

from ProjectConstants import OUTPUT_PATH, PROJECT_PATH

ANALYSIS_PATH = os.path.join(PROJECT_PATH, "results")


def analyse_specific_pl(start1=0, end1=100):
    t = PassiveScalarModel(n_agents=85, target_locations=f"{PROJECT_PATH}/target_center_daily_with_table.json")
    filename = f'{PROJECT_PATH}/ps_model/data_model_emitter_standing_receiver_standing.p'
    filename1 = f'{PROJECT_PATH}/ps_model/kitchen_emitter_standing_receiver_standing.p'
    filename2 = f'{PROJECT_PATH}/ps_model/data_model_emitter_standing_receiver_sitting.p'
    xgb_emit_stand_receiver_stand = pickle.load(open(filename, 'rb'))
    xgb_emit_stand_receiver_sit = pickle.load(open(filename2, 'rb'))
    kitchen = pickle.load(open(filename1, 'rb'))

    for i in range(start1, end1):
        output = f"{OUTPUT_PATH}/{i}/_sim/vadere.d/OffsetPosition.txt"
        output1_path = f"{ANALYSIS_PATH}/ps_results_daily/ps_individual/daily_{i}_pl.csv"
        output2_path = f"{ANALYSIS_PATH}/ps_results_daily/agent_ps_individual/daily_{i}_pl.csv"
        output3_path = f"{ANALYSIS_PATH}/ps_results_daily/ps_individual_raw/daily_{i}_pl_raw.csv"
        output4_path = f"{ANALYSIS_PATH}/ps_results_daily/source_data/daily_{i}_pl.csv"
        t.compute_ps_pl(output, xgb_emit_stand_receiver_stand, output1_path, output2_path, save=True, new_model=kitchen,
                        output_format="parquet", raw=output3_path, source_save=output4_path)
        output1_path = f"{ANALYSIS_PATH}/ps_results_daily/ps_individual/daily_{i}_pl_student.csv"
        output2_path = f"{ANALYSIS_PATH}/ps_results_daily/agent_ps_individual/daily_{i}_pl_student.csv"
        output3_path = f"{ANALYSIS_PATH}/ps_results_daily/ps_individual_raw/daily_{i}_pl_student_raw.csv"
        output4_path = f"{ANALYSIS_PATH}/ps_results_daily/source_data/daily_{i}_pl_student.csv"
        t.compute_ps_pl(output, xgb_emit_stand_receiver_stand, output1_path, output2_path, save=True, new_model=kitchen,
                        student_model=xgb_emit_stand_receiver_sit, output_format="parquet", raw=output3_path,
                        source_save=output4_path)


if __name__ == "__main__":
    analyse_specific_pl(105, 205)
