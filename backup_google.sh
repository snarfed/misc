#!/usr/local/bin/bash
#
# http://snarfed.org/backup_google
#
# Dump as much of my data in google services as I can.
# See https://www.google.com/dashboard/ for a full list.

if [ $# -lt 3 ]; then
  echo "Backs up data from Google Contacts, Calendar, Reader, and Tasks."
  echo 
  echo "Usage: `basename $0` backup_google.sh EMAIL PASSWORD DIR"
  exit 1
fi

EMAIL=$1
PASSWD=$2
BASEDIR=$3
mkdir -p ${BASEDIR}
cd ${BASEDIR}


# uses ClientLogin to get an Auth header value. details:
# http://code.google.com/apis/accounts/docs/AuthForInstalledApps.html#Request
# service names: http://code.google.com/apis/gdata/faq.html#clientlogin
# (calendar is cl, reader is reader, gmail is mail, etc.)
# takes one positional arg, the service name.
function auth () {
  CLIENTLOGIN=`/usr/local/bin/curl https://www.google.com/accounts/ClientLogin -s \
    -d Email=$EMAIL \
    -d Passwd=$PASSWD \
    -d accountType=GOOGLE \
    -d service=$1`
  # note that ${CLIENTLOGIN} will convert newlines to spaces
  SID=`echo ${CLIENTLOGIN} | egrep -o '^SID=[^ ]+' | cut -c 5-`
  AUTH=`echo ${CLIENTLOGIN} | egrep -o Auth=.+ | cut -c 6-`
  
  if [ "${AUTH}" == "" -o "${SID}" == "" ]; then
    echo 'Error logging in. Got this from ClientLogin:'
    echo "${CLIENTLOGIN}"
    exit 1
  fi
}

# short circuit and exit if any command fails
set -e

CURL="/usr/local/bin/curl -L -s --fail"

# this is one auth alternative, it pulls cookies from firefox, which will work as
# long as i've logged into my google account in firefox recently.
#
# ~/src/misc/export_firefox_cookies.py \
#   ~/.mozilla/firefox/default.???/cookies.sqlite /tmp/cookies.txt
#
# another auth alternative would be just to take everything from android
# phone, since it syncs all of this data from all of these services. see
# etc/android_manual_backup_with_adb.html.


# Calendar. (The old way was the private ICS URLs for each calendar. Those are
# available in the settings page for each calendar.)
auth cl
${CURL} -H "Authorization:GoogleLogin auth=${AUTH}" \
  http://www.google.com/calendar/exporticalzip > calendars.zip


# Reader. Download the OPML.
auth reader
${CURL} -H "Authorization:GoogleLogin auth=${AUTH}" \
  http://www.google.com/reader/subscriptions/export \
  > reader_subscriptions.opml.xml


# Contacts. Found this endpoint with the firefox Live HTTP Headers plugin.
# (Old way was to pass SID cookie to this URL:
# http://www.google.com/contacts/c/data/export?groupToExport=%5EMine&exportType=ALL&out=VCARD )
auth cp
${CURL} -H "Authorization:GoogleLogin auth=${AUTH}" \
  https://www.google.com/m8/feeds/contacts/default/full?maxresults=999999 \
  > contacts.xml


# Tasks.
# now via the API, yay!
#
# Old scraping version was based on
# http://privacylog.blogspot.com/2010/09/updated-google-tasks-api.html
auth goanna_mobile
DATA=`${CURL} -H "Authorization:GoogleLogin auth=${AUTH}" \
  https://mail.google.com/tasks/m`

# Old way:
# # this is r={"action_list":[{"action_type":"get_all","action_id":"2","get_deleted":true,"date_start":"1969-12-31","get_archived":true}],"client_version":12566865}
# DATA=`${CURL} --header "AT: 1" \
#   --data 'r=%7B%22action_list%22%3A%5B%7B%22action_type%22%3A%22get_all%22%2C%22action_id%22%3A%222%22%2C%22get_deleted%22%3Atrue%2C%22date_start%22%3A%221969-12-31%22%2C%22get_archived%22%3Atrue%7D%5D%2C%22client_version%22%3A12566865%7D' \
#   https://mail.google.com/tasks/r/d`

# extract the list ids. they're of the form:
#   04291589652955054844:0:0
IDS=`echo ${DATA} | egrep -o '[0-9]+:[0-9]+:0' | uniq`

rm -f tasks.json
touch tasks.json

for id in ${IDS}; do
  # this is:
  # r={"action_list":[{"action_type":"get_all","action_id":"10","list_id":"04291589652955054844:4:0","get_deleted":false,"date_start":"1969-12-31","get_archived":true}],"client_version":12566865}
  ${CURL} -H "Authorization:GoogleLogin auth=${AUTH}" --header 'AT: 1' --data r=%7B%22action_list%22%3A%5B%7B%22action_type%22%3A%22get_all%22%2C%22action_id%22%3A%2210%22%2C%22list_id%22%3A%22${id}%22%2C%22get_deleted%22%3Afalse%2C%22date_start%22%3A%221969-12-31%22%2C%22get_archived%22%3Atrue%7D%5D%2C%22client_version%22%3A12566865%7D \
    https://mail.google.com/tasks/r/d \
    >> tasks.json
done

# here's a simpler alternative. i'm not using it since it returns HTML. this
# describes how to parse it:
# http://privacylog.blogspot.com/2010/09/updated-google-tasks-api.html

# ${CURL}  -H "Authorization:GoogleLogin auth=${AUTH}" \
#   "https://mail.google.com/tasks/m?listid=${id}" \


# TODO: Docs. Complicated HTTP request pattern.

# POST http://docs.google.com/export-status
# archiveId=...&token=...&version=4&tzfp=...&tzo=480&subapp=4&app=2&clientUser=...&hl=en
# ...
# TODO: gmail filters, with filter export/import labs feature.
# http://groups.google.com/group/gmail-labs-help-filter-import-export/

