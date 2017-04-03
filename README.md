# pyKeyPress

A key-press server for psychophysical response time measurements.

A server logging all key strokes and their system timestamp is running in the background. A client can be used to poll the server and access the stack of events.

## Server

To start the server, type `python pyKeyPress.py` in a terminal:

```
usage: pyKeyPress.py [-h] [--host HOST] [--port PORT] [-n STACKSIZE] [-v]
                     [--version]

Runs a key logging server.

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           The IP address of the host on which the server is
                        running.
  --port PORT           Port on which the server can be queried.
  -n STACKSIZE, --stacksize STACKSIZE
                        Defines the size of the event stack kept in memory
  -v, --verbose         Displays activity in the console.
  --version             Displays version information and returns.

Written by Etienne Gaudrain <etienne.gaudrain@cnrs.fr>
Copyright 2017 CNRS (FR), UMCG (NL)
```
## Matlab client

To collect key strokes from Matlab, use the `pyKeyPress_query` function in Matlab.

`RESP = pyKeyPress_query(QUERY, [PORT, HOST])`

Sends a `QUERY` to a running pyKeyPress server and returns a structure `RESP`.
 
The QUERY is a struct() that can contain the following fields:
  - `from`: the timestamp from which key presses will be considered
  - `to`: the timestamp until which key presses will be considered
  - `first`: to limit the output to N first elements
  - `last`: (incompatible with first) to limit the output to N last
            elements.
 
If the `QUERY` has a field `shutdown` that evaluates to true, the server will be shut down.
 
The response `RESP` is a `struct()` with the following fields:
  - `success`: always present, this field is 1 if the server processed the
             query successfully and 0 otherwise
  - `code`: if there was communication with the server, it returns a code
          similar to HTTP response codes
  - `message`: same as code, but the textual version
  - `body`: always present, this field contains the results from the query
          if it was successful, or a message indicating the error if the
          query did not terminate properly
 
If the `QUERY` did return some results, they have the following structure:
  - `char`: the character corresponding the keypress
  - `t`: the timestamp of the keypress (in seconds since system startup)
  - `key`: the keycode of the keypress
 
The timestamp is in same format and unit as the PsychToolbox `GetSecs` function.
 
If omitted, `PORT` and `HOST` are taken from `pyKeyPress_options()`.
 
