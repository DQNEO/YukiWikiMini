#!/usr/bin/perl
#
# YukiWikiMini Version 1.0.2
#
# ykwkmini.cgi - Yet another WikiWikiWeb clone.
#
# Copyright (C) 2000,2001,2003,2004 by Hiroshi Yuki.
# <hyuki@hyuki.com>
# http://www.hyuki.com/yukiwiki/
#
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.
#
##############################
use strict;
my $dbname = 'ykwkmini';
my $thisurl = 'ykwkmini.cgi';
my $frontpage = 'FrontPage';
my $indexpage = 'Index';
my $errorpage = 'Error';
my $WikiName = '([A-Z][a-z]+([A-Z][a-z]+)+)';
my $kanjicode = 'sjis';
my $editchar = '?';
my $bgcolor = 'white';
my $contenttype = 'Content-type: text/html; charset=Shift_JIS';
my $naviwrite = 'Write';
my $naviedit = 'Edit';
my $naviindex = 'Index';
my $msgdeleted = ' is deleted.';
my $cols = 80;
my $rows = 20;
my $style = <<'EOD';
<style type="text/css">
<!--
body { font-family: "Courier New", monospace; }
pre { line-height:130%; }
a { text-decoration: none }
a:hover { text-decoration: underline }
-->
</style>
EOD
##############################
my %form;
my %database;

require 'jcode.pl';
&main;
exit(0);

sub main {
    &init_form;
    &sanitize_form;
    foreach (keys %form) {
        if (/^($WikiName)$/) {
            $form{mycmd} = 'read';
            $form{mypage} = $1;
            last;
        }
    }
    unless (dbmopen(%database, $dbname, 0666)) {
        &print_error("(dbmopen)");
    }
    $_ = $form{mycmd};
    if (/^read$/) {
        &do_read;
    } elsif (/^write$/) {
        &do_write;
    } elsif (/^edit$/) {
        &do_edit;
    } elsif (/^index$/) {
        &do_index;
    } else {
        $form{mypage} = $frontpage;
        &do_read;
    }
    dbmclose(%database);
}

sub do_read {
    &print_header($form{mypage}, 1);
    &print_content;
    &print_footer;
}

sub do_edit {
    &print_header($form{mypage}, 0);
    my $mymsg = &escape($database{$form{mypage}});
    print <<"EOD";
    <form action="$thisurl" method="post">
        <input type="hidden" name="mycmd" value="write">
        <input type="hidden" name="mypage" value="$form{mypage}">
        <input type="submit" value="$naviwrite"><br />
        <textarea cols="$cols" rows="$rows" name="mymsg" wrap="off">$mymsg</textarea><br />
        <input type="submit" value="$naviwrite">
    </form>
EOD
    &print_footer;
}

sub do_index {
    &print_header($indexpage, 0);
    print qq|<ul>\n|;
    foreach (sort keys %database) {
        print qq|<li><a href="$thisurl?$_"><tt>$_</tt></a></li>\n|
    }
    print qq|</ul>\n|;
    &print_footer;
}

sub do_write {
    if ($form{mymsg}) {
        $database{$form{mypage}} = $form{mymsg};
        &print_header($form{mypage}, 1);
        &print_content;
    } else {
        delete $database{$form{mypage}};
        &print_header($form{mypage} . $msgdeleted, 0);
    }
    &print_footer;
}

sub print_error {
    my $msg = shift;
    &print_header($errorpage, 0);
    print "<h1>$msg</h1>";
    &print_footer;
    exit(0);
}

sub print_header {
    my ($title, $canedit) = @_;
    print <<"EOD";
$contenttype

<html>
    <head><title>$title</title>$style</head>
    <body bgcolor="$bgcolor">
        <table width="100%" border="0">
            <tr valign="top">
                <td>
                    <h1>$title</h1>
                </td>
                <td align="right">
                    <a href="$thisurl?$frontpage">$frontpage</a> | 
                    @{[$canedit ? qq(<a href="$thisurl?mycmd=edit&mypage=$form{mypage}">$naviedit</a> | ) : '' ]}
                    <a href="$thisurl?mycmd=index">$naviindex</a> | 
                    <a href="http://www.hyuki.com/yukiwiki/mini/">YukiWikiMini</a>
                </td>
            </tr>
        </table>
EOD
}

sub print_footer {
    print "</body></html>";
}

sub escape {
    my $s = shift;
    $s =~ s|\r\n|\n|g;
    $s =~ s|\r|\n|g;
    $s =~ s|\&|&amp;|g;
    $s =~ s|<|&lt;|g;
    $s =~ s|>|&gt;|g;
    $s =~ s|"|&quot;|g;
    return $s;
}

sub print_content {
    $_ = &escape($database{$form{mypage}});
    s!
        (
            ((mailto|http|https|ftp):[\x21-\x7E]*)  # Direct http://...
                |
            ($WikiName)                             # LocalLinkLikeThis
        )
    !
        &make_link($1)
    !gex;
    print "<pre>", $_, "</pre>";
}

sub make_link {
    $_ = shift;
    if (/^(http|https|ftp):/) {
        return qq|<a href="$_">$_</a>|;
    } elsif (/^(mailto):(.*)/) {
        return qq|<a href="$_">$2</a>|;
    } elsif ($database{$_}) {
        return qq|<a href="$thisurl?$_">$_</a>|;
    } else {
        return qq|$_<a href="$thisurl?mycmd=edit&mypage=$_">$editchar</a>|;
    }
}

sub init_form {
    my ($query);
    if ($ENV{REQUEST_METHOD} =~ /^post$/i) {
        read(STDIN, $query, $ENV{CONTENT_LENGTH});
    } else {
        $query = $ENV{'QUERY_STRING'};
    }
    my @assocarray = split(/&/, $query);
    foreach (@assocarray) {
        my ($property, $value) = split /=/;
        $value =~ tr/+/ /;
        $value =~ s/%([A-Fa-f0-9][A-Fa-f0-9])/pack("C", hex($1))/eg;
        &jcode'convert(\$value, $kanjicode);
        $form{$property} = $value;
    }
}

sub sanitize_form {
    if (defined($form{mypage}) and $form{mypage} !~ /^$WikiName$/) {
        &print_error("(invalid mypage)");
    }
}
