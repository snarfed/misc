#!/usr/bin/perl -w
##
## File: away_sender.pl
## Author: Ryan Barrett (rbarrett@stanford.edu)
##
## This is a Perl plugin for Gaim. Its goal is to automate the management of my
## AIM away message, so that it's correct more often without needing me to set
## it all the time.
##
## This one sends a message to the master (bl4ize) when its away message is set.

require 5.004;
use strict;


## registers this plugin with GAIM
my $handle = GAIM::register("AwaySender", "0.1", "", "");
my $master = "bl4ize";
my $last_away = "";

sub description {
    my($a, $b, $c, $d, $e, $f) = @_;
    ("AwaySender",
     "0.1",
     "When an account goes away, it sends its away message in an IM to the " .
     "master screen name.",
     "Ryan Barrett (ryan at barrett dot name)",
     "http://ryan.barrett.name/",
     "/dev/null");
}


## register callbacks
GAIM::add_event_handler($handle, "event_away", "send_away_msg");

## send_away_msg
sub send_away_msg {
    my ($account, $away_msg) = @_;

    if (is_proxy(GAIM::get_info(3, $account))) {
#        GAIM::print("changing", $away_msg . " => " . $last_away);
        $last_away = $away_msg;
        GAIM::serv_send_im($account, $master, $away_msg);
    }
}


## is_proxy
##
## Returns true if the given string matches the proxy screen name,
## false otherwise.
sub is_proxy {
    my ($name) = @_;

#    GAIM::print("asdf", "checking " . $name);
    return (($name eq "nomad blaize") || ($name eq "nomadblaize"));
}
