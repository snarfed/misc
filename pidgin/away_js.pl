#!/usr/bin/perl -w
##
## File: away_js.pl
## Author: Ryan Barrett (rbarrett@stanford.edu)
##
## This is a Perl plugin for Gaim. It registers a callback that is called when
## any active account sets an away message or returns from away. It discards the
## first call to the callback (this is from my ICQ account - Gaim doesn't send
## the away message correctly for ICQ accounts), then writes the away message
## given in the second callback into a JavaScript function in the file
## specified by kaway_js_file.
##
## If the away message is the empty string, this means that the account is
## returning from away. In this case, the string "Online" is written to the
## JavaScript function.
##

require 5.004;
#use strict;


## registers this plugin with GAIM
my $handle = GAIM::register("Away writer", "0.3", "", "");

sub description {
	my($a, $b, $c, $d, $e, $f) = @_;
	("Away writer",
	 "0.3",
	 "Writes my away message to a javascript file",
	 "Ryan Barrett (rbarrett at stanford dot edu)",
	 "http://ryan.barrett.name",
	 "/dev/null");
}


## registers write_away_msg as a callback to be called when any account sets an
## away message or returns from away
GAIM::add_event_handler($handle, "event_away", "write_away_msg");
GAIM::add_event_handler($handle, "event_signon", "write_signon");
GAIM::add_event_handler($handle, "event_signoff", "write_signoff");

my $ssh_cmd = "ssh -i /home/ryanb/.ssh/id_rsa_backup snarfed.org /home/rbarrett/bin/write_away_msg.sh ";

write_away_msg();


## write_signon
##
sub write_signon {
    my ($account) = @_;
    write_away_msg($account, "Online");
}

## write_signoff
##
sub write_signoff {
    my ($account) = @_;
    write_away_msg($account, "Offline");
}

## write_away_msg
##
## The meat of this plugin. write_away_msg is registered as an event handler for
## the event_away event.
sub write_away_msg {
	my ($account, $away_msg) = @_;

#    my $accountname = "bl4ize";
    my $accountname = GAIM::get_info(3, $account);
    if ($accountname ne "bl4ize") {
        return;
    }

	# if the away message is blank, then i'm returning from away
	if ($away_msg eq "") {
		$away_msg = "Online";
	}

    my $cmd = $ssh_cmd . $away_msg;
    system($cmd);
#    if (system($cmd) != 0) {
#        my $msg = "error $? running $cmd";
#        open(MAIL, '| mail -s away_js.pl ryan@barrett.name');
#        print MAIL $msg;
#        close(MAIL);
#        die $msg;
#    }
}
