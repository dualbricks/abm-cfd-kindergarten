import os
import pickle
import time
from pathlib import Path

from ProjectConstants import VADERE_PATH, OUTPUT_PATH


from flowcontrol.crownetcontrol.setup.entrypoints import get_controller_from_args
from flowcontrol.crownetcontrol.state.state_listener import VadereDefaultStateListener
from flowcontrol.crownetcontrol.traci import constants_vadere as tc

from base import Daily

BASE_DIR = Path(__file__).resolve().parent
def run_experiment(start=0, end=30):
    for i in range(start, end):
        settings = [
            "--port",
            "9999",
            "--host-name",
            "localhost",
            "--scenario-file",
            f"{VADERE_PATH}/scenarios/daily_with_table.scenario",
            "--client-mode",
            "--controller-type",
            "Daily",
            "--output-dir",
            f"{OUTPUT_PATH}/{i}",
            "-vr",
            VADERE_PATH,
            "-j",
            "vadere-server.jar"
        ]
        sub = VadereDefaultStateListener.with_vars(
            "persons",
            {"pos": tc.VAR_POSITION, "speed": tc.VAR_SPEED, "angle": tc.VAR_ANGLE},
            init_sub=True,
        )
        s = Daily()
        start_end = time.time()
        controller = get_controller_from_args(working_dir=os.getcwd(), args=settings, controller=s)
        controller.register_state_listener("default", sub, set_default=True)
        controller.reset()
        controller.start_controller()
        end_time = time.time() - start_end
        print(
            "----------------------------------------------------------------------------------------------------------------------------")
        print("Duration of simulation is", end_time)
        print(
            "----------------------------------------------------------------------------------------------------------------------------")


if __name__ == "__main__":
    run_experiment(164, 165)
