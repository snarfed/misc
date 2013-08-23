#!/bin/bash
#
# Sync my home dir, music, and pictures onto my phone. Based on backup.sh.
#
# Mac OS X: don't know. have to use Android File Transfer? So no way to sync?
#
# Linux: For Nexus 4, run:
# sudo mtpfs -o allow_other /media/usb0
#
# more: http://www.theandroidsoul.com/how-to-mount-nexus-4-on-linux-for-transferring-files/
#
#
# Old instructions for Nexus S:
# This *was* run automatically when the phone was connected to USB using udev. See
# udev(7) and http://reactivated.net/writing_udev_rules.html .
# (I first tried https://help.ubuntu.com/community/UsbDriveDoSomethingHowto
# but it wasn't quite enough.)
#
# First, I edited /etc/usbmount/usbmount.conf and added vfat to FILESYSTEMS and
# -fstype=vfat,uid=XXXX,gid=XXXX,utf8,dmask=027,fmask=137,shortname=winnt to
# FS_MOUNTOPTIONS so that usbmount would automatically mount and unmount the
# phone on /media/usb0 when it's plugged and unplugged. look up uid and gid in
# /etc/passwd and /etc/group. shortname=winnt tells it to be smarter about case
# sensitivity. details in the mount(8) man page.
#
# Use id(1) to find uid and gid.
#
# If usbmount doesn't take effect right away, run sudo mount /dev/sdb.
#
# Then, I added /etc/udev/rules.d/z99_ryanb_sync_phone.rules with this one line:
#
# SUBSYSTEMS=="usb", ATTRS{manufacturer}=="Google, Inc.", ATTRS{product}=="Nexus One", ATTRS{serial}=="...", RUN+="/home/ryanb/bin/sync_phone_wrapper.sh"
#
# If I wasn't using usbmount, I'd need this:
# mount -t vfat ${DDEVNAME} /media/usb0 -o uid=1000,gid=100,utf8,dmask=027,fmask=137

TARGET=/media/usb0

# --delete means delete files in dest that aren't in source. also note this
# uses the default behavior for symlinks, ie ignore them.
#
# from man rsync:
# In particular, when transferring to or from an MS Windows FAT filesystem
# (which represents times with a 2-second resolution), --modify-window=1 is
# useful (allowing times to differ by up to 1 second).
RSYNC="nice rsync $@ -rtv --inplace --cvs-exclude --modify-window=1 --progress"

# # mount
# sudo mtpfs -o allow_other $TARGET

# # OLD FOR NEXUS S:
# # use mount's sync option so i can see progress more easily during big writes
# # like the rsyncs below.
# sudo mount -o uid=5520,gid=5000,utf8,dmask=027,fmask=137,shortname=winnt,sync \
#   /dev/sdb /media/usb0

# DEPRECATED. i now use BotSync on the phone to backup to snarfed over the network.
#
# backup stuff from the phone to my computer. note that i *don't* pass --delete
# to rsync. i want to preserve old sms and call log backups.
# $RSYNC -z --checksum ~/usb/{{SMS,CallLog}BackupRestore,DCIM/Camera} \
#     ~ryanb/phone_backup

# sync

# # note that a / suffix on a source dir means copy the *contents* of the dir
# # into the target dir; if the / suffix is missing, it means copy the dir itself
# # into the target dir, recursively. (rsync is recursive by default.)
# #
# # i tried to unify the binary/image extension excludes here and in the next
# # rsync, but couldn't get bash to brace expand inside variables. :/
# $RSYNC --exclude=voicemail_* --exclude=credit* --exclude=id{_,entity}* \
#   --exclude=mail/ --exclude=*.{blogpost,bz2,zip,gif,gpg,jpeg,jpg,pdf,png} \
#   --checksum --delete --delete-excluded ~ryanb/{etc,src/snarfed} $TARGET

# sync

# # # music. changes rarely, but takes a long time to compute hashes.
# # this is for everything:
# # $RSYNC -k --delete --update --size-only --exclude=*.{bz2,gpg,jpg,jpeg,gif,png,zip} \
# #   ~/phone/music/ $TARGET/Music

# # this is for just the symlinks in music/phone/:
# $RSYNC --copy-links --update --delete --delete-excluded --size-only \
#   --exclude=*.{bz2,gpg,jpg,jpeg,gif,png,zip} \
#   ~/music/phone/ $TARGET/Music

# sync

# pictures. only sync galleries from the past 2 years that are on snarfed.
QUERY='SELECT DISTINCT path FROM wp_ngg_gallery \
  INNER JOIN wp_ngg_pictures ON gid = galleryid'
  # WHERE imagedate > NOW() - INTERVAL 2 YEAR;'
INCLUDE=`mysql -u snarfed --silent --raw -e "$QUERY" snarfed \
  | sed 's/wp-content\/gallery\///g'`
  # | sed 's/wp-content\/gallery/--include=/g'`

cd ~/pictures
$RSYNC --update --size-only --delete --delete-excluded --exclude=thumbs/ \
  $INCLUDE $TARGET/Pictures
  # $INCLUDE --include=/{2400_diamond,cats,draw_group}/ \

sync
