import os
import shutil

# 设置源路径和目标路径
source_dir = './Assets/Garment/Hat'
target_dir = './Assets/tmp/all_hats'

# 确保目标目录存在

os.makedirs(target_dir, exist_ok=True)

# 遍历源路径下的文件夹
for i in range(1, 120):
    # 格式化ID为三位数
    folder_name = f"HA_hat{str(i).zfill(3)}"
    file_name = f"HA_hat{str(i).zfill(3)}_obj.usd"
    
    # 构建文件的完整路径
    source_file = os.path.join(source_dir, folder_name, file_name)
    
    # 检查源文件是否存在
    if os.path.exists(source_file):
        if os.path.exists(os.path.join(target_dir, file_name)):
            pass
        # 复制文件到目标路径
        shutil.copy(source_file, target_dir)
        print(f"Copied: {source_file} {target_dir}")
    else:
        print(f"File not found: {source_file}")
        


''' 有几个文件的命名方式不同 '''
# for i in range(1, 5):
#     # 格式化ID为三位数
#     folder_name = f"HA_hat{str(i)}"
#     file_name = f"HA_hat{str(i)}_obj.usd"
    
#     # 构建文件的完整路径
#     source_file = os.path.join(source_dir, folder_name, file_name)
    
#     # 检查源文件是否存在
#     if os.path.exists(source_file):
#         # 复制文件到目标路径
#         shutil.copy(source_file, target_dir)
#         print(f"Copied: {source_file} {target_dir}")
#     else:
#         print(f"File not found: {source_file}")
