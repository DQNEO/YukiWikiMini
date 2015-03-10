use strict;
use warnings;
use App::YukiWikiMini;
use Plack::Request;

my $app = App::YukiWikiMini::to_app();

my $wrapper = sub {
    my $env = shift;
    my $req = Plack::Request->new($env);
    return $app->($req);
};

