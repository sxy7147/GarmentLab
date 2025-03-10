import os
import sys
sys.path.append(os.getcwd())
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# print('BASE_DIR: ', BASE_DIR)
# sys.path.append('.')
# sys.path.append(os.path.join(BASE_DIR, '../Env'))
# print('sys.path: ', sys.path)
import torch
import numpy as np

from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": True})

# import open3d as o3d
import random
import threading
from termcolor import cprint
import omni.replicator.core as rep
import omni.isaac.core.utils.prims as prims_utils
from omni.isaac.core import World
from omni.isaac.core import SimulationContext
from omni.isaac.core.objects import DynamicCuboid, FixedCuboid, VisualCuboid
from omni.isaac.core.utils.prims import is_prim_path_valid
from omni.isaac.core.utils.string import find_unique_string_name
from omni.isaac.core.materials.physics_material import PhysicsMaterial
from omni.isaac.core.utils.stage import add_reference_to_stage, is_stage_loading
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.prims.geometry_prim import GeometryPrim
from omni.isaac.core.prims.rigid_prim import RigidPrim  
from omni.isaac.core.prims.rigid_prim_view import RigidPrimView 
from omni.isaac.core.prims.geometry_prim_view import GeometryPrimView
from omni.isaac.core.materials import OmniGlass
from omni.isaac.sensor import ContactSensor
from omni.physx.scripts import deformableUtils,particleUtils,physicsUtils
from omni.physx import acquire_physx_interface
from pxr import UsdGeom,UsdPhysics,PhysxSchema, Gf
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.prims import XFormPrim, ClothPrim, RigidPrim, GeometryPrim, ParticleSystem

from Env.env.BaseEnv import BaseEnv

from Env.Deformable.Deformable import Deformable

from Env.Garment.Garment import Garment
from Env.Config.GarmentConfig import GarmentConfig


from Env.Camera.Recording_Camera import Recording_Camera

from LearningBaseline.unigarmentmanip.collect.utils.CollisionGroup import CollisionGroup
from LearningBaseline.unigarmentmanip.collect.utils.transforms import Rotation
from LearningBaseline.unigarmentmanip.collect.utils.file_operation import get_unique_filename
from LearningBaseline.unigarmentmanip.collect.utils.utils import get_pcd2mesh_correspondence, get_mesh2pcd_correspondence, get_max_sequence_number
from LearningBaseline.unigarmentmanip.collect.utils.pcd_utils import normalize_pcd_points, unnormalize_pcd_points, get_visible_indices
from LearningBaseline.unigarmentmanip.collect.utils.attachmentblock import AttachmentBlock

import shutil
import open3d as o3d


