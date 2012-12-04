#!/usr/bin/perl -w
##
## File: test.pl
## Author: Ryan Barrett (rbarrett@stanford.edu)
##

## This is a Perl plugin for Gaim. It's purely for diagnostic/debugging.

require 5.004;
use strict;


## registers this plugin with GAIM
my $handle = GAIM::register("Tester", "0.0", "", "");

sub description {
    my($a, $b, $c, $d, $e, $f) = @_;
    ("Tester",
     "0.0",
     "Prints diagnostics on some signals",
     "Ryan Barrett (ryan at barrett dot name)",
     "http://ryan.barrett.name/",
     "/dev/null");
}


## register callbacks
#GAIM::add_event_handler($handle, "event_im_recv", "im_recv");
#GAIM::add_event_handler($handle, "event_buddy_away", "buddy_away");
#GAIM::add_event_handler($handle, "event_buddy_back", "buddy_back");
#GAIM::add_event_handler($handle, "event_buddy_signon", "buddy_signon");
#GAIM::add_event_handler($handle, "event_buddy_signoff", "buddy_signoff");

GAIM::add_event_handler($handle, "event_away", "away");
GAIM::add_event_handler($handle, "event_signon", "signon");
GAIM::add_event_handler($handle, "event_signoff", "signoff");

sub im_recv {
    my ($account, $from, $msg) = @_;
    GAIM::print("im_recv " . $account . " " . $from . " " . $msg);
}

sub buddy_away {
    my ($account, $who, $msg) = @_;
    GAIM::print("buddy_away " . $account . " " . $who . " " . $msg);
}

sub buddy_back {
    my ($account, $who) = @_;
    GAIM::print("buddy_back " . $account . " " . $who);
}

sub buddy_signon {
    my ($account, $who) = @_;
    GAIM::print("buddy_signon " . $account . " " . $who);
}

sub buddy_signoff {
    my ($account, $who) = @_;
    GAIM::print("buddy_signoff " . $account . " " . $who);
}

sub away {
    my ($account, $msg) = @_;
    GAIM::print("away " . $account . " " . $msg);
}

sub signon {
    my ($account) = @_;
    GAIM::print("signon " . $account);
}

sub signoff {
    my ($account) = @_;
    GAIM::print("signoff " . $account);
}

