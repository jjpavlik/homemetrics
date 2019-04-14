#!/bin/bash

INSTALL_FOLDER=/opt/homemetrics

uid=$(id -u)

if [[ $uid != 0 ]]; then
  echo "Please run as root"
  exit 1
fi

if [ -d "$INSTALL_FOLDER" ]; then
  echo "Cleaning $INSTALL_FOLDER first, leaving log files."
  for i in `ls $INSTALL_FOLDER | grep -v ".log"`; do
    rm -rf $INSTALL_FOLDER/$i
  done
fi

mkdir -p $INSTALL_FOLDER
echo "Copying files to $INSTALL_FOLDER"
cp *.py $INSTALL_FOLDER/
cp requirements.txt $INSTALL_FOLDER/
cp -pr systemd $INSTALL_FOLDER/
cp *.conf $INSTALL_FOLDER/
cp *.sh $INSTALL_FOLDER/
cp arduino.ino $INSTALL_FOLDER/
chmod +x $INSTALL_FOLDER/*.sh

echo "Creating virtualenv"
virtualenv -p python3 $INSTALL_FOLDER

cd $INSTALL_FOLDER/
source ./bin/activate

echo "Installing requirements"
pip install -r requirements.txt

deactivate

echo "Copying systemd files:"
cd $INSTALL_FOLDER/
cp systemd/pusher.service /etc/systemd/system/
cp systemd/collector.service /etc/systemd/system/
