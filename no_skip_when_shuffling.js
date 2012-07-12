/* no_skip_when_shuffling.js
 *
 * Copyright 2007 Ryan Barrett
 * http://snarfed.org/windows_itunes_script_to_unset_skip_when_shuffling
 *
 * An iTunes for Windows script that turns off the "skip when shuffling" and
 * "remember playback position" settings, found in the Options tab of the Info
 * window. iTunes turns these on by default for new podcasts when they're
 * downloaded, which prevents Autofill from filling them onto an iPod.
 *
 * Uses the Windows Scripting Host and iTunes' COM bindings for Windows.
 *
 * Inspired by this AppleScript, which does the same thing:
 *
 * http://www.macosxhints.com/article.php?story=20070218041737189
 *
 * Apple's original site for the iTunes for Windows COM SDK has disapeared:
 *
 * http://developer.apple.com/sdk/itunescomsdk.html
 *
 * ...so I used this page (from Microsoft, no less!), which was invaluable:
 *
 * http://www.microsoft.com/technet/scriptcenter/funzone/tunes.mspx
 *
 * You can also still find iTunesCOMInterface.h on code search engines like
 * koders, vizkit, and google code search:
 *
 * http://www.google.com/codesearch?hl=en&q=+iTunesCOMInterface.h+show:tuaQ8-JRruc:VCewQzHOoTs:OeYmnRoCpzg&sa=N&cd=3&ct=rc&cs_p=svn://svn.berlios.de/mgoodies/trunk&cs_f=listeningto/players/iTunesCOMInterface.h#a0
 *
 * More info:
 * http://ottodestruct.com/blog/2005/10/20/itunes-javascripts/
 * http://dougscripts.com/itunes/itinfo/windowshelp.php
 *
 * http://mutable.net/blog/archive/2006/11/30/How-to-schedule-iTunes-to-download-Podcasts-on-Windows.aspx
 * http://www.macosxhints.com/article.php?story=20060731010250960
 */

var playlist_name = "Podcasts for iPod";
var iTunes = WScript.CreateObject("iTunes.Application");

// update podcasts
iTunes.UpdatePodcastFeeds();

// let them download
var fs = WScript.CreateObject("Scripting.FileSystemObject");
do {
  WScript.Sleep(60000);  // ms
} while (fs.FolderExists("C:\\Documents and Settings\\ryanb\\My Documents\\My Music\\iTunes\\iTunes Music\\Downloads\\Podcasts"))

// unset "skip when shuffling"
var sources = iTunes.Sources;
var playlists = sources.ItemByName("Library").Playlists;
var playlist = playlists.ItemByName(playlist_name);
var tracks = playlist.Tracks;

for (i = 1; i <= tracks.Count; i++) {
//     WScript.echo(tracks.Item(i).Name)
    tracks.Item(i).ExcludeFromShuffle = false;
//    tracks.Item(i).RememberBookmark = false;
}

WScript.Echo("Done!");

// autofill ipod
//
// ...this just *syncs* the iPod. it doesn't autofill it. looks like there's no
// way to autofill an iPod through the COM interface. grr!!!
// ipod = sources.ItemByName("Ryan's Shuffle");
// WScript.echo(ipod.toString())
// ipod.UpdateIPod();
