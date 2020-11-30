#!/usr/bin/env perl
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# This Source Code Form is "Incompatible With Secondary Licenses", as
# defined by the Mozilla Public License, v. 2.0.

use 5.10.1;
use strict;
use warnings;

use lib qw(. lib local/lib/perl5);

use Bugzilla;
use Bugzilla::Constants;
use Bugzilla::Error;
use Bugzilla::WebService::Constants;
use Capture::Tiny qw(capture_stdout);

BEGIN {
  if (!Bugzilla->feature('xmlrpc')) {
    ThrowCodeError('feature_disabled', {feature => 'xmlrpc'});
  }
}
use Bugzilla::WebService::Server::XMLRPC;

my $stdout = capture_stdout {
  Bugzilla->usage_mode(USAGE_MODE_XMLRPC);

# Fix the error code that SOAP::Lite uses for Perl errors.
  local $SOAP::Constants::FAULT_SERVER;
  $SOAP::Constants::FAULT_SERVER = ERROR_UNKNOWN_FATAL;

# The line above is used, this one is ignored, but SOAP::Lite
# might start using this constant (the correct one) for XML-RPC someday.
  local $XMLRPC::Constants::FAULT_SERVER;
  $XMLRPC::Constants::FAULT_SERVER = ERROR_UNKNOWN_FATAL;

  local @INC = (bz_locations()->{extensionsdir}, @INC);
  my $server = new Bugzilla::WebService::Server::XMLRPC;

# We use a sub for on_action because that gets us the info about what
# class is being called. Note that this is a hack--this is technically
# for setting SOAPAction, which isn't used by XML-RPC.
  $server->on_action(sub { $server->handle_login(WS_DISPATCH, @_) })->handle();
};
my ($header_str, $body) = split(/(?:\r\n\r\n|\n\n)/, $stdout, 2);
my $headers = Mojo::Headers->new;
my $C = Bugzilla->request_cache->{mojo_controller};
$headers->parse("$header_str\r\n\r\n");
foreach my $name (@{$headers->names}) {
  $C->res->headers->header($name => $headers->header($name));
}
my ($code) = $headers->header('Status') =~ /^(\d+)/;
$C->res->code($code) if $code;
$C->write($body);
exit;
