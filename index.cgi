#!/usr/bin/env perl
use strict;
use warnings;
use CGI;

our $VERSION = "1.2.0";

my $dbname = 'ykwkmini';
my $frontpage = 'FrontPage';
my $indexpage = 'Index';
my $errorpage = 'Error';
my $WikiName = '([A-Z][a-z]+([A-Z][a-z]+)+)';
my $editchar = '?';
my $naviwrite = 'Write';
my $naviedit = 'Edit';
my $naviindex = 'Index';
my $msgdeleted = ' is deleted.';
my $cols = 80;
my $rows = 20;

my %form;
my %database;
my $q = CGI->new;

main();

sub main {
    sanitize_form();

    if (defined $q->Vars->{keywords} && $q->Vars->{keywords} =~ /^($WikiName)$/) {
        $q->Vars->{mycmd} = 'read';
        $q->Vars->{mypage} = $1;
    }

    unless (dbmopen(%database, $dbname, 0666)) {
        print render_error("(dbmopen)");
        exit(0);
    }
    $_ = $q->Vars->{mycmd};
    if (! $_) {
        $q->Vars->{mypage} = $frontpage;
        do_read();
    } elsif (/^read$/) {
        do_read();
    } elsif (/^write$/) {
        do_write();
    } elsif (/^edit$/) {
        do_edit();
    } elsif (/^index$/) {
        do_index();
    } else {
        $q->Vars->{mypage} = $frontpage;
        do_read();
    }
    dbmclose(%database);
}

sub do_read {
    print render_header($q->param("mypage"), 1);
    print render_content();
    print render_footer();
}

sub do_edit {
    print render_header($q->param("mypage"), 0);
    my $mymsg = escape($database{$q->param("mypage")});
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
    print render_footer();
}

sub do_index {
    print render_header($indexpage, 0);
    print qq|<ul>\n|;
    foreach (sort keys %database) {
        print qq|<li><a href="?$_"><tt>$_</tt></a></li>\n|
    }
    print qq|</ul>\n|;
    print render_footer();
}

sub do_write {
    if ($q->Vars->{mymsg}) {
        $database{$q->param("mypage")} = $q->Vars->{mymsg};
        print render_header($q->param("mypage"), 1);
        print render_content();
    } else {
        delete $database{$q->param("mypage")};
        print render_header($q->param("mypage") . $msgdeleted, 0);
    }
    print render_footer();
}

sub render_error {
    my $msg = shift;
    my $html;
    $html = render_header($errorpage, 0);
    $html .= "<h1>$msg</h1>";
    $html .= render_footer();
    return $html;
}

sub render_header {
    my ($title, $canedit) = @_;
    my $params = {
        title => $title,
        frontpage => $frontpage,
        mypage => $q->param("mypage") || "",
        naviedit => $naviedit,
        naviindex => $naviindex,
        canedit => $canedit,
    };

    my $html =  <<"EOD";
Content-type: text/html; charset=utf-8

<!DOCTYPE html>
<html>
    <head>
    <meta charset="utf-8">
    <title>$params->{title}</title>
    <style type="text/css">
    <!--
    body { font-family: "Courier New", monospace; }
    pre { line-height:130%; }
    a { text-decoration: none }
    a:hover { text-decoration: underline }
    -->
    </style>
    </head>
    <body bgcolor="white">
        <table width="100%" border="0">
            <tr valign="top">
                <td>
                    <h1>$params->{title}</h1>
                </td>
                <td align="right">
                    <a href="?$params->{frontpage}">$params->{frontpage}</a> | 
                    @{[$params->{canedit} ? qq(<a href="?mycmd=edit&mypage=$params->{mypage}">$params->{naviedit}</a> | ) : '' ]}
                    <a href="?mycmd=index">$params->{naviindex}</a> | 
                    <a href="http://www.hyuki.com/yukiwiki/mini/">YukiWikiMini</a>
                </td>
            </tr>
        </table>
EOD
}

sub render_footer {
    return "</body></html>";
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

sub render_content {
    $_ = escape($database{$q->param("mypage")});
    s!
        (
            ((mailto|http|https|ftp):[\x21-\x7E]*)  # Direct http://...
                |
            ($WikiName)                             # LocalLinkLikeThis
        )
    !
        make_link($1)
    !gex;
    return "<pre>", $_, "</pre>";
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
        print render_error("(invalid mypage)");
        exit(0);
    }
}
