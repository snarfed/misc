#!/usr/bin/perl -w
##
## File: awaybot.pl
## Author: Ryan Barrett (rbarrett@stanford.edu)
##

## This is a Perl plugin for Gaim. Its goal is to automate the management of my
## AIM away message, so that it's correct more often without needing me to set
## it all the time.
##
## Features
## - I can IM "bl4ize" from a different screen name - specifically,
## "nomadblaize" - to set "bl4ize"'s away message. It registers a callback that
## is called when I receive an IM. The callback checks whether the sender is
## "nomadblaize", and if it is, the callback sets my away message to the
## message that "nomadblaize" sent.
##
## - When "nomadblaize" signs on, "bl4ize" sets its away msg to "at work", and
## when "nomadblaize" signs off, "bl4ize" sets its away message to "on the
## train" (if it's btw sunday and thursday) or "out for the night" (if it's
## friday or saturday)

require 5.004;
use strict;


## registers this plugin with GAIM
my $handle = GAIM::register("AwayBot", "0.3", "", "");
my $last = "";

sub description {
    my($a, $b, $c, $d, $e, $f) = @_;
    ("AwayBot",
     "0.3",
     "Automates away message management with some nifty tools and heuristics",
     "Ryan Barrett (ryan at barrett dot name)",
     "http://ryan.barrett.name/",
     "/dev/null");
}


## register callbacks
GAIM::add_event_handler($handle, "event_im_recv", "set_away_msg");
GAIM::add_event_handler($handle, "event_buddy_signon", "buddy_signon");
#GAIM::add_event_handler($handle, "event_buddy_back", "buddy_signon");

## set_away_msg
##
## Called when bl4ize receives a message. If the sender is nomadblaize, set the
## away message to the im text.
sub set_away_msg {
    my ($account, $from, $msg) = @_;

#    print $account . "\n" . $from . "\n" . $msg .  "\n\n";

    if (is_proxy($account, $from)) {
        GAIM::command("away", $msg);
        $last = $msg;
    }
}


## buddy_signon
##
## Called when a buddy signs on. If it's the proxy, set bl4ize's away message
## to "at work".
sub buddy_signon {
    my ($account, $who) = @_;

    if (is_proxy($account, $who)) {
        GAIM::command("away", "at work");
    }
}


## buddy_away
##
## Called when a buddy goes away. If it's the proxy, mirror his away message.
##
## Sigh...this can't work, since it doesn't give me the away message. It's
## really only the first two parameters, not all three.
#sub buddy_away {
#    my ($account, $who, $msg) = @_;

#    if (is_proxy($account, $who)) {
#        my ($a, $b, $c, $d, $e, $f, $g, $h) = GAIM::user_info(2, "nomadblaize");
#        GAIM::print($a . $b . $c . $d . $e . $f . $g . $h);
#        GAIM::command("away", $msg);
#    }
#}
    

## buddy_signoff
##
## Called when a buddy signs off. If it's the proxy, set bl4ize's away message
## to the last, non-"at work" away message.
##
sub buddy_signoff {
    my ($account, $who) = @_;

    if (is_proxy($account, $who)) {
        GAIM::command("away", $last);
    }
}


## is_proxy
##
## Returns true if the given account is the master account and the buddy name
## is the proxy's screen name, false otherwise.
sub is_proxy {
    my ($account, $buddy_name) = @_;

#    GAIM::print("debug", "account " . $account . ", buddy " . $buddy . "\n");

    return (is_name($account, "bl4ize") &&
            ($buddy_name eq "nomad blaize") || ($buddy_name eq "nomadblaize"));
}


## is_name
##
## Returns true the screen name (or ICQ UIN or whatever) from a Gaim account
## matches the name parameter, false otherwise.
sub is_name {
    my ($account, $name) = @_;

    return (GAIM::get_info(3, $account) eq $name);
}
