#!/usr/bin/env python
#-*- coding: utf-8 -*-

#==============================================================================
# pyKeyPress - A key-logging server that can be queried for response times
#------------------------------------------------------------------------------
# Etienne Gaudrain <etienne.gaudrain@cnrs.fr>, 2017-03-06
# Copyright CNRS (FR), UMCG (NL) and the authors.
#------------------------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#==============================================================================

"""
pyKeyPress is a key logger that runs in the backgound and captures all key presses
and the system timestamp at which they occur. The key stack can then be queried to
retrieve some or all of the key presses events.

See --help for details of the command line arguments of the server.

The server implements a TCP/IP protocol and can thus be connected to from any system
that implements that protocol. The packets are JSON encoded objects ending with a
line feed character '\\n'. The packet objects send by the client must have the
following fields:
- header: should be "pyKeyPress"
- socket_version: specifies the verison of the socket format (currently 20170306).
  Newer socket handler should ensure backward compatibility, but if the socket
  handler is older than the socket, an error will be returned.

With no more fields, the server will return the entire stack of key presses (by
default the stack is 1024 elements). Otherwise, the stack can be filtered with one
or more of the following fields:
- from: the timestamp from which events are included
- to: the timestamp until which events are included
- first: the number of events to return starting from the first one (incompatible
  with 'last')
- last: the number of events to return starting from the last one (incompatible
  with 'first')
- char: a character or an array of characters to include
- keycode: a keycode or an array of keycodes to include

To shutdown the server, you need to send it a query with a 'shutdown' field that
evaluates to True.

The principle of the implementation is that the key-logger is retrieving system
events by attempting to add a hook in the system loop. If this is not possible on
that system, then the key-logger runs a tight loop monitoring key-presses. At the
moment, the only implementation is for Mac OSX. Implementations for Windows and
Linux need to be developped.

IMPORTANT: Key-logging represents a serious security danger for your computer. Do
not type sensitive information like passwords while the key-logger is running.
"""

import platform

SYSTEM = platform.system()
SOCKET_VERSION = 20170306

#===============================================================
# Mac OSX
#-----------------------------------------------------
if SYSTEM=='Darwin':

    from AppKit import NSApplication, NSApp
    from Foundation import NSObject, NSLog
    from Cocoa import NSEvent, NSKeyDownMask
    from PyObjCTools import AppHelper

    class AppDelegate(NSObject):
        def applicationDidFinishLaunching_(self, notification):
            # Note: we only monitor key-down events, not key-release

            if VERBOSE>=2:
                print "-> applicationDidFinishLaunching"

            mask = NSKeyDownMask
            evH = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(mask, osx_handler)
            if not evH:
                raise RuntimeError("The Global Monitor couldn't be added the App.")

    #-----------------------------------------------------
    def osx_handler(event):
        global key_stack, VERBOSE

        c = event.characters()
        t = event.timestamp()
        k = event.keyCode()

        if VERBOSE>=2:
            print "%9s [%03d] @ %f" % (repr(c), k, t)

        with key_stack_lock:
            key_stack.append({'char': c, 't': t, 'key': k})

    #-----------------------------------------------------
    def monitor_start():
        app = NSApplication.sharedApplication()
        delegate = AppDelegate.alloc().init()
        NSApp().setDelegate_(delegate)
        AppHelper.runEventLoop()

    #-----------------------------------------------------
    def monitor_stop():
        AppHelper.stopEventLoop()

#===============================================================

from threading import Semaphore, Thread
import SocketServer, socket
import collections, copy
import json

SocketServer.TCPServer.allow_reuse_address = True

class pyKeyPress_RequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(1)
        try:
            buffer = ''
            continue_receiving = True
            while "\n" not in buffer:
                buffer += self.request.recv(4096)

            buffer = unicode(buffer.split('\n',1)[0], "UTF-8")

            if VERBOSE:
                print "Received query:"
                print "   ", buffer

            query = json.loads(buffer)

            # Checking if we got the right type of query
            if 'header' not in query:
                raise ValueError("No header element.")
            elif query['header']!='pyKeyPress':
                raise ValueError("Bad header element.")

            # Checking if we have compatible version
            if 'socket_version' not in query:
                raise ValueError("No socket version provided.")
            elif query['socket_version']>SOCKET_VERSION:
                raise ValueError("The sent socket is version %d but the server can only handle %d." % (query['socket_version'], SOCKET_VERSION))

            # Checking if we have compatible version
            if 'last' in query and 'first' in query:
                raise ValueError("The arguments 'first' and 'last' cannot be used simultaneously.")

            if 'shutdown' in query and query['shutdown']:
                self.request.shutdown(socket.SHUT_RD)
                self.request.close()
                if VERBOSE:
                    print "Shutting down server..."
                self.server.__shutdown_request = True
                if VERBOSE:
                    print "Stopping monitor..."
                monitor_stop()
                return

            resp = self.handle_query(query)
            self.request.send(self.encapsulate({'code': 200, 'message': "OK", 'body': resp}))

        except socket.timeout, e:
            self.request.send(self.encapsulate({'code': 408, 'message': "Request Timeout", 'body': unicode(e)}))
        except ValueError, e:
            self.request.send(self.encapsulate({'code': 400, 'message': "Bad Request", 'body': unicode(e)}))


    def encapsulate(self, obj):
        return json.dumps(obj)+'\n'

    def handle_query(self, query):
        global key_stack, key_stack_lock

        with key_stack_lock:
            ks = list(copy.deepcopy(key_stack))

        if 'from' in query:
            ks = [x for x in ks if x['t']>=query['from']]

        if 'to' in query:
            ks = [x for x in ks if x['t']<=query['to']]

        if 'first' in query:
            ks = ks[0:query['first']]
        elif 'last' in query:
            ks = ks[-query['last']:]

        if 'char' in query:
            ks = [x for x in ks if x['char'] in query['char']]

        if 'keycode' in query:
            if type(query['keycode'])==type(int()):
                query['keycode'] = [query['keycode']]
            ks = [x for x in ks if x['key'] in query['keycode']]

        return ks

#===============================================================
def main(host='127.0.0.1', port=9999, stacksize=1024, verbose=False):
    global key_stack, key_stack_lock, server, VERBOSE

    VERBOSE = verbose

    key_stack = collections.deque(maxlen=stacksize)
    key_stack_lock = Semaphore()
    #query_stack = Queue.Queue(1024)

    if VERBOSE:
        print "Starting pyKeyPress server on %s:%d" % (host, port)

    server = SocketServer.ThreadingTCPServer((host, port), pyKeyPress_RequestHandler)
    server_thread = Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    monitor_start()

    server.shutdown()
    server.server_close()
    if VERBOSE:
        print "Server and monitor stopped."


#-----------------------------------------------------
if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Runs a key logging server.', epilog='Written by Etienne Gaudrain <etienne.gaudrain@cnrs.fr>\nCopyright 2017 CNRS (FR), UMCG (NL)', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--host', help="The IP address of the host on which the server is running.", default='127.0.0.1')
    parser.add_argument('--port', help="Port on which the server can be queried.", default=9999, type=int)
    parser.add_argument('-n', '--stacksize', help="Defines the size of the event stack kept in memory", default=1024, type=int)
    parser.add_argument('-v', '--verbose', help="Displays activity in the console.", default=0, action='count')
    parser.add_argument('--version', help="Displays version information and returns.", action='version', version="SOCKET_VERSION = %d" % SOCKET_VERSION)

    args = parser.parse_args()

    main(args.host, args.port, args.stacksize, args.verbose)
