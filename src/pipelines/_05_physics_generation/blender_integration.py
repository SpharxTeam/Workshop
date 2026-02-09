"""
Blender物理仿真集成模块
使用Blender进行物理仿真和事实生成
"""

import os
import json
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import shutil
import numpy as np

from src.utils.file_utils import FileUtils

logger = logging.getLogger(__name__)


class BlenderIntegrationError(Exception):
    """Blender集成错误"""
    pass


class BlenderPhysicsSimulator:
    """
    Blender物理仿真器
    使用Blender进行物理仿真和场景分析
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化Blender仿真器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.file_utils = FileUtils()
        
        # Blender路径
        self.blender_path = self._find_blender()
        if not self.blender_path:
            raise BlenderIntegrationError("Blender未找到，请确保已安装Blender")
        
        # Python脚本路径
        self.script_dir = Path(__file__).parent / "blender_scripts"
        self.script_dir.mkdir(exist_ok=True)
        
        # 模板路径
        self.template_dir = Path("configs/physics/blender_templates")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Blender仿真器初始化完成，Blender路径: {self.blender_path}")
    
    def _find_blender(self) -> Optional[Path]:
        """查找Blender可执行文件"""
        # 尝试多个可能的路径
        possible_paths = [
            "/usr/bin/blender",
            "/usr/local/bin/blender",
            "/opt/blender/blender",
            "/Applications/Blender.app/Contents/MacOS/Blender",  # macOS
            "C:\\Program Files\\Blender Foundation\\Blender\\blender.exe",  # Windows
            shutil.which("blender")
        ]
        
        for path_str in possible_paths:
            if path_str:
                path = Path(path_str)
                if path.exists() and os.access(path, os.X_OK):
                    logger.info(f"找到Blender: {path}")
                    return path
        
        logger.warning("未找到Blender可执行文件")
        return None
    
    def run_blender_script(self, script_content: str, args: List[str] = None,
                          blend_file: Path = None) -> Tuple[bool, str]:
        """
        运行Blender Python脚本
        
        Args:
            script_content: Python脚本内容
            args: 额外参数
            blend_file: .blend文件路径
            
        Returns:
            (是否成功, 输出信息)
        """
        # 创建临时Python脚本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = Path(f.name)
        
        try:
            # 构建Blender命令
            command = [str(self.blender_path), "--background"]
            
            if blend_file:
                command.extend([str(blend_file)])
            
            command.extend([
                "--python", str(script_path),
                "--"
            ])
            
            if args:
                command.extend(args)
            
            logger.info(f"运行Blender命令: {' '.join(command)}")
            
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.config.get("timeout", 3600),
                check=False
            )
            
            if process.returncode == 0:
                logger.info("Blender脚本执行成功")
                return True, process.stdout
            else:
                error_msg = f"Blender脚本执行失败 (code={process.returncode}): {process.stderr}"
                logger.error(error_msg)
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = f"Blender脚本执行超时"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Blender脚本执行异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        finally:
            # 清理临时文件
            if script_path.exists():
                script_path.unlink()
    
    def import_3d_model(self, model_path: Path, model_type: str = "obj") -> str:
        """
        生成导入3D模型的Blender脚本
        
        Args:
            model_path: 模型文件路径
            model_type: 模型类型 ("obj", "ply", "fbx", "glb")
            
        Returns:
            Python脚本内容
        """
        script = f"""
import bpy
import os
import sys

# 清除场景
bpy.ops.wm.read_factory_settings(use_empty=True)

model_path = "{model_path}"
model_type = "{model_type}"

print(f"导入模型: {{model_path}}")

