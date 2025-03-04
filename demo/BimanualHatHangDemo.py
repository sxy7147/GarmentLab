import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print('BASE_DIR: ', BASE_DIR)
sys.path.append('.')
sys.path.append(os.path.join(BASE_DIR, '../Env'))
print('sys.path: ', sys.path)
# sys.path.append("/home/user/GarmentLab")
from Env.env.BimanualDeformableEnv import DeformableEnv

from Env.Config.GarmentConfig import GarmentConfig
from Env.Config.FrankaConfig import FrankaConfig
from Env.Config.DeformableConfig import DeformableConfig
import numpy as np


''' 鸭舌帽: hat030, 44,45,46 '''


if __name__=="__main__":
    
    id = 44
    # id = 7
    folder_name = f"HA_hat{str(id).zfill(3)}"
    file_name = f"HA_hat{str(id).zfill(3)}_obj.usd"
    # deformbaleConfig = DeformableConfig(usd_path=os.path.join('./Assets/Garment/Hat', folder_name, file_name), pos=np.array([0.6,-1.3,0.3]), ori=np.array([0,0,0]))
    deformbaleConfig = DeformableConfig(usd_path=os.path.join('./Assets/Garment/Hat', folder_name, file_name), pos=np.array([0.6,1.3,0.32]), ori=np.array([np.pi,0,0]))
    # deformbaleConfig = DeformableConfig(usd_path=os.path.join('./Assets/Garment/Hat', folder_name, file_name), pos=np.array([0.59,1.3,0.2]), ori=np.array([-np.pi/2+0.01,0,0]))
    env=DeformableEnv(deformbaleConfig=deformbaleConfig)
    
    # env=DeformableEnv()
    env.reset()
    
    env.step()
    # original_points, _ = env.recording_camera.get_point_cloud_data()
    # print('initial_pc_points: ', original_points.shape)
    
    save_rgb_dir = '/media/sim/WD_BLACK/sy/PreGrasp/GarmentLab/data/tmp'
    env.recording_camera.get_rgb_graph(
        save_path=os.path.join(save_rgb_dir, f"rgb_{id}_0.png",),
        save_or_not=True
    )
    
    env.robots[0].movel(np.array([0.70, -0.13, 0.5]))
    env.robots[1].movel(np.array([0.45, 0.0, 0.7]))
    env.recording_camera.get_rgb_graph(
        save_path=os.path.join(save_rgb_dir, f"rgb_{id}_1.png",),
        save_or_not=True
    )
    env.def_control.bimanual_grasp([np.array([0.70, -0.13, 0.078]), np.array([0.45, 0.0, 0.7])],[None, None],[True, False])
    env.recording_camera.get_rgb_graph(
        save_path=os.path.join(save_rgb_dir, f"rgb_{id}_2.png",),
        save_or_not=True
    )
    env.def_control.move([np.array([0.70, -0.13, 0.5]), None],[None, None],[True, False])
    env.recording_camera.get_rgb_graph(
        save_path=os.path.join(save_rgb_dir, f"rgb_{id}_3.png",),
        save_or_not=True
    )
    env.def_control.move([np.array([0.65, 0., 0.5]), None],[np.array([np.pi, 0, 0]), None],[True, False])
    # env.def_control.bimanual_grasp([None, np.array([0.63, -0.22, 0.03])],[None, None],[False, True])
    # env.def_control.move([None, np.array([0.65, 0., 0.5])],[None, None],[False, True])
    # env.def_control.move([None, np.array([0.65, 0., 0.5])],[None, np.array([np.pi, 0, 0])],[False, True])
    
    # env.robots[0].movel(np.array([0.65, -0.20, 0.5]))
    # env.def_control.bimanual_grasp([np.array([0.63, -0.22, 0.03]), None],[None, None],[True, False])
    # env.def_control.move([np.array([0.65, 0., 0.5]), None],[None, None],[True, False])
    # env.def_control.move([np.array([0.65, 0., 0.5]), None],[np.array([np.pi, 0, 0]), None],[True, False])
    
    
    # object id-7
    # env.robots[0].movel(np.array([0.65, 0.1, 0.7]))
    # env.robots[1].movel(np.array([0.85, 0.2, 0.7]))
    # env.robots[0].movel(np.array([0.65, 0.1, 0.5]))
    # env.robots[1].movel(np.array([0.85, 0.2, 0.5]))
    # env.def_control.bimanual_grasp([np.array([0.65535, -0.03994, 0.09283]), np.array([0.65535, 0.1, 0.09283])],[None, None],[True, True])
    # env.def_control.move([np.array([0.5, -0.0, 0.72]), np.array([0.5, 0.12, 0.72])],[None, None],[True, True])
    # env.def_control.move([np.array([0.525, 0.525, 0.7]), np.array([0.575, 0.575, 0.7])],[None, None],[True, True])
    # env.def_control.ungrasp([False, False])
    
    
    # env.robots[0].movel(np.array([0.65,0,0.7]))
    # env.robots[1].movel(np.array([0.8,0,0.7]))
    # env.robots[0].movel(np.array([0.65,0,0.5]))
    # env.def_control.grasp([np.array([0.65535,-0.03994,0.09283]), None],[None, None],[True, False])
    # env.def_control.move([np.array([0.5,-0.0,0.72]), None],[None, None],[True, False])
    # env.def_control.move([None, np.array([0.525,0.1,0.72])],[None, None],[False, True])
    # env.def_control.grasp([np.array([0.65535,-0.03994,0.09283]), None],[None, None],[True, False])
    
    # env.def_control.move([np.array([0.525,0.525,0.67]), np.array([0.525,0.625,0.67])],[None,None],[True,True])
    # env.def_control.ungrasp([False, False])
    
    for i in range(50):
        env.world.step()
