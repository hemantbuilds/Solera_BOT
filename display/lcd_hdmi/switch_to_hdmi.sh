#!/bin/bash
sudo sed -i 's/^dtoverlay=waveshare/#dtoverlay=waveshare/' /boot/config.txt
sudo sed -i 's/^#hdmi_force_hotplug/hdmi_force_hotplug/' /boot/config.txt
sudo sed -i 's/^#hdmi_group/hdmi_group/' /boot/config.txt
sudo sed -i 's/^#hdmi_mode/hdmi_mode/' /boot/config.txt
sudo reboot