try:
    # 根据文件类型选择导入方法
    if model_type.lower() == "obj":
        bpy.ops.wm.obj_import(filepath=model_path)
    elif model_type.lower() == "ply":
        bpy.ops.wm.ply_import(filepath=model_path)
    elif model_type.lower() == "fbx":
        bpy.ops.import_scene.fbx(filepath=model_path)
    elif model_type.lower() == "glb" or model_type.lower() == "gltf":
        bpy.ops.import_scene.gltf(filepath=model_path)
    else:
        print(f"不支持的模型类型: {{model_type}}")
        sys.exit(1)
    
    print("模型导入成功")
    
    # 统计场景信息
    num_objects = len(bpy.data.objects)
    num_meshes = len(bpy.data.meshes)
    num_materials = len(bpy.data.materials)
    
    print(f"场景统计:")
    print(f"  物体数量: {{num_objects}}")
    print(f"  网格数量: {{num_meshes}}")
    print(f"  材质数量: {{num_materials}}")
    
    # 输出场景信息为JSON
    scene_info = {{
        "num_objects": num_objects,
        "num_meshes": num_meshes,
        "num_materials": num_materials,
        "objects": []
    }}
    
    for obj in bpy.data.objects:
        obj_info = {{
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "dimensions": list(obj.dimensions),
            "has_mesh": obj.type == 'MESH'
        }}
        
        if obj.type == 'MESH':
            mesh = obj.data
            obj_info["vertices"] = len(mesh.vertices)
            obj_info["faces"] = len(mesh.polygons)
            obj_info["materials"] = len(mesh.materials)
        
        scene_info["objects"].append(obj_info)
    
    # 保存场景信息
    import json
    info_path = os.path.join(os.path.dirname(model_path), "scene_info.json")
    with open(info_path, 'w') as f:
        json.dump(scene_info, f, indent=2)
    
    print(f"场景信息已保存: {{info_path}}")
    
except Exception as e:
    print(f"模型导入失败: {{e}}")
    sys.exit(1)
"""
        return script
    
    def setup_physics(self, material_properties: Dict[str, Any] = None) -> str:
        """
        生成设置物理属性的Blender脚本
        
        Args:
            material_properties: 材料属性
            
        Returns:
            Python脚本内容
        """
        if material_properties is None:
            material_properties = {
                "default": {
                    "density": 1000.0,  # kg/m³
                    "friction": 0.5,
                    "restitution": 0.3
                }
            }
        
        material_json = json.dumps(material_properties, indent=2)
        
        script = f"""
import bpy
import json

# 材料属性配置
material_properties = {material_json}

print("设置物理属性...")

# 启用物理引擎
bpy.context.scene.use_gravity = True
bpy.context.scene.gravity = (0, 0, -9.81)  # 标准重力

# 设置物理属性
for obj_name, props in material_properties.items():
    # 尝试按名称查找物体，或应用默认设置
    if obj_name == "default":
        continue
    
    if obj_name in bpy.data.objects:
        obj = bpy.data.objects[obj_name]
        
        # 添加刚体物理
        if obj.rigid_body is None:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.rigidbody.object_add()
        
        # 设置质量属性（基于体积和密度）
        if obj.type == 'MESH':
            # 计算体积（近似）
            dimensions = obj.dimensions
            volume = dimensions.x * dimensions.y * dimensions.z
            
            # 设置质量
            density = props.get("density", 1000.0)
            mass = volume * density
            
            obj.rigid_body.mass = mass
            print(f"物体 {{obj_name}}: 质量={{mass:.2f}}kg (密度={{density}}kg/m³)")
        
        # 设置物理材质
        if "friction" in props:
            obj.rigid_body.friction = props["friction"]
        if "restitution" in props:
            obj.rigid_body.restitution = props["restitution"]
        
        # 设置碰撞形状
        obj.rigid_body.collision_shape = 'MESH'  # 使用实际网格作为碰撞形状

# 为没有特定属性的物体应用默认设置
default_props = material_properties.get("default", {{}})
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.rigid_body is None:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.rigidbody.object_add()
        
        # 计算质量
        dimensions = obj.dimensions
        volume = dimensions.x * dimensions.y * dimensions.z
        density = default_props.get("density", 1000.0)
        mass = volume * density
        
        obj.rigid_body.mass = mass
        
        if "friction" in default_props:
            obj.rigid_body.friction = default_props["friction"]
        if "restitution" in default_props:
            obj.rigid_body.restitution = default_props["restitution"]
        
        obj.rigid_body.collision_shape = 'MESH'

print("物理属性设置完成")
"""
        return script
    
    def run_simulation(self, duration: float = 5.0, steps: int = 250,
                      output_path: Path = None) -> str:
        """
        生成运行物理仿真的Blender脚本
        
        Args:
            duration: 仿真时长（秒）
            steps: 仿真步数
            output_path: 输出路径
            
        Returns:
            Python脚本内容
        """
        if output_path is None:
            output_path = Path.cwd() / "simulation_output.json"
        
        script = f"""
import bpy
import json
import math

print("开始物理仿真...")

# 仿真参数
duration = {duration}
steps = {steps}
output_path = "{output_path}"

# 设置仿真参数
bpy.context.scene.rigidbody_world.time_scale = 1.0
bpy.context.scene.rigidbody_world.substeps_per_frame = 10
bpy.context.scene.rigidbody_world.solver_iterations = 50

