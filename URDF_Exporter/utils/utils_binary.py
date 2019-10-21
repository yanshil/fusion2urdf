# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 17:25:30 2019

@author: yanshil
"""

#https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-ECA8A484-7EDD-427D-B1E3-BD59A646F4FA

import adsk, adsk.core, adsk.fusion
import os.path, re
from xml.etree import ElementTree
from xml.dom import minidom

## https://github.com/django/django/blob/master/django/utils/text.py
def get_valid_filename(s):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def create_stl_export_component(root):    
    """
    duplicate all occurences as a new component
        1. Extract all occurences (regardless of the level)
        2. Create a new component in root to store the occurence
            * name = re.sub(occ.name)
            * origin component name = old_component
        3. Copy the rigid body from origin to new component
    """    
    def copy2root(Occurs, occ):
        """    
        copy the old occ to new component
        """
        bodies = occ.bRepBodies
        ## Initialized as an identity matrix and is created statically using the Matrix3D.create method.
        transform = adsk.core.Matrix3D.create()
        
        # Create new components from occ
        # This support even when a component has some occes. 
        new_occs = Occurs.addNewComponent(transform)  # this create new occs
        if occ.component.name == 'base_link':
            occ.component.name = 'old_component'
            new_occs.component.name = 'base_link'
        else:
            new_occs.component.name = occs.fullPathName
        new_occs = Occurs[-1]
        for i in range(bodies.count):
            body = bodies.item(i)
            body.copyToComponent(new_occs)
    
    ## All occurences with nested structure
    allOccs = root.allOccurrences
    oldOccs = []
    coppy_list = [occs for occs in allOccs]
    for occs in coppy_list:
        if occs.bRepBodies.count > 0:
            copy2root(root.occurrences, occs)
            oldOccs.append(occs)

    for occs in oldOccs:
        occs.component.name = 'old_component'


def deleteOldComponent(design): 
    root = design.rootComponent
    components = design.allComponents

    componentsToDelete = []  
    for component in components:
        #if len(component.bRepBodies) == 0:
        if 'old_component' in component.name:
            componentsToDelete.append(component)

    for component in componentsToDelete:
        # Get the name first because deleting the final Occurrence will delete the Component.
        name = component.name

        # Build a list of unique immediate occurrences of the component.
        occurrences = root.allOccurrencesByComponent(component)
        for occurrence in occurrences:
            occurrence.deleteMe()


def export_stl(design, save_dir):  
    """
    export stl files into "save_dir/"
    
    
    Parameters
    ----------
    design: adsk.fusion.Design.cast(product)
    save_dir: str
        directory path to save
    """
    # get root component in this design
    root = design.rootComponent

    # create a single exportManager instance
    exportMgr = design.exportManager
    # get the script location
    try: os.mkdir(save_dir + '/mm_stl')
    except: pass
    scriptDir = save_dir + '/mm_stl'

    allOccus = root.occurrences

    # # export the occurrence one by one in the component to a specified file
    # for component in components:
    #     allOccus = component.allOccurrences
    for occ in allOccus:
        if 'old_component' not in occ.component.name:
            try:
                ## Filename cannot contain "\/:*?<>"
                fileName = scriptDir + "/" + get_valid_filename(occ.component.name)
                # create stl exportOptions
                stlExportOptions = exportMgr.createSTLExportOptions(occ, fileName)
                stlExportOptions.sendToPrintUtility = False
                stlExportOptions.isBinaryFormat = False
                # options are .MeshRefinementLow .MeshRefinementMedium .MeshRefinementHigh
                stlExportOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementLow
                exportMgr.execute(stlExportOptions)
            except:
                print('Component ' + occ.fullPathName + 'has something wrong.')
                

def file_dialog(ui):     
    """
    display the dialog to save the file
    """
    # Set styles of folder dialog.
    folderDlg = ui.createFolderDialog()
    folderDlg.title = 'Fusion Folder Dialog' 
    
    # Show folder dialog
    dlgResult = folderDlg.showDialog()
    if dlgResult == adsk.core.DialogResults.DialogOK:
        return folderDlg.folder
    return False


def origin2center_of_mass(inertia, center_of_mass, mass):
    """
    convert the moment of the inertia about the world coordinate into 
    that about center of mass coordinate


    Parameters
    ----------
    moment of inertia about the world coordinate:  [xx, yy, zz, xy, yz, xz]
    center_of_mass: [x, y, z]
    
    
    Returns
    ----------
    moment of inertia about center of mass : [xx, yy, zz, xy, yz, xz]
    """
    x = center_of_mass[0]
    y = center_of_mass[1]
    z = center_of_mass[2]
    translation_matrix = [y**2+z**2, x**2+z**2, x**2+y**2,
                         -x*y, -y*z, -x*z]
    return [ round(i - mass*t, 6) for i, t in zip(inertia, translation_matrix)]


def prettify(elem):
    """
    Return a pretty-printed XML string for the Element.
    Parameters
    ----------
    elem : xml.etree.ElementTree.Element
    
    
    Returns
    ----------
    pretified xml : str
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

