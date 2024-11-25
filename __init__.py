# 本项目由 [叶北宋] 提供，仅供学习与个人使用。未经授权，不得用于商业活动、分发或抄写。
# 如需商业用途，请联系作者并获得书面许可。
# Copyright (C) [2024/11/25] [叶北宋]. All rights reserved.
bl_info = {
    "name": "spark-Gold weight module",
    "blender": (4, 0, 0),
    "category": "spark",
    "version": (1, 9, 0),
    "author": "叶北宋",
    "description": "spark-金重模块",
    "location": "View3D > Sidebar > Spark",
}

import bpy
import bmesh
from bpy.types import Panel, Operator
from bpy.props import StringProperty

class MESH_OT_calculate_selected_volumes(Operator):
    bl_idname = "mesh.calculate_selected_volumes"
    bl_label = "Calculate Volumes for Selected Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected.")
            return {'CANCELLED'}

        volume_dict = {}
        total_volume = 0

        for obj in selected_objects:
            if obj.type == 'MESH':
                volume = self.calculate_mesh_volume(obj)
            elif obj.type == 'CURVE':
                volume = self.calculate_curve_volume(obj)
            elif obj.type == 'SURFACE':
                volume = self.calculate_surface_volume(obj)
            else:
                continue

            if volume:
                volume_dict[obj.name] = volume
                total_volume += volume
        
        context.scene.spark_volume_results = str(volume_dict)
        context.scene.spark_total_volume = total_volume

        self.report({'INFO'}, f"Total Volume: {total_volume:.6f} cubic units")
        return {'FINISHED'}

    def calculate_mesh_volume(self, obj):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        
        if not eval_obj.data.polygons:
            self.report({'WARNING'}, f"Object {obj.name} has no volume.")
            return 0.0
        
        mesh_data = eval_obj.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(mesh_data)
        bm.transform(eval_obj.matrix_world)
        volume = bm.calc_volume()
        bm.free()
        eval_obj.to_mesh_clear()
        
        return volume

    def calculate_curve_volume(self, obj):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        
        mesh_data = eval_obj.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(mesh_data)
        bm.transform(eval_obj.matrix_world)
        volume = bm.calc_volume()
        bm.free()
        eval_obj.to_mesh_clear()
        
        return volume

    def calculate_surface_volume(self, obj):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        
        mesh_data = eval_obj.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(mesh_data)
        bm.transform(eval_obj.matrix_world)
        volume = bm.calc_volume()
        bm.free()
        eval_obj.to_mesh_clear()
        
        return volume

class MESH_OT_scale_to_target_weight(Operator):
    bl_idname = "mesh.scale_to_target_weight"
    bl_label = "Scale to Target Weight"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected.")
            return {'CANCELLED'}
        
        total_volume = context.scene.spark_total_volume
        density = context.scene.spark_density
        target_weight = context.scene.spark_target_weight

        if total_volume == 0 or density == 0:
            self.report({'ERROR'}, "Cannot scale objects: total volume or density is zero.")
            return {'CANCELLED'}

        current_weight = total_volume * 0.001 * density
        scale_factor = (target_weight / current_weight) ** (1/3)
        context.scene.spark_scale_factor = scale_factor

        for obj in selected_objects:
            obj.scale *= scale_factor
            bpy.ops.object.transform_apply(scale=True)

        self.report({'INFO'}, f"Scaled selected objects to target weight: {target_weight:.6f} g")
        return {'FINISHED'}