# 记录初始状态
initial_state = []
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.rigid_body:
        initial_state.append({{
            "name": obj.name,
            "type": obj.type,
            "initial_location": list(obj.location),
            "initial_rotation": list(obj.rotation_euler),
            "mass": obj.rigid_body.mass,
            "friction": obj.rigid_body.friction,
            "restitution": obj.rigid_body.restitution
        }})

# 运行仿真
print(f"运行仿真: {{duration}}秒, {{steps}}步")
frame_start = bpy.context.scene.frame_start
frame_end = int(duration * bpy.context.scene.render.fps)

bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = frame_end

# 记录仿真数据
simulation_data = {{
    "duration": duration,
    "fps": bpy.context.scene.render.fps,
    "total_frames": frame_end,
    "objects": {{}},
    "collisions": []
}}

# 为每个物体创建记录
for obj_info in initial_state:
    obj_name = obj_info["name"]
    simulation_data["objects"][obj_name] = {{
        "trajectory": [],
        "rotations": [],
        "velocities": [],
        "initial_state": obj_info
    }}

# 逐帧记录
for frame in range(0, frame_end + 1):
    bpy.context.scene.frame_set(frame)
    
    # 记录每个物体的状态
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.rigid_body:
            obj_name = obj.name
            
            # 位置和旋转
            simulation_data["objects"][obj_name]["trajectory"].append(list(obj.location))
            simulation_data["objects"][obj_name]["rotations"].append(list(obj.rotation_euler))
            
            # 速度
            if hasattr(obj.rigid_body, 'linear_velocity'):
                velocity = list(obj.rigid_body.linear_velocity)
                simulation_data["objects"][obj_name]["velocities"].append(velocity)
    
    # 检测碰撞（简化版本）
    for obj1 in bpy.data.objects:
        if obj1.type == 'MESH' and obj1.rigid_body:
            for obj2 in bpy.data.objects:
                if obj2.type == 'MESH' and obj2.rigid_body and obj1.name != obj2.name:
                    # 简单的AABB碰撞检测
                    loc1 = obj1.location
                    dim1 = obj1.dimensions
                    loc2 = obj2.location
                    dim2 = obj2.dimensions
                    
                    # 检查边界框重叠
                    overlap_x = abs(loc1.x - loc2.x) < (dim1.x/2 + dim2.x/2)
                    overlap_y = abs(loc1.y - loc2.y) < (dim1.y/2 + dim2.y/2)
                    overlap_z = abs(loc1.z - loc2.z) < (dim1.z/2 + dim2.z/2)
                    
                    if overlap_x and overlap_y and overlap_z:
                        collision = {{
                            "frame": frame,
                            "time": frame / bpy.context.scene.render.fps,
                            "object1": obj1.name,
                            "object2": obj2.name,
                            "location1": list(loc1),
                            "location2": list(loc2)
                        }}
                        
                        # 避免重复记录
                        if collision not in simulation_data["collisions"]:
                            simulation_data["collisions"].append(collision)

# 保存仿真数据
print(f"保存仿真数据: {{output_path}}")
with open(output_path, 'w') as f:
    json.dump(simulation_data, f, indent=2)

print("仿真完成")
"""
        return script
    
    def analyze_scene_relationships(self, output_path: Path = None) -> str:
        """
        生成分析场景关系的Blender脚本
        
        Args:
            output_path: 输出路径
            
        Returns:
            Python脚本内容
        """
        if output_path is None:
            output_path = Path.cwd() / "scene_relationships.json"
        
        script = f"""
import bpy
import json
import math

print("分析场景关系...")

relationships = {{
    "supporting": [],
    "containing": [],
    "adjacent": [],
    "attached": []
}}

# 分析支撑关系
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        # 获取物体底部（最低点）
        vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
        if vertices:
            min_z = min(v.z for v in vertices)
            bottom_center = obj.location.copy()
            bottom_center.z = min_z + obj.dimensions.z / 2
            
            # 向下发射射线检测支撑物体
            ray_origin = bottom_center
            ray_direction = (0, 0, -1)
            ray_length = 1.0  # 1米
            
            # 使用场景射线检测
            depsgraph = bpy.context.evaluated_depsgraph_get()
            result, location, normal, index, hit_obj, matrix = bpy.context.scene.ray_cast(
                depsgraph, ray_origin, ray_direction, distance=ray_length
            )
            
            if result and hit_obj and hit_obj.name != obj.name:
                # 计算接触面积（简化）
                dimensions = obj.dimensions
                contact_area = dimensions.x * dimensions.y
                
                relationships["supporting"].append({{
                    "supported": obj.name,
                    "supporter": hit_obj.name,
                    "contact_area": contact_area,
                    "contact_point": list(location),
                    "normal": list(normal)
                }})