class LiftGarment_Collect_Deformation(BaseEnv):
    def __init__(self, garment_path, garment_position, garment_orientation):
        # load BaseEnv
        super().__init__()
        
        # store garment path
        self.garment_path = []
        # load Garment Object
        self.garment = Garment(self.world, 
                               garment_config=GarmentConfig(usd_path=garment_path,
                                pos=garment_position,
                                ori=garment_orientation,
                                friction=10.0,
                                contact_offset=0.018,
                                rest_offset=0.015,
                                particle_contact_offset=0.018,
                                fluid_rest_offset=0.015,
                                solid_rest_offset=0.015,), 
                            #    particle_system=ParticleSystem(
                            #     particle_adhesion_scale=0.05,
                            #     particle_friction_scale=0.05,),
                               )
        
        self.garment_path.append(self.garment.garment_prim_path)
              
        # load camera
        self.recording_camera = Recording_Camera(camera_position=np.array([0.0, 0.5, 8]), camera_orientation=np.array([0, 90, -90]))
        
        # initialize world
        self.reset()
        
        # initialize camera, make sure the 'initialization' procedure is behind the 'reset' procedure.
        self.recording_camera.initialize(pc_enable=True, segment_prim_path_list=["/World/Garment/garment"])

        
        cprint("finish creating the world!", color='green')
        
        for i in range(50):
            self.step()
        # cprint(self.bimanual_dex.dexleft.get_joint_positions(), 'cyan')
        cprint("world ready!", color='green')
        
    def record_callback(self, step_size):
        
        joint_pos_L = self.bimanual_dex.dexleft.get_joint_positions()
        
        joint_pos_R = self.bimanual_dex.dexright.get_joint_positions()
        
        action = [*joint_pos_L, *joint_pos_R]
        
        self.saving_data.append({ 
            "action": action,
        })
    
        
    def create_attach_block(self, idx, init_position=np.array([0.0, 0.0, 1.0])):
        '''
        Create attachment block and update the collision group at the same time.
        '''
        # create attach block and finish attach
        print(f"idx: {idx}")
        self.attach = AttachmentBlock(self.world, self.stage, "/World/AttachmentBlock", [self.garment.garment_mesh_prim_path])
        self.attach.create_block(block_name=f"attach_{idx}", block_position=init_position, block_visible=True)
        print("attach finish!")
        # update attach collision group
        # self.collision.update_after_attach()
        for i in range(10):
            simulation_app.update()
        print("Update collision group successfully!")
        
    def set_attach_to_garment(self, attach_position):
        '''
        push attach_block to new grasp point and attach to the garment
        '''
        # set the position of block
        self.attach.set_block_position(attach_position)
        # create attach
        self.attach.attach()
        # render the world
        self.world.step(render=True)
        
    def pick_random_garment_point(self):
        
        points = self.garment.get_vertice_positions()
        center_point = np.mean(points, axis=0)      
        random_point = points[np.random.randint(0, len(points))]
        return random_point
    
    def pick_random_garment_point_with_candidates(self, candidates):
        random_point = candidates[np.random.randint(0, len(candidates))]
        return random_point
    

    def place_random_garment_point(self, pick_point, max_distance_ratio=1, max_pick2place_distance=0.4):
        
        points = self.garment.get_vertice_positions()
        center_point = np.mean(points, axis=0)
        
        # 计算点云的x和y范围，并扩展1/3
        x_range = np.max(points[:, 0]) - np.min(points[:, 0])
        y_range = np.max(points[:, 1]) - np.min(points[:, 1])
        
        x_min = np.min(points[:, 0]) - x_range / 3
        x_max = np.max(points[:, 0]) + x_range / 3
        y_min = np.min(points[:, 1]) - y_range / 3
        y_max = np.max(points[:, 1]) + y_range / 3
        
        offset = np.array(pick_point) - np.array(center_point)
        
        # 判断排除的象限
        exclude_x = offset[0] > 0  # 如果为正，排除右侧象限
        exclude_y = offset[1] > 0  # 如果为正，排除上方象限
        
        # 根据要排除的象限定义可以选取的区域
        if exclude_x and exclude_y:
            # 排除右上角
            x_range = (x_min, pick_point[0])
            y_range = (y_min, pick_point[1])
        elif exclude_x and not exclude_y:
            # 排除右下角
            x_range = (x_min, pick_point[0])
            y_range = (pick_point[1], y_max)
        elif not exclude_x and exclude_y:
            # 排除左上角
            x_range = (pick_point[0], x_max)
            y_range = (y_min, pick_point[1])
        else:
            # 排除左下角
            x_range = (pick_point[0], x_max)
            y_range = (pick_point[1], y_max)
        
        # 计算允许的最大距离（中心点和pick_point的距离的max_distance_ratio倍）
        center_to_pick_dist = np.linalg.norm(center_point - pick_point)
        max_place_dist = center_to_pick_dist * max_distance_ratio
        
        # 生成place_point并验证是否满足距离条件
        while True:
            # 随机选择一个place_point的x和y
            place_x = np.random.uniform(*x_range)
            place_y = np.random.uniform(*y_range)
            place_2d = np.array([place_x, place_y])
            
            center_to_place_dist = np.linalg.norm(center_point[:2] - place_2d)
            pick2place_distance = np.linalg.norm(pick_point[:2] - place_2d)
            
            # 如果距离在允许范围内
            if pick2place_distance <= max_pick2place_distance:
                # 从points中找到离place_2d最近的点
                distances = np.linalg.norm(points[:, :2] - place_2d, axis=1)  # 计算所有点到place_2d的2D距离
                nearest_point_index = np.argmin(distances)  # 找到距离最小的点的索引
                nearest_point = points[nearest_point_index]  # 获取最近点的完整三维坐标
                
                return nearest_point  

