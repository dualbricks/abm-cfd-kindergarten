import json
from Controller.Agent import Principal
from Controller.ClassManager import ClassManager
from Controller.DailyConstants import PRINCIPAL_ROOM, CLASSROOM_6
from Controller.SeatManager import TableSeatManager, PrincipalRoomManager

from flowcontrol.crownetcontrol.setup.entrypoints import get_controller_from_args
from flowcontrol.crownetcontrol.state.state_listener import VadereDefaultStateListener
from flowcontrol.crownetcontrol.controller import Controller
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.strategy.timestepping.timestepping import FixedTimeStepper

from ProjectConstants import PROJECT_PATH
class Base(Controller):
    """
    Base class for PCF simulation
    """

    def __init__(self):
        super().__init__(time_stepper=FixedTimeStepper(time_step_size=0.4, start_time=0.4))


    def handle_sim_step(self, sim_time, sim_state):
        """
        Main update loop TO BE CONVERTED TO A CONTROLLER
        :param sim_time:
        :param sim_state:
        :return:
        """
    pass


class Daily(Base, Controller):
    def __init__(self):
        self.classManager = ClassManager()
        self.principal = Principal(2, CLASSROOM_6, [])
        self.principalRoomManager = PrincipalRoomManager(PRINCIPAL_ROOM)
        super().__init__()
        with open(f"{PROJECT_PATH}/target_center_daily_with_table.json") as f:
            self.target_dict = json.load(f).keys()

    def reset(self):
        self.classManager.reset()
        self.principal.reset()
        self.principalRoomManager.reset()

    def handle_sim_step(self, sim_time, sim_state):
        aa = list(self.con_manager.domains.v_person.get_id_list())
        self.update_position(aa)
        self.principal.update_interested_class(self.classManager)
        self.principal.update_agent_movement(None, sim_time)
        for agent in self.classManager.agents.values():
            self.toiletManager.toilet_event_handling(agent, sim_time)

        self.toiletManager.toilet_event_handling(self.principal, sim_time)
        self.classManager.update_free_staff(sim_time)
        self.classManager.update_class_movement(sim_time)
        for ped_id in aa:
            if ped_id == "2":
                self.con_manager.domains.v_person.set_target_list(str(ped_id), [str(self.principal.current_target)])
            else:

                self.con_manager.domains.v_person.set_target_list(str(ped_id), [
                    str(self.classManager.agents[int(ped_id)].current_target)])

        self.time_stepper.forward_time()

    def update_position(self, aa):

        pos = list(self.con_manager.domains.v_person.get_position2_dlist())

        for ped in pos:
            if str(ped[0]) == "2":
                self.principal.update_position(ped[1:3])
            else:
                self.classManager.agents[ped[0]].update_position(ped[1:3])
