# fusion2urdf

Developed from [@syuntoku14/fusion2urdf](https://github.com/syuntoku14/fusion2urdf)

### What is this script?

A Fusion 360 script to export urdf files. This is a PyBullet adpative version.  **CURRENTLY NOT SUPPORT NESTED COMPONENT** 

This exports:

* .urdf files of the model
* .stl files of your model
* A example hello.py to load your model into PyBullet.

### Fusion Add-in
Add this script into Fusion 360 via Tools -> Add-Ins

<img src="https://github.com/yanshil/fusion2urdf/blob/images/addin.png" alt="addin" title="Fusion Add-in" width="300" height="300">

#### Before using this script

1. Some other notes for getting avoid of warnings: 
   1. Change language preference to English
   2. Rename any full-width symbol to half-width symbol (like `。` and `（）`)
2. Set up `base_link`
3. Nested components are not supported by the exporter. Tidy the nested components by `Decpature Deisign history` , split components and reset all links

#### Using script inside Fusion 360: Example

1. Set up the compoenents properly

- [x] A base_link

- [x] Check component and joint names (Set English as the language if necessary)

- [x] Set up joints properly
	
	* In fusion, when you hit 'J' to assemble joints, note that the exporter consider **component 1 as 'child' and component 2 as 'parent'**. For example, when you want to assemble a 4-wheel car with middle cuboid as `base_link`, you should assemble the vehicle with wheel as component 1 and 'base_link' as component 2.

	* For example, you should be assemble your model to make result of `check_urdf simple_car.urdf`  like the following. i.e. BL, BR, FL, FR as component 1 and base_link as component 2 when you assemble these 4 joints.
	```
    robot name is: simple_car
	  ---------- Successfully Parsed XML ---------------
	  root Link: base_link has 4 child(ren)
	      child(1):  BL_1
	      child(2):  BR_1
	      child(3):  FL_1
	      child(4):  FR_1
	```

2. Run the script and select storing location
   * Note: **Don't save** your file after running the scripts! Some temporary "old component" will be created
   * <img src="https://github.com/yanshil/fusion2urdf/blob/images/2.png" alt="2" title="outputs" width="300" height="300">
   * <img src="https://github.com/yanshil/fusion2urdf/blob/images/files.png" alt="files" title="files" width="300" height="300">
3. Enjoy from `python hello_bullet.py` !

