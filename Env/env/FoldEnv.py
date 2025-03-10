import numpy as np
from isaacsim import SimulationApp
import torch

simulation_app = SimulationApp({"headless": False,"muti_gpu":False})
import numpy as np
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.franka import Franka
from omni.isaac.core.utils.prims import is_prim_path_valid
from omni.isaac.core.utils.string import find_unique_string_name
from omni.isaac.core import World
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import add_reference_to_stage, get_stage_units
from omni.isaac.franka.controllers.pick_place_controller import PickPlaceController
from omni.isaac.franka.controllers.rmpflow_controller import RMPFlowController
from omni.isaac.franka import KinematicsSolver
from omni.isaac.core.utils.types import ArticulationAction
import torch
import sys
sys.path.append("/home/user/GarmentLab/")
from Env.Utils.transforms import euler_angles_to_quat
from Env.Utils.transforms import quat_diff_rad
from Env.env.BaseEnv import BaseEnv
from Env.Garment.Garment import Garment
from Env.Robot.Franka.MyFranka import MyFranka
from Env.env.Control import Control
from Env.Config.GarmentConfig import GarmentConfig
from Env.Config.FrankaConfig import FrankaConfig
from Env.Config.DeformableConfig import DeformableConfig
from Env.Camera.Recording_Camera import Recording_Camera
import open3d as o3d

class FoldEnv(BaseEnv):
    def __init__(self,garment_config:GarmentConfig=None,franka_config:FrankaConfig=None,Deformable_Config:DeformableConfig=None):
        BaseEnv.__init__(self,garment=True)
        if garment_config is None:
            self.garment_config=[GarmentConfig(ori=np.array([0,0,0]))]
        else:
            self.garment_config=garment_config
        self.garment:list[Garment]=[]
        for garment_config in self.garment_config:
            self.garment.append(Garment(self.world,garment_config))
        if franka_config is None:
            self.franka_config=FrankaConfig()
        else:
            self.franka_config=franka_config
        self.robots=self.import_franka(self.franka_config)
        self.control=Control(self.world,self.robots,[self.garment[0]])
        self.camera = Recording_Camera(
            camera_position=np.array([0.0, 0, 6.75]),
            camera_orientation=np.array([0, 90.0, 90]),
            prim_path="/World/recording_camera",
        )

    def reset(self):
        super().reset()
        self.camera.initialize(
            depth_enable=True,
            pc_enable=True,
            segment_prim_path_list=[
                "/World/Garment/garment",
            ]
        )






if __name__=="__main__":
    env=FoldEnv()
    env.reset()
    # env.control.grasp([np.array([0.5,-0.1,0.04])],[None],[True])
    # env.control.move([np.array([0.5,-0.1,0.5])],[None],[True])
    # env.control.ungrasp([False])
    # env.control.grasp([np.array([0.5,-0.1,0.04])],[None],[True])
    # env.control.move([np.array([0.5,-0.1,0.5])],[None],[True])
    # env.control.ungrasp([False])
    step=0
    while 1:
        env.step()
        step+=1
        if step%1000==0:
            points=env.garment[0].get_vertices_positions().reshape(-1,3)
            pcd=o3d.geometry.PointCloud()
            pcd.points=o3d.utility.Vector3dVector(points)
            o3d.visualization.draw_geometries([pcd])
