#!/bin/bash
# Script to enable both HDMI and LCD displays simultaneously on Raspberry Pi

# Backup the current config.txt
echo "Backing up /boot/config.txt..."
sudo cp /boot/config.txt /boot/config_backup.txt

# Enable HDMI and LCD configuration
echo "Configuring /boot/config.txt for dual display..."
sudo bash -c 'cat << EOF >> /boot/config.txt

# Dual display configuration
dtoverlay=vc4-kms-v3d
enable_dpi_lcd=1
display_default_lcd=1
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=82
framebuffer_priority=2

# LCD settings (Replace with your LCD-specific overlay)
dtoverlay=waveshare35a
dpi_group=2
dpi_mode=87
dpi_output_format=0x6f005
dpi_timings=480 0 48 40 32 320 0 13 2 10 0 0 0 60 0 19200000 6

EOF'

# Restart display services
echo "Restarting display services..."
sudo systemctl restart lightdm || sudo systemctl restart display-manager

# Reboot to apply changes
echo "Configuration completed. Rebooting the system..."
sudo reboot
