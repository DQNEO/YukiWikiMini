#!/usr/bin/env perl
use strict;
use warnings;
use CGI;

my $app = require 'app.psgi';

my $cgi = CGI->new;
$cgi->{QUERY_STRING} = $ENV{QUERY_STRING};

handle_psgi($app, $cgi);

sub handle_psgi {
    my ($app, $cgi) = @_;
    my ($status,$headers,$body) = @{$app->($cgi)};
    print $headers->[0], ":" , $headers->[1] , "\n";
    print "\n";
    print $_ for @$body;
}

