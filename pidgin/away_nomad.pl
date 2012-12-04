#!/usr/bin/perl -w
##
## File: away_nomad.pl
## Author: Ryan Barrett (rbarrett@stanford.edu)
##

## This is a Perl plugin for Gaim. It allows me to IM myself from a different
## screen name - specifically, "nomadblaize" - to set "bl4ize"'s away message.
## It registers a callback that is called when I receive an IM. The callback
## checks whether the sender is "nomadblaize", and if it is, the callback sets
## my away message to the message that "nomadblaize" sent.
##

require 5.004;
#use strict;


## registers this plugin with GAIM
GAIM::register("remote away setter", ".1", "", "");

## registers set_away_msg as a callback to be called when any account receives
## an IM
GAIM::add_event_handler("event_im_recv", "set_away_msg");


## set_away_msg
##
## The meat of this plugin. set_away_msg is registered as an event handler for
## the event_away event.
sub set_away_msg {
	my ($account, $from, $msg) = @_;

#	print $account . "\n" . $from . "\n" . $msg .  "\n\n";

	if (($from eq "nomad blaize") || ($from eq "nomadblaize")) {
		GAIM::command("away", $msg);
	}
}
