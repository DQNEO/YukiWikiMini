use strict;
use warnings;
use YukiWikiMini;
use Plack::Request;

my $app = YukiWikiMini::to_app();

my $wrapper = sub {
    my $env = shift;
    my $req = Plack::Request->new($env);
    return $app->($req);
};

