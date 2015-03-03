#!/usr/bin/env perl
use strict;
use warnings;
use CGI;

our $VERSION = "1.2.1";

my $dbname = 'ykwkmini';
my $frontpage = 'FrontPage';
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

my $app = sub {
    my $env = shift;
    my $body;

    my $status;
    my $headers = ["Content-type" => "text/html; charset=utf-8"];
    if (defined($q->param("mypage")) and $q->param("mypage") !~ /^$WikiName$/) {
        $status = 200;
        $body = do_error("(invalid mypage)");
        return [$status,$headers, $body];
    }

    if (defined $env->Vars->{keywords} && $env->Vars->{keywords} =~ /^($WikiName)$/) {
        $env->Vars->{mycmd} = 'read';
        $env->Vars->{mypage} = $1;
    }

    unless (dbmopen(%database, $dbname, 0666)) {
        $status = 200;
        $body =  do_error("(dbmopen)");
        return [$status,$headers, $body];
    }

    $_ = $env->Vars->{mycmd};
    if (! $_) {
        $env->Vars->{mypage} = $frontpage;
        $body = do_read($q);
    } elsif (/^read$/) {
        $body = do_read($q);
    } elsif (/^write$/) {
        $body = do_write($q);
    } elsif (/^edit$/) {
        $body = do_edit($q);
    } elsif (/^index$/) {
        $body = do_index($q);
    } else {
        $env->Vars->{mypage} = $frontpage;
        $body = do_read($q);
    }
    dbmclose(%database);
    $status = 200;

    return [$status,$headers, $body];
};

handle_psgi($app, $q);

sub handle_psgi {
    my ($app, $q) = @_;
    my ($status,$headers,$body) = @{$app->($q)};
    print $headers->[0], ":" , $headers->[1] , "\n";
    print "\n";
    print $_ for @$body;
}

sub do_read {
    my $q = shift;
    return [
        render_header($q->param("mypage"), 1),
        render_content(),
        render_footer(),
        ];
}

sub do_edit {
    my $q = shift;

    my $mymsg = escape($database{$q->param("mypage")});
    $mymsg = "" unless defined $mymsg;
    my $mypage = $q->param("mypage");

    my $form =  <<"EOD";
    <form action="." method="post">
        <input type="hidden" name="mycmd" value="write">
        <input type="hidden" name="mypage" value="$mypage">
        <input type="submit" value="$naviwrite"><br />
        <textarea cols="$cols" rows="$rows" name="mymsg" wrap="off">$mymsg</textarea><br />
        <input type="submit" value="$naviwrite">
    </form>
EOD

    return [
        render_header($q->param("mypage"), 0),
        $form,
        render_footer()
        ];
}

sub do_index {
    my $q = shift;
    my $indexpage = 'Index';

    my @li;
    foreach (sort keys %database) {
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

    if ($q->Vars->{mymsg}) {
        $database{$q->param("mypage")} = $q->Vars->{mymsg};
        return [
            render_header($q->param("mypage"), 1),
            render_content(),
            render_footer(),
            ];
    } else {
        delete $database{$q->param("mypage")};
        return [
            render_header($q->param("mypage") . $msgdeleted, 0),
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
    return "<pre>". $_. "</pre>";
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