# 分析包含关系（基于边界框）
for obj1 in bpy.data.objects:
    if obj1.type == 'MESH':
        bbox1 = [obj1.matrix_world @ v.co for v in obj1.bound_box]
        min1 = [min(v[i] for v in bbox1) for i in range(3)]
        max1 = [max(v[i] for v in bbox1) for i in range(3)]
        
        for obj2 in bpy.data.objects:
            if obj2.type == 'MESH' and obj1.name != obj2.name:
                bbox2 = [obj2.matrix_world @ v.co for v in obj2.bound_box]
                min2 = [min(v[i] for v in bbox2) for i in range(3)]
                max2 = [max(v[i] for v in bbox2) for i in range(3)]
                
                # 检查obj1是否包含obj2
                if (min1[0] <= min2[0] and max1[0] >= max2[0] and
                    min1[1] <= min2[1] and max1[1] >= max2[1] and
                    min1[2] <= min2[2] and max1[2] >= max2[2]):
                    
                    relationships["containing"].append({{
                        "container": obj1.name,
                        "contained": obj2.name,
                        "containment_type": "fully_enclosed"
                    }})

# 分析相邻关系（基于距离）
distance_threshold = 0.1  # 10厘米
for i, obj1 in enumerate(bpy.data.objects):
    if obj1.type == 'MESH':
        for obj2 in list(bpy.data.objects)[i+1:]:
            if obj2.type == 'MESH':
                distance = (obj1.location - obj2.location).length
                if distance < distance_threshold:
                    relationships["adjacent"].append({{
                        "object1": obj1.name,
                        "object2": obj2.name,
                        "distance": distance
                    }})

# 保存关系数据
print(f"保存关系数据: {{output_path}}")
with open(output_path, 'w') as f:
    json.dump(relationships, f, indent=2)

