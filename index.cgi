#!/usr/bin/env perl
use strict;
use warnings;
use CGI;
our $VERSION = "1.1.1";
my $dbname = 'ykwkmini';
my $frontpage = 'FrontPage';
my $indexpage = 'Index';
my $errorpage = 'Error';
my $WikiName = '([A-Z][a-z]+([A-Z][a-z]+)+)';
my $editchar = '?';
my $bgcolor = 'white';
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

my $q = CGI->new;
&main;
exit(0);

sub main {
    &sanitize_form;

    if (defined $q->Vars->{keywords} && $q->Vars->{keywords} =~ /^($WikiName)$/) {
        $q->Vars->{mycmd} = 'read';
        $q->Vars->{mypage} = $1;
    }

    unless (dbmopen(%database, $dbname, 0666)) {
        &print_error("(dbmopen)");
    }
    $_ = $q->Vars->{mycmd};
    if (! $_) {
        $q->Vars->{mypage} = $frontpage;
        &do_read;
    } elsif (/^read$/) {
        &do_read;
    } elsif (/^write$/) {
        &do_write;
    } elsif (/^edit$/) {
        &do_edit;
    } elsif (/^index$/) {
        &do_index;
    } else {
        $q->Vars->{mypage} = $frontpage;
        &do_read;
    }
    dbmclose(%database);
}

sub do_read {
    &print_header($q->param("mypage"), 1);
    &print_content;
    &print_footer;
}

sub do_edit {
    &print_header($q->param("mypage"), 0);
    my $mymsg = &escape($database{$q->param("mypage")});
    $mymsg = "" unless defined $mymsg;
    my $mypage = $q->param("mypage");

    print <<"EOD";
    <form action="." method="post">
        <input type="hidden" name="mycmd" value="write">
        <input type="hidden" name="mypage" value="$mypage">
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
        print qq|<li><a href="?$_"><tt>$_</tt></a></li>\n|
    }
    print qq|</ul>\n|;
    &print_footer;
}

sub do_write {
    if ($q->Vars->{mymsg}) {
        $database{$q->param("mypage")} = $q->Vars->{mymsg};
        &print_header($q->param("mypage"), 1);
        &print_content;
    } else {
        delete $database{$q->param("mypage")};
        &print_header($q->param("mypage") . $msgdeleted, 0);
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
    my $mypage = $q->param("mypage");
    print <<"EOD";
Content-type: text/html; charset=utf-8

<html>
    <head><title>$title</title>$style</head>
    <body bgcolor="$bgcolor">
        <table width="100%" border="0">
            <tr valign="top">
                <td>
                    <h1>$title</h1>
                </td>
                <td align="right">
                    <a href="?$frontpage">$frontpage</a> | 
                    @{[$canedit ? qq(<a href="?mycmd=edit&mypage=$mypage">$naviedit</a> | ) : '' ]}
                    <a href="?mycmd=index">$naviindex</a> | 
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
    local $_ = shift;
    return unless $_;
    s|\r\n|\n|g;
    s|\r|\n|g;
    s|\&|&amp;|g;
    s|<|&lt;|g;
    s|>|&gt;|g;
    s|"|&quot;|g;
    return $_;
}

sub print_content {
    $_ = &escape($database{$q->param("mypage")});
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
        return qq|<a href="?$_">$_</a>|;
    } else {
        return qq|$_<a href="?mycmd=edit&mypage=$_">$editchar</a>|;
    }
}

sub sanitize_form {
    if (defined($q->param("mypage")) and $q->param("mypage") !~ /^$WikiName$/) {
        &print_error("(invalid mypage)");
    }
}
