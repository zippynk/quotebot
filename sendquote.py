#!/usr/bin/env python
#  A python module for submitting Quotes to the Backtick Quote DB. Distributed as part of quotebot by Nathan Krantz-Fire (a.k.a zippynk). https://github.com/zippynk/quotebot
#  Based on Hardmath123's jokebot. https://github.com/hardmath123/jokebot
#  Many thanks to Hardmath123 and Nickolas360 for helping debug this module.

#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import socket
import select
import ssl
import sys
import time
import os
newline = """
"""

def read_loop(callback):
    data = ""
    CRLF = '\r\n'
    while True:
        time.sleep(0.2)
        try:
            readables, writables, exceptionals = select.select([s], [s], [s])
            if len(readables) == 1:
                data += s.recv(512);
                while CRLF in data:
                    message = data[:data.index(CRLF)]
                    data = data[data.index(CRLF)+2:]
                    callback(message)
        except KeyboardInterrupt:
            s.close()
            exit(0)

def submitQuote(quote):
    plain = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s = plain
    s.connect(("localhost", 1338))
    #time.sleep(0.2) # Currently commented out, as it seems I don't need it. I may revisit this in the future.
    lines = quote.split("\n")
    for i in lines:
        s.sendall(quote +newline)
        time.sleep(0.1)
    time.sleep(0.2)
    s.shutdown(socket.SHUT_RDWR)
    s.close()

if __name__ == "__main__":
    submitQuote(raw_input("Quote: "))