def get_place_point_type2(mesh_points, op_y_rate):
    min_x, max_x = np.min(mesh_points[:, 0]), np.max(mesh_points[:, 0])
    min_y, max_y = np.min(mesh_points[:, 1]), np.max(mesh_points[:, 1])
    
    mesh_visible_indices = get_visible_indices(mesh_points)
    mesh_visible_points = mesh_points[mesh_visible_indices]
    left_mesh_visible_points = mesh_visible_points[mesh_visible_points[:, 0] < 0]
    right_mesh_visible_points = mesh_visible_points[mesh_visible_points[:, 0] > 0]
    op_y = min_y + (max_y - min_y) * op_y_rate
    left_op_x = -(max_x - min_x) / 20
    right_op_x = (max_x - min_x) / 20
    
    left_target = np.array([left_op_x, op_y])
    distances = np.linalg.norm(left_mesh_visible_points[:, :2] - left_target, axis=1)
    left_branch_point = left_mesh_visible_points[np.argmin(distances)]
    
    right_target = np.array([right_op_x, op_y])
    distances = np.linalg.norm(right_mesh_visible_points[:, :2] - right_target, axis=1)
    right_branch_point = right_mesh_visible_points[np.argmin(distances)]
    
    return left_branch_point, right_branch_point
 
def manipulate_garment(env, save_idx, save_npz_dir, save_rgb_dir):
    
    lift_offset = np.array([0, 0, 0.25])
    tolerance = 0.06
    
    initial_pc_points, _ = env.recording_camera.get_point_cloud_data()

    x_values = initial_pc_points[:, 0]
    min_x = np.min(x_values)
    max_x = np.max(x_values)
    cprint(max_x - min_x, 'yellow')
    
    y_values = initial_pc_points[:, 1]
    min_y = np.min(y_values)
    max_y = np.max(y_values)
    cprint(max_y - min_y, 'yellow')
    
    left_sleeve_point = initial_pc_points[np.argmin(x_values)]  # x 最小点 左袖子
    right_sleeve_point = initial_pc_points[np.argmax(x_values)]  # x 最大点 右袖子
    
    mesh_points = env.garment.get_vertice_positions()

    # 合并候选点
    candidates = np.vstack([left_sleeve_point, right_sleeve_point,
                            get_place_point_type2(mesh_points, 0.2)[0], get_place_point_type2(mesh_points, 0.2)[1],
                            get_place_point_type2(mesh_points, 0.5)[0], get_place_point_type2(mesh_points, 0.5)[1],])
    
    idx = 0
    pick_point_idx = np.random.choice(candidates.shape[0])
    pick_point = candidates[pick_point_idx]
    print("pick_point", pick_point)
    
    if pick_point_idx <=1:
        place_point = env.place_random_garment_point(pick_point, max_distance_ratio=1)
    elif pick_point_idx %2 == 0:
        x_offset_max = (max_x - min_x) / 4
        x_offset_min = (max_x - min_x) / 8
        x_offset = np.random.uniform(x_offset_min, x_offset_max)
        place_point = np.array([pick_point[0] - x_offset, pick_point[1], pick_point[2]])
    else:
        x_offset_max = (max_x - min_x) / 4
        x_offset_min = (max_x - min_x) / 8
        x_offset = np.random.uniform(x_offset_min, x_offset_max)
        place_point = np.array([pick_point[0] + x_offset, pick_point[1], pick_point[2]])
        
    print("place_point", place_point)    
    
    pick_air_point = pick_point + lift_offset
    place_air_point = place_point + lift_offset
    mani_trajectory = np.array([pick_point, pick_air_point, place_air_point, place_point])
    env.create_attach_block(idx, mani_trajectory[0] + np.array([0, 0, 10]))
    env.set_attach_to_garment(mani_trajectory[0])
    
    for i in range(10):
        env.step()
    
    for i in range(1, len(mani_trajectory)):
        env.attach.set_block_position_slowly(mani_trajectory[i], steps=20)
    
    env.attach.detach()
    
    for i in range(60):
        env.step()
    
    new_pc_points, _ = env.recording_camera.get_point_cloud_data()       
    mesh_points = env.garment.get_vertice_positions()

    # save npz and rgb
    np.savez(os.path.join(save_npz_dir, f"p_{save_idx}.npz"), 
                pcd_points=new_pc_points, 
                mesh_points=mesh_points)

    env.recording_camera.get_rgb_graph(
        save_path=os.path.join(save_rgb_dir, f"rgb_{save_idx}.png",),
        save_or_not=True
    )
    
    save_idx += 1
    
    print("stop")
    
    for i in range(1):
        env.step()     