class MESH_OT_save_output_to_file(Operator):
    bl_idname = "mesh.save_output_to_file"
    bl_label = "Save Output to File"
    
    filepath: StringProperty(
        name="File Path",
        description="File path to save the output text",
        default="//output.txt",
        subtype='FILE_PATH'
    )

    def execute(self, context):
        scene = context.scene
        volume_results = eval(scene.spark_volume_results)
        total_volume = scene.spark_total_volume
        total_volume_ml = total_volume * 0.001
        density = scene.spark_density
        total_weight = total_volume_ml * density
        scale_factor = scene.spark_scale_factor

        output_text = "Selected Objects' Volumes:\n"
        for obj_name, volume in volume_results.items():
            output_text += f"{obj_name}: {volume:.6f} cubic units\n"
        output_text += f"Total Volume: {total_volume:.6f} cubic units\n"
        output_text += f"Total Weight: {total_weight:.6f} g (Density: {density})\n"
        output_text += f"Scale Factor: {scale_factor:.6f}\n"

        with open(self.filepath, 'w') as file:
            file.write(output_text)

        self.report({'INFO'}, f"Output saved to {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class WM_OT_execute_script(Operator):
    bl_idname = "wm.execute_script"
    bl_label = "Execute Script"

    script_path: StringProperty(
        name="Script Path",
        description="Path to the Python script to execute",
        default="",
        subtype='FILE_PATH'
    )

    def execute(self, context):
        try:
            with open(self.script_path, 'r') as file:
                exec(file.read(), globals())
            self.report({'INFO'}, f"Script executed: {self.script_path}")
        except Exception as e:
            self.report({'ERROR'}, f"Error executing script: {str(e)}")
        return {'FINISHED'}

class VIEW3D_PT_spark_volume_tools(Panel):
    bl_label = "  "
    bl_idname = "VIEW3D_PT_spark_volume_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'spark'

    def draw_header(self, context):
        layout = self.layout
        row = layout.row(align=True)
        
        row.alignment = 'RIGHT'
        row.operator("wm.execute_script", text="", icon='COPY_ID').script_path = r"C:\spark\BL\脚本\打开b站链接.py"
        row.label(text="     spark-金重模块     ")
        row.operator("wm.execute_script", text="", icon='QUESTION').script_path = r"C:\spark\BL\脚本\打开b站链接.py"
        row.separator()
        row.label(text="  ")

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text="选中物体的数据:")
        
        volume_results = eval(scene.spark_volume_results)
        for obj_name, volume in volume_results.items():
            box.label(text=f"{obj_name}: {volume:.6f} 立方毫米")

        box.label(text=f"总体积(单位:立方毫米): {scene.spark_total_volume:.6f} 立方毫米")
        
        total_volume_ml = scene.spark_total_volume * 0.001
        density = scene.spark_density
        total_weight = total_volume_ml * density
        box.label(text=f"总重量(单位:g): {total_weight:.6f} g (相对密度: {density})")

        scale_factor = scene.spark_scale_factor
        box.label(text=f"缩放比例,点击修改金重即时刷新: {scale_factor:.6f}")

        layout.operator("mesh.calculate_selected_volumes", text="点击测量")
        
        layout.separator()
        layout.label(text="金重控制器:")
        layout.prop(scene, "spark_target_weight")
        layout.operator("mesh.scale_to_target_weight", text="点击修改金重")
        
        layout.separator()
        layout.label(text="Density:")
        layout.prop(scene, "spark_density", slider=True)

        layout.separator()
        layout.operator("mesh.save_output_to_file", text="保存数据到指定路径")
        
        # Transform sub-panel
        layout.separator()
        layout.label(text="Transform:")
        box = layout.box()
        box.use_property_split = True
        box.use_property_decorate = False
        box.prop(context.object, "location")
        box.prop(context.object, "rotation_euler", text="Rotation")
        box.prop(context.object, "scale")

def register():
    bpy.utils.register_class(MESH_OT_calculate_selected_volumes)
    bpy.utils.register_class(MESH_OT_scale_to_target_weight)
    bpy.utils.register_class(MESH_OT_save_output_to_file)
    bpy.utils.register_class(VIEW3D_PT_spark_volume_tools)
    bpy.utils.register_class(WM_OT_execute_script)
    
    bpy.types.Scene.spark_volume_results = bpy.props.StringProperty(
        name="Volume Results", 
        description="Calculated volumes for selected objects",
        default="{}"
    )
    
    bpy.types.Scene.spark_total_volume = bpy.props.FloatProperty(
        name="Total Volume", 
        description="Total calculated volume for selected objects",
        default=0.0
    )

    bpy.types.Scene.spark_target_weight = bpy.props.FloatProperty(
        name="Target Weight (g)", 
        description="Target weight for scaling",
        default=1.0
    )

    bpy.types.Scene.spark_density = bpy.props.FloatProperty(
        name="Density", 
        description="Density value used for weight calculation",
        default=1.0,
        min=0.0,
        max=100.0
    )

    bpy.types.Scene.spark_scale_factor = bpy.props.FloatProperty(
        name="Scale Factor", 
        description="Last used scale factor",
        default=1.0
    )

def unregister():
    bpy.utils.unregister_class(MESH_OT_calculate_selected_volumes)
    bpy.utils.unregister_class(MESH_OT_scale_to_target_weight)
    bpy.utils.unregister_class(MESH_OT_save_output_to_file)
    bpy.utils.unregister_class(VIEW3D_PT_spark_volume_tools)
    bpy.utils.unregister_class(WM_OT_execute_script)
    
    del bpy.types.Scene.spark_volume_results
    del bpy.types.Scene.spark_total_volume
    del bpy.types.Scene.spark_target_weight
    del bpy.types.Scene.spark_density
    del bpy.types.Scene.spark_scale_factor

if __name__ == "__main__":
    register()
