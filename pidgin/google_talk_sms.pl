#!/usr/bin/perl -w
##
## File: google_talk_sms.pl
## Author: Ryan Barrett <pidgin@ryanb.org>
##
## This is a Perl plugin for Pidgin that works around Google Talk's restriction
## of its SMS feature to official clients by by reporting that Pidgin supports
## the 'sms-v1' and 'sms-v2' XMPP capabilities (XEP-0115) extensions.
##
## Details in http://snarfed.org/space/google_talk_sms+pidgin+plugin
##
## Thanks to Michael Braun's Perl plugin for XEP-0027 (encryption), which
## provided a great example of how to use pidgin's xmlnode data structure in
## Perl: https://www.zuhauseall.homeip.net/~michael/pidgin-xep0027/

use strict;
use Purple;

our %PLUGIN_INFO = (
    perl_api_version => 2,
    name => "Google Talk SMS",
    version => "0.4",
    summary => "Enables Google Talk's SMS feature, which is normally restricted to official clients.",
    description => "Works around Google Talk's restriction of its SMS feature to official clients by reporting that Pidgin supports the 'sms-v1' and 'sms-v2' XMPP capabilities (XEP-0115) extensions.",
    author => "Ryan Barrett <pidgin\@ryanb.org>",
    url => "http://snarfed.org/space/google_talk_sms+pidgin+plugin",
    load => "plugin_load",
    unload => "plugin_unload"
);

sub plugin_init {
    return %PLUGIN_INFO;
}

sub plugin_load {
    my $plugin = shift;
    my $jabber = Purple::Find::prpl("prpl-jabber");
    Purple::Signal::connect($jabber, "jabber-sending-xmlnode", $plugin,
                            \&jabber_sending_xmlnode_cb, "unused userdata");
}

sub plugin_unload {
    my $plugin = shift;
}

sub jabber_sending_xmlnode_cb {
    my ($connection, $xmlnode, $userdata) = @_;

    my $c = $xmlnode->get_child("c");
    if (not defined($c)) {
        return;
    }

    my $ext = $c->get_attrib("ext");
    if (not defined($c)) {
        $ext = "";
    }
    $c->set_attrib("ext", $ext . " sms-v1 sms-v2");

    $_[1] = $xmlnode;
}
