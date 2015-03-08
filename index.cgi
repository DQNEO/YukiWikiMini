#!/usr/bin/env perl
use strict;
use warnings;
use CGI;

our $VERSION = "1.2.1";

my $config = { frontpage => 'FrontPage'};

my $WikiName = '([A-Z][a-z]+([A-Z][a-z]+)+)';

my $app = sub {
    my $env = my $q = shift;

    my $db = {};
    my $body;

    my $status;
    my $headers = ["Content-type" => "text/html; charset=utf-8"];

    my $cmd = $env->param("mycmd");
    my $mypage = $q->param("mypage");
    if (defined($mypage) and $mypage !~ /^$WikiName$/) {
        $status = 200;
        $body = do_error("(invalid mypage)");
        return [$status,$headers, $body];
    }

    if ($ENV{QUERY_STRING} =~ /^($WikiName)$/) {
        $cmd = 'read';
        $mypage = $1;
    }

    unless (db_open($db)) {
        $status = 200;
        $body =  do_error("(dbmopen)");
        return [$status,$headers, $body];
    }

    if (! $cmd) {
        $body = do_read($q, $db, $config->{frontpage});
    } elsif ($cmd eq "read") {
        $body = do_read($q, $db, $mypage);
    } elsif ($cmd eq "write") {
        $body = do_write($q, $db, $mypage);
    } elsif ($cmd eq "edit") {
        $body = do_edit($q, $db, $mypage);
    } elsif ($cmd eq "index") {
        $body = do_index($q, $db);
    } else {
        $body = do_read($q, $db, $config->{frontpage});
    }
    db_close($db);
    $status = 200;

    return [$status,$headers, $body];
};

handle_psgi($app, CGI->new);

sub handle_psgi {
    my ($app, $q) = @_;
    my ($status,$headers,$body) = @{$app->($q)};
    print $headers->[0], ":" , $headers->[1] , "\n";
    print "\n";
    print $_ for @$body;
}

sub do_read {
    my $q = shift;
    my $db = shift;
    my $mypage = shift;
    return [
        render_header($mypage, 1),
        render_content($db, $mypage),
        render_footer(),
        ];
}

sub do_edit {
    my $q = shift;
    my $db = shift;
    my $mypage = shift;
    my $mymsg = escape($db->{$mypage});
    $mymsg = "" unless defined $mymsg;

    my $form =  <<"EOD";
    <form action="." method="post">
        <input type="hidden" name="mycmd" value="write">
        <input type="hidden" name="mypage" value="$mypage">
        <input type="submit" value="Write"><br />
        <textarea cols="80" rows="20" name="mymsg" wrap="off">$mymsg</textarea><br />
        <input type="submit" value="Write">
    </form>
EOD

    return [
        render_header($mypage, 0),
        $form,
        render_footer()
        ];
}

sub do_index {
    my $q = shift;
    my $db = shift;
    my $indexpage = 'Index';

    my @li;
    foreach (sort keys %$db) {
        push @li, "<li><a href=\"?$_\"><tt>$_</tt></a></li>\n";
    }

    return [
        render_header($indexpage, 0),
        "<ul>\n",
        @li,
        "</ul>\n",
        render_footer()
        ];
}

sub do_write {
    my $q = shift;
    my $db = shift;
    my $mypage = shift;
    if ($q->param("mymsg")) {
        $db->{$mypage} = $q->param("mymsg");
        return [
            render_header($mypage, 1),
            render_content($db, $mypage),
            render_footer(),
            ];
    } else {
        delete $db->{$mypage};
        return [
            render_header($mypage . ' is deleted.', 0),
            render_footer()
            ];
    }

}

sub do_error {
    my $msg = shift;
    my $errorpage = 'Error';

    return [
        render_header($errorpage, 0),
        "<h1>$msg</h1>",
        render_footer()
        ];
}

sub render_header {
    my ($mypage, $canedit) = @_;
    my $params = {
        title => $mypage,
        frontpage => $config->{frontpage},
        mypage => $mypage  || "",
        canedit => $canedit,
    };

    my $html =  <<"EOD";
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
                    @{[$params->{canedit} ? qq(<a href="?mycmd=edit&mypage=$params->{mypage}">Edit</a> | ) : '' ]}
                    <a href="?mycmd=index">Index</a> | 
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
    my $db = shift;
    my $mypage = shift;
    $_ = escape($db->{$mypage});
    s!
        (
            ((mailto|http|https|ftp):[\x21-\x7E]*)  # Direct http://...
                |
            ($WikiName)                             # LocalLinkLikeThis
        )
    !
        make_link($1, $db)
    !gex;
    return "<pre>". $_. "</pre>";
}

sub make_link {
    my $word = shift;
    my $db = shift;

    my $editchar = '?';

    if ($word =~ /^(http|https|ftp):/) {
        return sprintf('<a href="%s">%s</a>', $word, $word);
    } elsif ($word =~ /^(mailto):(.*)/) {
        return sprintf('<a href="%s">%s</a>', $word, $2);
    } elsif ($db->{$word}) {
        return sprintf('<a href="?%s">%s</a>', $word, $word);
    } else {
        return sprintf('%s<a href="?mycmd=edit&mypage=%s">%s</a>',
                       $word, $word, $editchar);
    }
}

sub db_open {
    my $db = shift;
    my $dbname = 'ykwkmini';
    dbmopen(%$db, $dbname, 0666);
}

sub db_close {
    my $db = shift;
    dbmclose(%$db);
}
