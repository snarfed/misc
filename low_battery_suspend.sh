#!/bin/bash
#
# acpid action script that suspends if the battery is low. based on:
# http://mindspill.net/computing/linux-notes/acpi/acpi-low-battery-warning.html
                                                                               
# Location of acpi files.
PROC=/proc/acpi/battery/BAT0
CURRENT=`grep -E '^remaining capacity:' $PROC/state | tr -s ' ' | cut -d' ' -f3`
LOW=`grep -E '^design capacity low:' $PROC/info | tr -s ' ' | cut -d' ' -f4`
CHARGING=`grep -E '^charging state:' $PROC/state | tr -s ' ' | cut -d' ' -f3`

if [[ $CHARGING == "discharging" && $CURRENT -lt $LOW ]]; then
  pm-suspend-hybrid
fi 
