#!/bin/bash

INSTALL_FOLDER=/opt/homemetrics

uid=$(id -u)

if [[ $uid != 0 ]]; then
  echo "Please run as root"
fi

if [ -d "$INSTALL_FOLDER" ]; then
  echo "Cleaning $INSTALL_FOLDER first"
  rm -rf $INSTALL_FOLDER
fi

mkdir -p $INSTALL_FOLDER
echo "Copying files to $INSTALL_FOLDER"
cp *.py $INSTALL_FOLDER/

echo "Creating virtualenv"
virtualenv -p python3 $INSTALL_FOLDER

cd $INSTALL_FOLDER/
source ./bin/source

echo "Installing requirements"
pip install requirements.text

deactivate

echo "Copying systemd files:"
cp systemd/pusher.service /etc/systemd/system/