print("场景关系分析完成")
"""
        return script
    
    def generate_physics_facts(self, scene_id: str, model_path: Path, 
                              output_dir: Path) -> Dict[str, Any]:
        """
        生成物理事实
        
        Args:
            scene_id: 场景ID
            model_path: 3D模型路径
            output_dir: 输出目录
            
        Returns:
            物理事实数据
        """
        logger.info(f"为场景 {scene_id} 生成物理事实...")
        
        result = {
            "scene_id": scene_id,
            "success": False,
            "stages": {},
            "outputs": {},
            "errors": []
        }
        
        try:
            # 1. 导入模型
            logger.info("阶段1: 导入3D模型...")
            import_script = self.import_3d_model(model_path)
            
            success, output = self.run_blender_script(import_script)
            if not success:
                result["errors"].append("模型导入失败")
                return result
            
            result["stages"]["import"] = {
                "status": "completed",
                "output": output
            }
            
            # 2. 分析场景关系
            logger.info("阶段2: 分析场景关系...")
            relationships_path = output_dir / "relationships.json"
            analysis_script = self.analyze_scene_relationships(relationships_path)
            
            success, output = self.run_blender_script(analysis_script)
            if success and relationships_path.exists():
                with open(relationships_path, 'r') as f:
                    relationships = json.load(f)
                result["outputs"]["relationships"] = relationships
                result["stages"]["relationship_analysis"] = {
                    "status": "completed"
                }
            else:
                result["stages"]["relationship_analysis"] = {
                    "status": "partial",
                    "error": "关系分析部分失败"
                }
            
            # 3. 设置物理属性
            logger.info("阶段3: 设置物理属性...")
            material_properties = self.config.get("material_properties", {
                "default": {
                    "density": 1000.0,
                    "friction": 0.5,
                    "restitution": 0.3
                }
            })
            
            physics_script = self.setup_physics(material_properties)
            
            success, output = self.run_blender_script(physics_script)
            result["stages"]["physics_setup"] = {
                "status": "completed" if success else "partial",
                "output": output
            }
            
            # 4. 运行物理仿真
            logger.info("阶段4: 运行物理仿真...")
            simulation_path = output_dir / "simulation.json"
            simulation_script = self.run_simulation(
                duration=self.config.get("simulation_duration", 5.0),
                steps=self.config.get("simulation_steps", 250),
                output_path=simulation_path
            )
            
            success, output = self.run_blender_script(simulation_script)
            if success and simulation_path.exists():
                with open(simulation_path, 'r') as f:
                    simulation_data = json.load(f)
                result["outputs"]["simulation"] = simulation_data
                result["stages"]["simulation"] = {
                    "status": "completed"
                }
            else:
                result["stages"]["simulation"] = {
                    "status": "partial",
                    "error": "仿真部分失败"
                }
            
            # 5. 生成物理事实汇总
            logger.info("阶段5: 生成物理事实汇总...")
            facts_path = output_dir / "physics_facts.json"
            facts = self._generate_facts_summary(result, output_dir)
            
            with open(facts_path, 'w') as f:
                json.dump(facts, f, indent=2)
            
            result["outputs"]["physics_facts"] = facts
            result["outputs"]["facts_path"] = str(facts_path)
            result["success"] = True
            
            logger.info(f"物理事实生成完成: {scene_id}")
            
        except Exception as e:
            logger.error(f"物理事实生成异常: {e}", exc_info=True)
            result["errors"].append(f"处理异常: {str(e)}")
            result["success"] = False
        
        return result
    
    def _generate_facts_summary(self, result: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
        """生成物理事实汇总"""
        facts = {
            "scene_id": result["scene_id"],
            "generation_time": self._get_timestamp(),
            "stages_completed": [],
            "relationships_summary": {},
            "physics_properties": {},
            "simulation_summary": {}
        }
        
        # 记录完成的阶段
        for stage_name, stage_info in result["stages"].items():
            if stage_info.get("status") == "completed":
                facts["stages_completed"].append(stage_name)
        
        # 关系汇总
        if "relationships" in result["outputs"]:
            relationships = result["outputs"]["relationships"]
            facts["relationships_summary"] = {
                "total_relationships": sum(len(v) for v in relationships.values()),
                "by_type": {k: len(v) for k, v in relationships.items()}
            }
        
        # 物理属性汇总
        if "physics_facts" in result["outputs"]:
            # 从配置中获取材料属性
            material_props = self.config.get("material_properties", {})
            facts["physics_properties"] = {
                "materials_configured": len(material_props),
                "gravity": -9.81,
                "default_density": material_props.get("default", {}).get("density", 1000.0)
            }
        
        # 仿真汇总
        if "simulation" in result["outputs"]:
            sim_data = result["outputs"]["simulation"]
            facts["simulation_summary"] = {
                "duration": sim_data.get("duration"),
                "total_frames": sim_data.get("total_frames"),
                "objects_simulated": len(sim_data.get("objects", {})),
                "collisions_detected": len(sim_data.get("collisions", []))
            }
        
        return facts
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


class PhysicsGenerator:
    """
    物理事实生成器
    高层接口，协调多个物理分析任务
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.simulator = BlenderPhysicsSimulator(config)
        self.file_utils = FileUtils()
    
    def generate_for_scene(self, scene_id: str, model_path: Path, 
                          output_dir: Path = None) -> Dict[str, Any]:
        """
        为场景生成物理事实
        
        Args:
            scene_id: 场景ID
            model_path: 3D模型路径
            output_dir: 输出目录
            
        Returns:
            生成结果
        """
        if output_dir is None:
            output_dir = Path(f"/home/SpharxWorkshop/data/output/datasets/SPHARX_PHYSICS_{scene_id}/L3_physics_facts")
        
        # 创建输出目录
        self.file_utils.ensure_dir(output_dir)
        
        # 生成物理事实
        result = self.simulator.generate_physics_facts(scene_id, model_path, output_dir)
        
        # 如果成功，复制相关文件
        if result["success"] and "outputs" in result:
            # 复制关键文件到标准位置
            standard_files = {
                "physics_facts.json": output_dir / "physics_facts.json",
                "relationships.json": output_dir / "relationships.json",
                "simulation.json": output_dir / "simulation.json"
            }
            
            for name, path in standard_files.items():
                if path.exists():
                    # 已经在该位置，无需复制
                    pass
        
        return result
    
    def batch_generate(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量生成物理事实
        
        Args:
            scenes: 场景列表，每个场景包含scene_id和model_path
            
        Returns:
            生成结果列表
        """
        results = []
        
        for scene_info in scenes:
            scene_id = scene_info["scene_id"]
            model_path = Path(scene_info["model_path"])
            
            logger.info(f"开始处理场景: {scene_id}")
            
            try:
                result = self.generate_for_scene(scene_id, model_path)
                results.append(result)
            except Exception as e:
                logger.error(f"场景处理失败 {scene_id}: {e}")
                results.append({
                    "scene_id": scene_id,
                    "success": False,
                    "error": str(e)
                })
        
        return results