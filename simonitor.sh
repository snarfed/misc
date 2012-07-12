#!/bin/bash
#
# simonitor.sh
# http://snarfed.org/simonitor
# Ryan Barrett <simonitor@ryanb.org>
# This script is in the public domain.
#
# Fetches the current balance of one or more Simon gift cards, scrapes the
# resulting HTML, and prints the balance to stdout. Simon uses a CAPTCHA,
# so the user is shown the CAPTCHA images and asked to enter its text.
#
# Usage: simonitor.sh CARDNUMBER/CCV [CARDNUMBER/CCV ...]
#
#
# DEVELOPMENT NOTES
# ===
# I've used the Live HTTP Headers Firefox plugin to help debug and update
# recent versions of this when Simon changes their web site. It's a huge help:
#
# http://livehttpheaders.mozdev.org/
#
# It's never required the User-Agent field before, but occasionally when it
# breaks and I can't figure out why, I think it's started. I've never been able
# to get the quoting right in this script using the --user-agent flag to set a
# user agent with spaces, but putting this in .curlrc works:
#
# user-agent="Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.12) Gecko/20101027 Ubuntu/10.04 (lucid) Firefox/3.6.12"
#
# Originally I needed to store cookies across http requests:
#
# COOKIE_FILE=/tmp/simonitor_cookie.jar
# CURL_ARGS="--cookie-jar $COOKIE_FILE --cookie $COOKIE_FILE --silent --show-error --insecure"
#
# ...and then at the top of the loop:
# 
# rm -f $COOKIE_FILE
#
# Here are some other params it accepts but doesn't require.
#
# __EVENTTARGET=&__EVENTARGUMENT=&
# &ctl00%24ctl09%24EmailAddressPassword=&ctl00%24RSCOverlay1%24RSCOverlayMode=Live&ctl00%24RSCOverlay1%24RSCOverlayModeId=0&EmailLogin=&PasswordLogin=&RememberMeCheckbox=on
# &${FIELD_PREFIX}regNumber=&${FIELD_PREFIX}regCid=&${FIELD_PREFIX}actNumber=&${FIELD_PREFIX}actCid=&${FIELD_PREFIX}actPhone=&q=
#
# See simonitor_headers for more example data.


