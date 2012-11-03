#!/bin/bash
#
# connect_to_wap.sh takes a list of WAP SSIDs as command line arguments and
# connects to the one with the strongest signal.

if [ $# == 0 ]; then
    echo Usage: connect_to_wap.sh SSID...
    exit
fi

echo Connecting to "$@"...



# this nmcli command line prints output like this:
#
# 29:'HRGuest1'
# 59:'HRGuest2'
# 17:'HRAP1'
nmcli --terse --escape no --fields signal,ssid dev wifi \
   | sort --numeric-sort --reverse \
   | grep -e STATE: need to join args w/| here
   | head -n 1 \
   | cut -d "'" -f 2 \
   | xargs nmcli con up id



# all of this below extracts the BSSID for a given SSID. i wrote it before i
# realized you could pass a NM connection name with `nmcli con up id`.

# LINE=`nmcli --terse --escape no --fields signal,ssid,bssid dev wifi \
#   | sort --numeric-sort --reverse \
#   | grep --max-count 1 "$1"`

# if [[ "$LINE" == "" ]]; then
#     echo not found.
#     exit
# fi

# # extract BSSID from end. it's six pairs of hex digits separated by colons, e.g.
# # C0:83:0A:B2:95:61, so 17 chars from the end.
# BSSID=${LINE: -17}

