#!/bin/bash

if [ "$1" != "" ]; then
    find $1 -type f -print0 | xargs -0 dos2unix
	bash stl2binary.bash $1
	cp ../../../Fusion2Pybullet/example/*.py ./$1/
	sed -i 's/robot.urdf/$1.urdf/g' $1/*.py
else
    echo "Please include the folder name."
fi

