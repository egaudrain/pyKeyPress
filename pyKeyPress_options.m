function options = pyKeyPress_options()

%OPTIONS = PYKEYPRESS_OPTIONS()
%   Returns the options for communication with a pyKeyPress server. Edit this
%   file to modify the default behaviour.

%--------------------------------------------------------
% Etienne Gaudrain <etienne.gaudrain@cnrs.fr> - 2017-03-06
%--------------------------------------------------------
% Copyright 2017 CNRS, FR; UMCG, NL
%--------------------------------------------------------


options.host = '127.0.0.1';
options.port = 9999;

%-- The options below shouldn't be modified without changing the Python
%   counterpart.
options.socket_header  = 'pyKeyPress';
options.socket_version = 20170306;