def collect_data(type, idx, garment_usd_path, rotate_x, rotate_y):
    
    env = LiftGarment_Collect_Deformation(
        garment_path=garment_usd_path,
        garment_position=np.array([0, 0.0, 0.1]),
        garment_orientation=np.array([rotate_x, rotate_y, 0])
    )

    # Render initial frames to stabilize environment
    for _ in range(20):
        env.step()
        
    original_points, _ = env.recording_camera.get_point_cloud_data()
    
    if len(original_points) < 10:
        return
    
    garment_mesh_points = env.garment.get_vertice_positions()
    print(garment_mesh_points.shape)
    
    garment_category = garment_usd_path.split("/")[-1].split(".")[0]
    save_npz_dir = f"data/{type}/unigarment/cd_original/mesh_pcd/{idx}_{garment_category}"
    os.makedirs(save_npz_dir, exist_ok=True)
    save_rgb_dir = f"data/{type}/unigarment/cd_original/cd_rgb_view/{idx}_{garment_category}"
    os.makedirs(save_rgb_dir, exist_ok=True)
    
    if rotate_x == 0 and rotate_y == 0:
        save_idx = 0
    elif rotate_x == 30 and rotate_y == 0:
        save_idx = 1
    elif rotate_x == 45 and rotate_y == 0:
        save_idx = 2
    elif rotate_x == 0 and rotate_y == 30:
        save_idx = 3
    elif rotate_x == 90 and rotate_y == 45:
        save_idx = 4
    
    rotate_z = 0
    
    np.savez(os.path.join(save_npz_dir, f"p_{save_idx}.npz"),
             pcd_points=original_points,
             mesh_points=garment_mesh_points)
    
    env.recording_camera.get_rgb_graph(
        save_path=os.path.join(save_rgb_dir, f"rgb_{save_idx}.png")
    )
    
    # 获取当前目录下已经保存到多少号变形了
    max_sequence_number = get_max_sequence_number(save_npz_dir)
    
    if max_sequence_number >= 5:
        nxt_save_idx = max_sequence_number + 1
    else:
        nxt_save_idx = 5
    
    # 开始变形
    manipulate_garment(env, nxt_save_idx, save_npz_dir, save_rgb_dir)
    
    print('finished')


    
   

if __name__=="__main__":

    import argparse
    parser = argparse.ArgumentParser(description="Collect deformation data for a specific garment.")
    parser.add_argument("--type", type=str, default='front_open', help="Type of garment")
    parser.add_argument("--idx", type=int, default=0, help="Index of the garment")
    parser.add_argument("--garment_usd_path", type=str, default="./Assets/Garment/Tops/Collar_Lsleeve_FrontOpen/TCLO_model2_054/TCLO_model2_054_obj.usd", help="Path to the garment USD file")
    parser.add_argument("--rotate_x", type=int, default=0, help="Rotation angle around the x-axis")
    parser.add_argument("--rotate_y", type=int, default=0, help="Rotation angle around the y-axis")
    args = parser.parse_args()  
    
    type = args.type
    idx = args.idx
    garment_usd_path = args.garment_usd_path
    rotate_x = args.rotate_x
    rotate_y = args.rotate_y
    
    # type = "front_open"
    # idx = 0
    # garment_usd_path = "./Assets/Garment/Tops/Collar_Lsleeve_FrontOpen/TCLO_model2_054/TCLO_model2_054_obj.usd"
    # rotate_x = 0
    # rotate_y = 0
    # python LearningBaseline/unigarmentmanip/collect/collect_cd/collect_front_open_deformation.py --type front_open --idx 0 --garment_usd_path ./Assets/Garment/Tops/Collar_Lsleeve_FrontOpen/TCLO_model2_054/TCLO_model2_054_obj.usd --rotate_x 0 --rotate_y 0

    collect_data(type, idx, garment_usd_path,
                 rotate_x, rotate_y)
    
    
    
    
   