if [ $# == 0 -o "$1" == "-h" -o "$1" == "--help" ]; then
  echo "Fetches the current balance of one or more Simon gift cards."
  echo 
  echo "Usage: `basename $0` CARDNUMBER/CCV [CARDNUMBER/CCV ...]"
  exit
fi

# simon.com runs on IIS, which requires a valid __VIEWSTATE parameter.
# evidently it's a base64-encoded struct. it doesn't look like it's actually
# used for anything, but it still needs to be there. %2B is the url encoding
# for +, %2F for /, %3D for =. see http://www.w3schools.com/tags/ref_urlencode.asp.
#
# when Simon changes their web site, this usually needs to be updated.
VIEWSTATE=%2FwEPDwUKMTA2OTI1NTI4MA9kFgJmD2QWAgIDD2QWAgIDD2QWCgIDDw8WAh4GTW9kZUlkZmRkAgUPZBYEAgEPFgIeB1Zpc2libGVnZAIDDw8WAh8BZ2RkAgcPZBYCZg8WAh8BZxYCAgEPDxYCHgtOYXZpZ2F0ZVVybAUwaHR0cDovL3d3dy5zaW1vbi5jb20vZ2lmdGNhcmQvZGVmYXVsdC5hc3B4P3JzYz1mZGQCCQ9kFgYCAQ9kFgICAQ8WAh4LXyFJdGVtQ291bnQCAhYEAgEPZBYCAgEPDxYIHwIFDS9kZWZhdWx0LmFzcHgeBFRleHQFBEhvbWUeCENzc0NsYXNzBQVmaXJzdB4EXyFTQgICZGQCAg9kFgICAQ8PFggfAgUMamF2YXNjcmlwdDo7HwQFCkdpZnQgQ2FyZHMfBQUHY3VycmVudB8GAgJkZAIDD2QWBmYPFgIfAWdkAgEPDxYCHwIFJi9naWZ0Y2FyZC9vcmRlcl9idWlsZC5hc3B4P3BhY2thZ2U9MjMyZBYCZg8PFgIeCEltYWdlVXJsBTcvZ2lmdGNhcmQvaW1hZ2VzL2NhcmRsYXJnZS9BTUVYX0dpbmdlcmJyZWFkXzIxNngxMzcucG5nZGQCAg88KwAJAQAPFgYeDVJlcGVhdENvbHVtbnMCBx4IRGF0YUtleXMWAB8DAg5kFhxmD2QWAgIBDw8WBB8CBR5%2BL29yZGVyX2J1aWxkLmFzcHg%2FcGFja2FnZT0xOTEeB1Rvb2xUaXAFIEFtZXJpY2FuIEV4cHJlc3MgQ29yZSAtIFN1bmJ1cnN0ZBYCZg8PFgIfBwUsL2dpZnRjYXJkL2ltYWdlcy9jYXJkdGh1bWJzL2FtZXhfY29yZV9zbS5qcGdkZAIBD2QWAgIBDw8WBB8CBR5%2BL29yZGVyX2J1aWxkLmFzcHg%2FcGFja2FnZT0xOTMfCgUeQW1lcmljYW4gRXhwcmVzcyAtIENlbGVicmF0aW9uZBYCZg8PFgIfBwUuL2dpZnRjYXJkL2ltYWdlcy9jYXJkdGh1bWJzL0FNRVhQcmVzZW50X3NtLnBuZ2RkAgIPZBYCAgEPDxYEHwIFHn4vb3JkZXJfYnVpbGQuYXNweD9wYWNrYWdlPTE5NR8KBRlBbWVyaWNhbiBFeHByZXNzIC0gU3VtbWVyZBYCZg8PFgIfBwUtL2dpZnRjYXJkL2ltYWdlcy9jYXJkdGh1bWJzL0FNRVhTdW1tZXJfc20ucG5nZGQCAw9kFgICAQ8PFgQfAgUefi9vcmRlcl9idWlsZC5hc3B4P3BhY2thZ2U9MTk3HwoFIkFtZXJpY2FuIEV4cHJlc3MgLSAgUHJlbWl1bSBPdXRsZXRkFgJmDw8WAh8HBS4vZ2lmdGNhcmQvaW1hZ2VzL2NhcmR0aHVtYnMvQU1FWF9vdXRsZXRfc20ucG5nZGQCBA9kFgICAQ8PFgQfAgUefi9vcmRlcl9idWlsZC5hc3B4P3BhY2thZ2U9MjMzHwoFHUFtZXJpY2FuIEV4cHJlc3MgLSBDYW5keSBDYW5lZBYCZg8PFgIfBwU0L2dpZnRjYXJkL2ltYWdlcy9jYXJkdGh1bWJzL0FNRVhfQ2FuZHljYW5lXzYweDM4LnBuZ2RkAgUPZBYCAgEPDxYEHwIFHn4vb3JkZXJfYnVpbGQuYXNweD9wYWNrYWdlPTIzNR8KBRpBbWVyaWNhbiBFeHByZXNzIC0gTWVub3JhaGQWAmYPDxYCHwcFMi9naWZ0Y2FyZC9pbWFnZXMvY2FyZHRodW1icy9BTUVYX01lbm9yYWhfNjB4MzgucG5nZGQCBg9kFgICAQ8PFgQfAgUefi9vcmRlcl9idWlsZC5hc3B4P3BhY2thZ2U9MjAwHwoFEVNpbW9uIFBpbmsgUmliYm9uZBYCZg8PFgIfBwUpL2dpZnRjYXJkL2ltYWdlcy9jYXJkdGh1bWJzL3N1c2Fua19zbS5naWZkZAIHD2QWAgIBDw8WBB8CBR5%2BL29yZGVyX2J1aWxkLmFzcHg%2FcGFja2FnZT0xOTIfCgUbQW1lcmljYW4gRXhwcmVzcyAtIEJpcnRoZGF5ZBYCZg8PFgIfBwUrL2dpZnRjYXJkL2ltYWdlcy9jYXJkdGh1bWJzL0FNRVhDYWtlX3NtLnBuZ2RkAggPZBYCAgEPDxYEHwIFHn4vb3JkZXJfYnVpbGQuYXNweD9wYWNrYWdlPTE5NB8KBRhBbWVyaWNhbiBFeHByZXNzIC0gSGVhcnRkFgJmDw8WAh8HBSwvZ2lmdGNhcmQvaW1hZ2VzL2NhcmR0aHVtYnMvQU1FWEhlYXJ0X3NtLnBuZ2RkAgkPZBYCAgEPDxYEHwIFHn4vb3JkZXJfYnVpbGQuYXNweD9wYWNrYWdlPTE5Nh8KBRtBbWVyaWNhbiBFeHByZXNzIC0gU3RhbmZvcmRkFgJmDw8WAh8HBTAvZ2lmdGNhcmQvaW1hZ2VzL2NhcmR0aHVtYnMvQU1FWF9zdGFuZm9yZF9zbS5wbmdkZAIKD2QWAgIBDw8WBB8CBR5%2BL29yZGVyX2J1aWxkLmFzcHg%2FcGFja2FnZT0yMzIfCgUeQW1lcmljYW4gRXhwcmVzcyAtIEdpbmdlcmJyZWFkZBYCZg8PFgIfBwU2L2dpZnRjYXJkL2ltYWdlcy9jYXJkdGh1bWJzL0FNRVhfR2luZ2VyYnJlYWRfNjB4MzgucG5nZGQCCw9kFgICAQ8PFgQfAgUefi9vcmRlcl9idWlsZC5hc3B4P3BhY2thZ2U9MjM0HwoFGkFtZXJpY2FuIEV4cHJlc3MgLSBTbm93bWFuZBYCZg8PFgIfBwUyL2dpZnRjYXJkL2ltYWdlcy9jYXJkdGh1bWJzL0FNRVhfU25vd21hbl82MHgzOC5wbmdkZAIMD2QWAgIBDw8WBB8CBR5%2BL29yZGVyX2J1aWxkLmFzcHg%2FcGFja2FnZT0xOTgfCgUOU2ltb24gR2lmdGNhcmRkFgJmDw8WAh8HBTcvZ2lmdGNhcmQvaW1hZ2VzL2NhcmR0aHVtYnMvR2lmdGNhcmRVU0JhbmtfdGJfNjB4MzgucG5nZGQCDQ9kFgICAQ8PFgQfAgUefi9vcmRlcl9idWlsZC5hc3B4P3BhY2thZ2U9MTk5HwoFFEZvcnVtIFNob3BzIEdpZnRjYXJkZBYCZg8PFgIfBwU2L2dpZnRjYXJkL2ltYWdlcy9jYXJkdGh1bWJzL0dpZnRjYXJkRm9ydW1fdGJfNjB4MzgucG5nZGQCBw9kFgYCCA8PFgIeC1Bvc3RCYWNrVXJsBTBodHRwczovL3d3dy5zaW1vbi5jb20vZ2lmdGNhcmQvY2FyZF9iYWxhbmNlLmFzcHhkZAIODw8WAh8LBTRodHRwczovL3d3dy5zaW1vbi5jb20vZ2lmdGNhcmQvYWNjb3VudF9yZWdpc3Rlci5hc3B4ZGQCFw8PFgIfCwU0aHR0cHM6Ly93d3cuc2ltb24uY29tL2dpZnRjYXJkL2FjY291bnRfYWN0aXZhdGUuYXNweGRkAgsPZBYGZg9kFgJmDw8WAh8LBQEvZGQCAg8PFgIfAWdkZAIDDw8WAh8BZ2RkGAEFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYDBSpjdGwwMCRGdWxsQ29udGVudCRjdGwwMyRjaGVja0JhbGFuY2VTdWJtaXQFJmN0bDAwJEZ1bGxDb250ZW50JGN0bDAzJHJlZ2lzdGVyU3VibWl0BSZjdGwwMCRGdWxsQ29udGVudCRjdGwwMyRhY3RpdmF0ZVN1Ym1pdFE4m9TYgVfZCcx7T%2Ft8%2F4nKaAHO

CURL_ARGS='--silent --show-error --insecure'

for CC in $*; do
  # extract comment (if any) and parse credit card number and CCV
  CC_PARSED=${CC%%#*}
  CC_NUM=`echo $CC_PARSED | grep -o -e '^[0-9]\{15,16\}'`
  CC_CID=`echo $CC_PARSED | grep -o -e '[0-9]\{3,4\}$'`
  if [[ $CC_NUM == "" || $CC_CID == "" ]]; then
    echo "Invalid card number or CCV: $CC"
    continue
  fi


  # GET the form page and the recaptcha image
  RECAPTCHA_K=`curl ${CURL_ARGS} \
                 https://www.simon.com/giftcard/card_balance.aspx | \
                 egrep -o "https://www.google.com/recaptcha/api/challenge\?k=[^&']+"`
  RECAPTCHA_C=`curl -L ${CURL_ARGS} $RECAPTCHA_K | \
                 egrep -o "challenge : '[^']+" | \
                 cut -c 14-`
  CAPTCHAFILE=`mktemp /tmp/simonitor_captcha.XXXXXX` || exit 1
  curl -L --output $CAPTCHAFILE ${CURL_ARGS} https://www.google.com/recaptcha/api/image?c=${RECAPTCHA_C}
  xloadimage $CAPTCHAFILE > /dev/null &
  XLOADIMAGE_PID="$!"

  # ask for the captcha
  read -e -p "Enter the captcha string: " CAPTCHA
  CAPTCHA=`echo $CAPTCHA | tr ' ' +`

  # erase the prompt w/ANSI escape codes. [1A moves the cursor up a line, [0K
  # erases the line. see http://www.answers.com/topic/ansi-escape-code .
  # ...never mind, this doesn't work in emacs shells.
  # echo -ne '\e[1A\e[0K'

  # POST to the form. note that %24 is the url encoding for the $ character.
  TMPFILE=`mktemp /tmp/simonitor_out.XXXXXX` || exit 1
  FIELD_PREFIX=ctl00%24FullContent%24ctl03%24
  if ( ! curl --output $TMPFILE $CURL_ARGS \
         --data "__VIEWSTATE=${VIEWSTATE}&__PREVIOUSPAGE=4-dZCmGaD91563GruBwLxk-bnZ3BkrV6Zcez_7aDpju0nm10FgRi5JZj50L-tr_w7PbfSsr-9YKYRdnLVZ8jVPdxh841&returnUrl=http%3A%2F%2Fwww.simon.com%3A80%2Fgiftcard%2Fdefault.aspx&${FIELD_PREFIX}ccNumber=${CC_NUM}&${FIELD_PREFIX}ccCid=${CC_CID}&recaptcha_challenge_field=${RECAPTCHA_C}&recaptcha_response_field=${CAPTCHA}&${FIELD_PREFIX}checkBalanceSubmit.x=0&${FIELD_PREFIX}checkBalanceSubmit.y=0" \
         https://www.simon.com/giftcard/card_balance.aspx); then
    continue
  fi

  # scrape the address, expiration date, and balance
  BALANCE=`egrep -o 'lblBalance">[^<]+' $TMPFILE | sed 's/lblBalance">//'`
  EXPDATE=`egrep -o 'lblExpDate">[^<]+' $TMPFILE | sed 's/lblExpDate">//'`
  echo "$CC: $BALANCE, expires $EXPDATE"

  NAME=`egrep -o 'lblPersonName">[^<]*' $TMPFILE | sed 's/lblPersonName">//'`
  CITY_STATE_ZIP=`egrep -o 'lblPersonAddress">[^<]*(<br>[^<]*)*' $TMPFILE \
                  | sed 's/lblPersonAddress">//' \
                  | sed 's/<br>/ /' | sed 's/<br>/ /' | sed 's/<br>/ /'`
  if [ "$NAME $CITY_STATE_ZIP" != " " ]; then
    echo "                      $NAME  $CITY_STATE_ZIP"
  fi

  shred -u $TMPFILE $CAPTCHAFILE
  if [[ $XLOADIMAGE_PID != "" ]]; then
    kill $XLOADIMAGE_PID
  fi
done
