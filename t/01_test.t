use strict;
use warnings;
use Test::More;
use App::YukiWikiMini;
use CGI;

my $app = App::YukiWikiMini::to_app();
my $q = CGI->new;
my $res = $app->($q);

is ref $res , "ARRAY";

my $count = @$res;

is $count, 3 ,"response 3 elements";

is $res->[0], 200, "status 200";

is $res->[1]->[0], "Content-type";
is $res->[1]->[1], "text/html; charset=utf-8";

done_testing;

