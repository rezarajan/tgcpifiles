cd /opt/openagbrain && sudo service rc.local stop && sudo mv venv /opt && sudo rm -r * && sudo git clone https://github.com/OpenAgInitiative/openag-device-software.git . && sudo git checkout pfc3-rack-20-test && sudo mv /opt/venv . && sudo touch data/config/device.txt && sudo chmod 777 data/config/device.txt && sudo echo "pfc3-v0.3.0" > data/config/device.txt && cd scripts && sudo ./upgrade.sh