#!/usr/local/bin/bash
#
# Backup my tweets.
# Background: https://dev.twitter.com/docs/api/1/get/statuses/user_timeline
#
# I used to use TwitterExport.php from
# http://www.adamfranco.com/2008/10/13/twitter-export-script/
#
# Note that the output JSON is ugly, no whitespace and all on a single line. Use
# json_pp(1) to prettify it.

set -e

# for seq
PATH=${PATH}:/usr/local/bin
CURL="curl --silent --fail --show-error"
DIR=${HOME}/backup
mkdir -p ${DIR}

for username in snarfed_org; do
  FILE=${DIR}/tweets_${username}.json

  # find id of last tweet in backup
  since_id=`grep -m 1 -o -E '"id":([0-9]+{15,99})' $FILE |head -n 1 | cut -c6-`

  # get tweets since then and insert at beginning
  truncate -s 0 ${FILE}.new
  $CURL "https://api.twitter.com/1/statuses/user_timeline.json?screen_name=${username}&count=200&since_id=${since_id}" > ${FILE}.new
  cat ${FILE} >> ${FILE}.new
  mv -f ${FILE}.new ${FILE}
done
