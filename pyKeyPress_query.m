function resp = pyKeyPress_query(query, port, host)

%RESP = PYKEYPRESS_QUERY(QUERY, [PORT, HOST])
%   Sends a QUERY to a running pyKeyPress server and returns a
%   structure RESP.
%
%   The QUERY is a struct() that can contain the following fields:
%   - from: the timestamp from which key presses will be considered
%   - to: the timestamp until which key presses will be considered
%   - first: to limit the output to N first elements
%   - last: (incompatible with first) to limit the output to N last
%           elements.
%
%   If the QUERY has a field 'shutdown' that evaluates to true, the server
%   will be shut down.
%
%   The response RESP is a struct() with the following fields:
%   - success: always present, this field is 1 if the server processed the
%              query successfully and 0 otherwise
%   - code: if there was communication with the server, it returns a code
%           similar to HTTP response codes
%   - message: same as code, but the textual version
%   - body: always present, this field contains the results from the query
%           if it was successful, or a message indicating the error if the
%           query did not terminate properly
%
%   If the QUERY did return some results, they have the following
%   structure:
%   - char: the character corresponding the keypress
%   - t: the timestamp of the keypress (in seconds since system startup)
%   - key: the keycode of the keypress
%
%   The timestamp is in same format and unit as the PsychToolbox GETSECS
%   function.
%
%   If omitted, PORT and HOST are taken from PYKEYPRESS_OPTIONS().
%
%   See also PYKEYPRESS_OPTIONS, GETSECS

%--------------------------------------------------------
% Etienne Gaudrain <etienne.gaudrain@cnrs.fr> - 2017-03-06
%--------------------------------------------------------
% Copyright 2017 CNRS, FR; UMCG, NL
%--------------------------------------------------------


import java.net.Socket
import java.io.*

options = pyKeyPress_options();
if nargin<2
    port = options.port;
end
if nargin<3
    host = options.host;
end

sck = [];
resp = struct();
line = '';

try
    socket_body = format_socket(query);
    sck = Socket(host, port);
    
    output_stream = sck.getOutputStream();
    output_stream_d = PrintWriter(output_stream);
    
    input_stream = sck.getInputStream();
    input_stream_d = BufferedReader(InputStreamReader(input_stream));
    
    output_stream_d.println(char(socket_body));
    output_stream_d.flush();
    
    line = char(input_stream_d.readLine());
    
    resp = matlab.internal.webservices.fromJSON(native2unicode(line, 'utf-8'));
    resp.success = 0;
    if resp.code == 200
        resp.success = 1;
    end

    sck.close();
    
catch ME
    m = '';
    for i=1:length(ME.stack)
        m = [m, sprintf('%s, line %d\n', ME.stack(i).name, ME.stack(i).line)];
    end
    
    resp.success = 0;
    resp.body = sprintf('%s :: %s\n%s\n\nRaw response:\n%s\n', ME.identifier, ME.message, m, line);
    
    if ~isempty(sck)
        try
            sck.close();
        catch
            warning('Couldn''t close the socket...');
        end
    end
    
    return
end



%%-------------------------------------------------------------------------

function s = format_socket(query)

options = pyKeyPress_options();

query.header = options.socket_header;
query.socket_version = options.socket_version;

s = sprintf('%s\n', matlab.internal.webservices.toJSON(query));

