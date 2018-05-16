#!/usr/bin/env bash


mkdir -p ./_package/bin
mkdir ./_package/pycalc
cp -r ./pycalc/* ./_package/pycalc/
cp ./main.py ./_package/bin/pycalc
chmod +x ./_package/bin/pycalc
cp ./setup.py ./_package/
cd ./_package/
tar cf ../package.tar *
cd ..
rm -rf ./_package/
echo "OK"
