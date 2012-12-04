#!/usr/bin/perl
# BlockAOLSystemMsg plugin tested on Pidgin 2.5.5. Put in ~/.purple/plugins/ and enable
#
# downloaded on 3/24/2010 from
# http://biodegradablegeek.com/2009/05/how-to-block-aims-annoying-aol-system-msg-in-pidgin/
use Purple;
our $target = 'AOL System Msg'; # case-insensitive
our $plugin_name = 'Block AOLSystemMsg'; 

%PLUGIN_INFO = (
  perl_api_version => 2,
  name => $plugin_name,
  version => "0.1",
  summary => "Blocks the screen name 'AOL System Msg'",
  description => "Ignore annoying 'your SN has signed on at 2 locations' AIM message",
  author => "Isam ",
  url => "http://biodegradablegeek.com",
  load => "plugin_load",
  unload => "plugin_unload"
);

sub loginfo { Purple::Debug::info($plugin_name, " @_\n"); }
sub minimize {
  my $r = lc($_[0]);
  $r =~ s/ //g;
  return $r;
}

sub plugin_init { return %PLUGIN_INFO; }

sub plugin_load {
  my $plugin = shift;
  $target = minimize($target);
  loginfo("Sight set on '$target'");
  Purple::Signal::connect(Purple::Conversations::get_handle(),
                          'receiving-im-msg', $plugin, \&callback, '');
}

sub plugin_unload {
  my $plugin = shift;
  loginfo('Block AOLSystemMsg Unloaded.');
}

sub callback {
  my ($acc, $sender, $msg, $flags) = @_;
  if (minimize($sender) eq $target) {
    loginfo("(BLOCKED) <$sender> $msg");
    return 1
  };
}
