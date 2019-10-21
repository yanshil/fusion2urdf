#Author-syuntoku14
#Description-Generate URDF file from Fusion 360

import adsk, adsk.core, adsk.fusion, traceback
import os
from .utils import utils_binary
from .core import Link, Joint, Write

import json

"""
# length unit is 'cm' and inertial unit is 'kg/cm^2'
# If there is no 'body' in the root component, maybe the corrdinates are wrong.
"""

# joint effort: 100
# joint velocity: 100
# supports "Revolute", "Rigid" and "Slider" joint types

# I'm not sure how prismatic joint acts if there is no limit in fusion model

def run(context):
    ui = None
    success_msg = 'Successfully create URDF file'
    msg = success_msg
    
    try:
        # --------------------
        # initialize
        app = adsk.core.Application.get()
        ui = app.userInterface
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        title = 'Fusion2URDF'
        if not design:
            ui.messageBox('No active Fusion design', title)
            return

        root = design.rootComponent  # root component 
        components = design.allComponents

        # set the names        
        package_name = 'fusion2urdf'
        robot_name = root.name.split()[0]
        save_dir = utils_binary.file_dialog(ui)
        if save_dir == False:
            ui.messageBox('Fusion2URDF was canceled', title)
            return 0
        
        save_dir = save_dir + '/' + robot_name
        try: os.mkdir(save_dir)
        except: pass     
        
        # --------------------
        # set dictionaries
        #joints_dict = {}
        inertial_dict = {}
        links_xyz_dict = {}

        # ## Generate joints_dict for ALL joints
        # for comp in design.allComponents:
        #     if comp.joints:
        #         comp_joints_dict, msg = Joint.make_joints_dict(comp, msg)
        #         joints_dict.update(comp_joints_dict)
        #         if msg != success_msg:
        #             ui.messageBox('Check Component: ' + comp.name + '\t Joint: ' + joint.name)
        #             ui.messageBox(msg, title)
        #             return 0
        
        [joints_dict, resultString] = Joint.getJoints(root)
        ui.messageBox(resultString)

        ## Generate inertial_dict
        inertial_dict, msg = Link.make_inertial_dict(root, msg)
        if msg != success_msg:
            ui.messageBox(msg, title)
            return 0         
        elif not 'base_link' in inertial_dict:
            msg = 'There is no base_link. Please set base_link and run again.'
            ui.messageBox(msg, title)
            return 0

        # --- TEST ---
        jd1 = json.dumps(joints_dict)
        f = open(os.path.join(save_dir,"joints_dict.json"),"w")
        f.write(jd1)
        f.close()

        jd2 = json.dumps(inertial_dict)
        f = open(os.path.join(save_dir,"inertial_dict.json"),"w")
        f.write(jd2)
        f.close()

        # --------------------
        # Generate URDF
        Write.write_urdf(joints_dict, links_xyz_dict, inertial_dict, package_name, save_dir, robot_name)
        Write.write_gazebo_launch(robot_name, save_dir)
        Write.write_control_launch(robot_name, save_dir, joints_dict)
        Write.write_yaml(robot_name, save_dir, joints_dict)
        
        # Generate STl files        
        ##utils.copy_occs(root)
        utils_binary.create_stl_export_component(root)
        utils_binary.export_stl(design, save_dir)   
        
        ui.messageBox(msg, title)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
