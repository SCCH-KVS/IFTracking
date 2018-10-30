#!/bin/bash
cd ./components/generator/src
python setup.py build_ext --inplace 
cd ../../..

cd ./components/preprocessor/modules/linassign
python setup.py build_ext --inplace
cd ../../../..

cd ./components/tracker/modules/fpattern/
python setup.py build_ext --inplace
cd ..

cd ./vfsampler/
python setup.py build_ext --inplace
cd ../../../..


