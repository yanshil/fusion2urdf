# -*- coding: utf-8 -*-
"""
Modified on Wed Oct 16 12:58:45 2019

@author: syuntoku
@yanshil
"""

import adsk, re
from xml.etree.ElementTree import Element, SubElement
from ..utils import utils_binary

class Joint:
    def __init__(self, key, name, xyz, axis, parent, child, joint_type, upper_limit, lower_limit):
        """
        Attributes
        ----------
        key: str
            full path of child + name of the joint
        name: str
            name of the joint
        type: str
            type of the joint(ex: rev)
        xyz: [x, y, z]
            coordinate of the joint
        axis: [x, y, z]
            coordinate of axis of the joint
        parent: str
            parent link
        child: str
            child link
        joint_xml: str
            generated xml describing about the joint
        tran_xml: str
            generated xml describing about the transmission
        """
        self.key = key
        self.name = name
        self.type = joint_type
        self.xyz = xyz
        self.parent = parent
        self.child = child
        self.joint_xml = None
        self.tran_xml = None
        self.axis = axis  # for 'revolute' and 'continuous'
        self.upper_limit = upper_limit  # for 'revolute' and 'prismatic'
        self.lower_limit = lower_limit  # for 'revolute' and 'prismatic'
        
    def make_joint_xml(self):
        """
        Generate the joint_xml and hold it by self.joint_xml
        """
        joint = Element('joint')
        joint.attrib = {'name':self.key, 'type':self.type}
        
        origin = SubElement(joint, 'origin')
        origin.attrib = {'xyz':' '.join([str(_) for _ in self.xyz]), 'rpy':'0 0 0'}
        parent = SubElement(joint, 'parent')
        parent.attrib = {'link':self.parent}
        child = SubElement(joint, 'child')
        child.attrib = {'link':self.child}
        if self.type == 'revolute' or self.type == 'continuous' or self.type == 'prismatic':        
            axis = SubElement(joint, 'axis')
            axis.attrib = {'xyz':' '.join([str(_) for _ in self.axis])}
        if self.type == 'revolute' or self.type == 'prismatic':
            limit = SubElement(joint, 'limit')
            limit.attrib = {'upper': str(self.upper_limit), 'lower': str(self.lower_limit),
                            'effort': '100', 'velocity': '100'}
            
        self.joint_xml = "\n".join(utils_binary.prettify(joint).split("\n")[1:])

    def make_transmission_xml(self):
        """
        Generate the tran_xml and hold it by self.tran_xml
        
        
        Notes
        -----------
        mechanicalTransmission: 1
        type: transmission interface/SimpleTransmission
        hardwareInterface: PositionJointInterface        
        """        
        
        tran = Element('transmission')
        tran.attrib = {'name':self.key + '_tran'}
        
        joint_type = SubElement(tran, 'type')
        joint_type.text = 'transmission_interface/SimpleTransmission'
        
        joint = SubElement(tran, 'joint')
        joint.attrib = {'name':self.key}
        hardwareInterface_joint = SubElement(joint, 'hardwareInterface')
        hardwareInterface_joint.text = 'PositionJointInterface'
        
        actuator = SubElement(tran, 'actuator')
        actuator.attrib = {'name':self.key + '_actr'}
        hardwareInterface_actr = SubElement(actuator, 'hardwareInterface')
        hardwareInterface_actr.text = 'PositionJointInterface'
        mechanicalReduction = SubElement(actuator, 'mechanicalReduction')
        mechanicalReduction.text = '1'
        
        self.tran_xml = "\n".join(utils_binary.prettify(tran).split("\n")[1:])



def traverseAssembly(occurrences, currentLevel, inputString, joints_dict={}, msg='Successfully create URDF file'):
    for i in range(0, occurrences.count):
        occ = occurrences.item(i)

        if occ.component.joints:
            for joint in occ.component.joints:
                ass_joint = joint.createForAssemblyContext(occ)
                tmp_joints_dict, msg = make_joints_dict(ass_joint, msg)
                if msg != 'Successfully create URDF file':
                    ui = adsk.core.Application.get().userInterface
                    ui.messageBox('Check Component: ' + comp.name + '\t Joint: ' + joint.name)
                    ui.messageBox(msg, title)
                    return 0
                joints_dict.update(tmp_joints_dict)
                inputString += spaces(currentLevel * 5) + 'Name: ' + occ.name  + ' +++ Joint: ' + ass_joint.name + '\n'
        else:
            inputString += spaces(currentLevel * 5) + 'Name: ' + occ.name + '\n'
        
        if occ.childOccurrences:
            [joints_dict, inputString] = traverseAssembly(occ.childOccurrences, currentLevel + 1, inputString, joints_dict,msg)

    return [joints_dict, inputString]

# Returns a string containing the especified number of spaces.
def spaces(spaceCount):
    result = ''
    for i in range(0, spaceCount):
        result += ' '

    return result

