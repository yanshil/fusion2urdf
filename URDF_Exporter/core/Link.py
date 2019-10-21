# -*- coding: utf-8 -*-
"""
Modified on Wed Oct 16 12:52:21 2019

@author: syuntoku
@yanshil
"""

import adsk, re
from xml.etree.ElementTree import Element, SubElement
from ..utils import utils_binary

class Link:

    def __init__(self, key, name, xyz, center_of_mass, repo, mass, inertia_tensor):
        """
        Parameters
        ----------
        key: str
            full path of the link
        name: str
            name of the link (Also the name of stl files)
        xyz: [x, y, z]
            coordinate for the visual and collision
        center_of_mass: [x, y, z]
            coordinate for the center of mass
        link_xml: str
            generated xml describing about the link
        repo: str
            the name of the repository to save the xml file
        mass: float
            mass of the link
        inertia_tensor: [ixx, iyy, izz, ixy, iyz, ixz]
            tensor of the inertia
        """
        self.key = key
        self.name = name
        # xyz for visual
        self.xyz = [-_ for _ in xyz]  # reverse the sign of xyz
        # xyz for center of mass
        self.center_of_mass = center_of_mass
        self.link_xml = None
        self.repo = repo
        self.mass = mass
        self.inertia_tensor = inertia_tensor
        
    def make_link_xml(self):
        """
        Generate the link_xml and hold it by self.link_xml
        """
        
        link = Element('link')
        link.attrib = {'name':self.key}     ## Unique among the design
        
        #inertial
        inertial = SubElement(link, 'inertial')
        origin_i = SubElement(inertial, 'origin')
        origin_i.attrib = {'xyz':' '.join([str(_) for _ in self.center_of_mass]), 'rpy':'0 0 0'}       
        mass = SubElement(inertial, 'mass')
        mass.attrib = {'value':str(self.mass)}
        inertia = SubElement(inertial, 'inertia')
        inertia.attrib = \
            {'ixx':str(self.inertia_tensor[0]), 'iyy':str(self.inertia_tensor[1]),\
            'izz':str(self.inertia_tensor[2]), 'ixy':str(self.inertia_tensor[3]),\
            'iyz':str(self.inertia_tensor[4]), 'ixz':str(self.inertia_tensor[5])}        
        
        # visual
        visual = SubElement(link, 'visual')
        origin_v = SubElement(visual, 'origin')
        origin_v.attrib = {'xyz':' '.join([str(_) for _ in self.xyz]), 'rpy':'0 0 0'}
        geometry_v = SubElement(visual, 'geometry')
        mesh_v = SubElement(geometry_v, 'mesh')
        mesh_v.attrib = {'filename':'package://' + self.repo + self.name + '_m-binary.stl'}
        #mesh_v.attrib = {'filename': self.repo + self.name + '.stl'}
        material = SubElement(visual, 'material')
        material.attrib = {'name':'silver'}
        color = SubElement(material, 'color')
        color.attrib = {'rgba':'1 0 0 1'}
        
        # collision
        collision = SubElement(link, 'collision')
        origin_c = SubElement(collision, 'origin')
        origin_c.attrib = {'xyz':' '.join([str(_) for _ in self.xyz]), 'rpy':'0 0 0'}
        geometry_c = SubElement(collision, 'geometry')
        mesh_c = SubElement(geometry_c, 'mesh')
        mesh_c.attrib = {'filename':'package://' + self.repo + self.name + '_m-binary.stl'}
        #mesh_c.attrib = {'filename': self.repo + self.name + '.stl'}

        # print("\n".join(utils_binary.prettify(link).split("\n")[1:]))
        self.link_xml = "\n".join(utils_binary.prettify(link).split("\n")[1:])


def make_inertial_dict(root, msg):
    """      
    Parameters
    ----------
    root: adsk.fusion.Design.cast(product)
        Root component
    msg: str
        Tell the status
        
    Returns
    ----------
    inertial_dict: {name:{mass, inertia, center_of_mass}}
    
    msg: str
        Tell the status
    """
    # Get ALL component properties.      
    allOccs = root.allOccurrences
    inertial_dict = {}
    
    for occs in allOccs:
        # Skip the root component.
        occs_dict = {}
        prop = occs.getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
        mass = round(prop.mass, 6)  #kg
        center_of_mass = [round(_ / 100.0, 6) for _ in prop.centerOfMass.asArray()]
        occs_dict['center_of_mass'] = center_of_mass
        inertia_world = [i / 10000.0 for i in \
            prop.getXYZMomentsOfInertia()[1:]]  #kg m^2
        # xx yy zz xy xz yz(default)
        inertia_world[4], inertia_world[5] = inertia_world[5], inertia_world[4]
        occs_dict['mass'] = mass
        occs_dict['inertia'] = utils_binary.origin2center_of_mass(inertia_world, center_of_mass, mass)  
        
        ## TODO: Use occ.GetComponentName
        ## Set up Occ name and key
        if occs.component.name == 'base_link':
            occs_dict['name'] = 'base_link'
            inertial_dict['base_link'] = occs_dict
        else:
            occs_dict['name'] = utils_binary.get_valid_filename(occs.fullPathName)
            inertial_dict[re.sub('[ :()]', '_', occs.fullPathName)] = occs_dict

    return inertial_dict, msg