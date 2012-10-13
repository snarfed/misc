#!/bin/bash
#
# Reapply my customizations that puppet override. :P Must be run as root.

# disable gdm
# also do sudo goobuntu-config set custom_grub_conf yes
sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=".*"$/GRUB_CMDLINE_LINUX_DEFAULT="text"/' \
  /etc/default/grub
update-grub

# disable idle timeout enforced by timeoutd
# truncate --size=0 /etc/timeouts
# service timeoutd restart

# don't require password for sudo
sed -i '/^%sudo *ALL.*/d' /etc/sudoers
echo '%sudo ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers.cmd_policy.include 
visudo -c

# disable bluetooth (?)
# add this to the end of /etc/rc.local:
# echo disable > /proc/acpi/ibm/bluetooth

# X settings that may have been reset
xhost +
xset b off
xset -dpms
xset s off

# Let www-data (apache) through the firewall
iptables -I ufw-after-output 4 --match owner --uid-owner www-data -j ACCEPT
iptables -I ufw-after-output 5 --match owner --uid-owner postfix -j ACCEPT

sed -i 's/^-A ufw-after-output -m owner --uid-owner googleadmin -j ACCEPT$/&\n-A ufw-after-output -m owner --uid-owner www-data -j ACCEPT\n-A ufw-after-output -m owner --uid-owner postfix -j ACCEPT/' \
  /etc/ufw/after.rules
