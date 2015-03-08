#!/usr/bin/env perl
use strict;
use warnings;
use CGI;

require 'YukiWikiMini.pm';
my $app = YukiWikiMini::to_app();

my $cgi = CGI->new;
$cgi->{QUERY_STRING} = $ENV{QUERY_STRING};

my ($status,$headers,$body) = @{$app->($cgi)};
print $headers->[0], ":" , $headers->[1] , "\n";
print "\n";
print $_ for @$body;