def getJoints(root):
    # Create the title for the output.
    resultString = 'Assembly structure \n'
    
    root_joint_dict = {}
    for joint in root.joints:
        tmp_dict,msg = make_joints_dict(joint, '')
        root_joint_dict.update(tmp_dict)
    
    # Call the recursive function to traverse the assembly and build the output string.
    [joints_dict, resultString] = traverseAssembly(root.occurrences.asList, 1, resultString)

    joints_dict.update(root_joint_dict)

    return [joints_dict, resultString]


def make_joints_dict(joint, msg):
    """
    joints_dict holds parent, axis and xyz information of the joints
    
    
    Parameters
    ----------
    joint: the input joint for grabbing infos
        comp.joint OR occ.comp.joint.createForAssemblyContext(occ)
    msg: str
        Tell the status
        
    Returns
    ----------
    joints_dict: 
        {name: {type, axis, upper_limit, lower_limit, parent, child, xyz}}
    msg: str
        Tell the status
    """

    joint_type_list = [
    'fixed', 'revolute', 'prismatic', 'Cylinderical',
    'PinSlot', 'Planner', 'Ball']  # these are the names in urdf

    joints_dict = {}
    
    joint_dict = {}
    joint_type = joint_type_list[joint.jointMotion.jointType]
    joint_dict['type'] = joint_type
    joint_dict['name'] = joint.name
    
    # swhich by the type of the joint
    joint_dict['axis'] = [0, 0, 0]
    joint_dict['upper_limit'] = 0.0
    joint_dict['lower_limit'] = 0.0
    
    # support  "Revolute", "Rigid" and "Slider"
    if joint_type == 'revolute':
        joint_dict['axis'] = [round(i / 100.0, 6) for i in \
            joint.jointMotion.rotationAxisVector.asArray()]  # converted to meter
        max_enabled = joint.jointMotion.rotationLimits.isMaximumValueEnabled
        min_enabled = joint.jointMotion.rotationLimits.isMinimumValueEnabled            
        if max_enabled and min_enabled:  
            joint_dict['upper_limit'] = round(joint.jointMotion.rotationLimits.maximumValue, 6)
            joint_dict['lower_limit'] = round(joint.jointMotion.rotationLimits.minimumValue, 6)
        elif max_enabled and not min_enabled:
            msg = joint.name + 'is not set its lower limit. Please set it and try again.'
#            break
        elif not max_enabled and min_enabled:
            msg = joint.name + 'is not set its upper limit. Please set it and try again.'
#            break
        else:  # if there is no angle limit
            joint_dict['type'] = 'continuous'
            
    elif joint_type == 'prismatic':
        joint_dict['axis'] = [round(i / 100.0, 6) for i in \
            joint.jointMotion.slideDirectionVector.asArray()]  # converted to meter
        max_enabled = joint.jointMotion.slideLimits.isMaximumValueEnabled
        min_enabled = joint.jointMotion.slideLimits.isMinimumValueEnabled            
        if max_enabled and min_enabled:  
            joint_dict['upper_limit'] = round(joint.jointMotion.slideLimits.maximumValue/100, 6)
            joint_dict['lower_limit'] = round(joint.jointMotion.slideLimits.minimumValue/100, 6)
        elif max_enabled and not min_enabled:
            msg = joint.name + 'is not set its lower limit. Please set it and try again.'
#            break
        elif not max_enabled and min_enabled:
            msg = joint.name + 'is not set its upper limit. Please set it and try again.'
#            break
    elif joint_type == 'fixed':
        pass
    
    if joint.occurrenceTwo.component.name == 'base_link':
        joint_dict['parent'] = 'base_link'
        joint_dict['parent_key'] = 'base_link'
    else:
        joint_dict['parent'] = utils_binary.get_valid_filename(joint.occurrenceTwo.fullPathName)
        joint_dict['parent_key'] = re.sub('[ :()]', '_', joint.occurrenceTwo.fullPathName)
    joint_dict['child'] = utils_binary.get_valid_filename(joint.occurrenceOne.fullPathName)
    joint_dict['child_key'] = re.sub('[ :()]', '_', joint.occurrenceOne.fullPathName)
    
    try:
        joint_dict['xyz'] = [round(i / 100.0, 6) for i in \
        joint.geometryOrOriginOne.origin.asArray()]  # converted to meter
    except:
        try:
            if type(joint.geometryOrOriginTwo)==adsk.fusion.JointOrigin:
                data = joint.geometryOrOriginTwo.geometry.origin.asArray()
            else:
                data = joint.geometryOrOriginTwo.origin.asArray()
            joint_dict['xyz'] = [round(i / 100.0, 6) for i in data]  # converted to meter
        except:
            msg = joint.name + " doesn't have joint origin. Please set it and run again."
#            break
    
    key = joint_dict['child_key'] + '---' + joint.name
    joints_dict[key] = joint_dict
    return joints_dict, msg