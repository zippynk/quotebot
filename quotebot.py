#!/usr/bin/env python

#  To run quotebot, type `python quotebot.py <host> <channel (no #)> [--ssl|--plain] <nick> [--readconfig]` into a terminal, replacing the placeholders with your configuration.

# The `--readconfig` flag reads all other data from the file titled `config.json` in the same directory as quotebot. This installation should contain an example configuration file, titled `config_example.json`.
# The `--password` flag prompts the user for a password when starting quotebot. Note that you may not be able to see the password as you type it, and that this can interfere with running quotebot in a location where you cannot actively input text. Does not run with `--readconfig`, as it does not apply there; the `config.json` file has an option for a password.

#  Based on Hardmath123's jokebot. https://github.com/hardmath123/jokebot

#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.


import socket
import select
import random
import ssl
import sys
import time
import os
import pickle
from datetime import datetime
import json
import getpass
import sendquote

if "/" in __file__:
    configLocation = os.path.dirname(__file__) +"/config.json"
else:
    configLocation = "config.json"
thisVersion = [0,1,0,"d"] # The version of quotebot, as a list of numbers (eg [0,1,0] means "v0.1.0"). A "d" at the end means that the current version is a development version and very well may break at some point.

if (len(sys.argv) < 5 or len(sys.argv) > 6) and not "--readconfig" in sys.argv:
    print """Usage: python quotebot.py <host> <channel (no #)> [--ssl|--plain] <nick> [--readconfig]

The `--readconfig` flag reads all other data from the file titled `config.json` in the same directory as quotebot. This installation should contain an example configuration file, titled `config_example.json`.
The `--password` flag prompts the user for a password when starting quotebot. Note that you may not be able to see the password as you type it, and that this can interfere with running quotebot in a location where you cannot actively input text. Does not run with `--readconfig`, as it does not apply there; the `config.json` file has an option for a password."""
    exit(0)

# Begin dev edition code.
if "d" in thisVersion:
    print "WARNING! This is a development version of quotebot. Proceeding may corrupt quotebot database files, crash, and/or have other consequences. Proceed at your own risk."
    if not raw_input("Are you sure you want to proceed? (y/n) ").lower() in ["yes","y","true","continue","yea","yeah","yup","sure"]:
        print "Aborting."
        exit(0)

# End Dev Edition Code.

if "--readconfig" in sys.argv:
    if os.path.isfile(configLocation):
        try:
            config = json.loads(open(configLocation,'r').read())
        except:
            print "Failed to decode configuration file."
            if "d" in thisVersion:
                print str(sys.exc_info()[0])
            exit(0)
        try:
            HOST = str(config["server"])
            if len(config["channels"]) > 1:
                print "quotebot only supports joining one channel at a time. Exiting."
                exit(0)
            else:
                CHANNEL = str(config["channels"][0])
            SSL = config["use_ssl"]
            NICK = config["nickname"]
        except KeyError, e:
            print "Failed to decode configuration file."
            if "d" in thisVersion:
                print e
            exit(0)
        if "nick-password" in config.keys():
            PASSWORD = config["nick-password"]
        else:
            PASSWORD = False
        PORT = 6697 if SSL else 1338
    else:
        print "Failed to decode configuration file."
        if "d" in thisVersion:
            print "File " +configLocation +" does not exist."
        exit(0)

else:
    HOST = sys.argv[1]
    CHANNEL = "#"+sys.argv[2]
    SSL = sys.argv[3].lower() == '--ssl'
    PORT = 6697 if SSL else 1338

    NICK = sys.argv[4]
    
    if "--password" in sys.argv:
        PASSWORD = getpass.getpass("Password? ")
    else:
        PASSWORD = False
        
USEDB = True

if USEDB == True and os.path.isfile(os.path.expanduser("~") +'/.quotebot_database.p'):
    dbLoad = pickle.load(open(os.path.expanduser("~") +'/.quotebot_database.p','rb'))
    if dbLoad['version'] == [0,2,0]:
        quotes = dbLoad['quotes']
    if dbLoad['version'] == [0,3,0]:
        quotes = dbLoad['quotes']
    else:
        print "This database was created with an old or unknown version of quotebot. Please use the newest version (or correct fork) and try again. If this is not possible, move or delete the file '~/.quotebot_database.p' and re-run quotebot. A new database will be created automatically."
        exit(0)
else:
    quotes = []
def saveDb():
    if USEDB == True:
        pickle.dump({'quotes':quotes,'version':thisVersion}, open(os.path.expanduser("~") +'/.quotebot_database.p','wb'))
        
last10Messages = []
    
plain = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s = ssl.wrap_socket(plain) if SSL else plain

print "Connecting..."

s.connect((HOST, PORT))
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
            print "Leaving..."
            s.sendall("PART %s :Bye\r\n"%(CHANNEL))
            s.close()
            exit(0)

print "Registering..."

s.sendall("NICK %s\r\n"%("tempnick" +str(random.randint(10000001,99999999))))
s.sendall("USER %s * * :A quote bot\r\n"%(NICK))


connected = False
def got_message(message):
    print message
    global connected # yes, bad Python style. but it works to explain the concept, right?
    words = message.split(' ')
    if 'PING' in message:
        s.sendall('PONG\r\n') # it never hurts to do this :)
    if words[0][0] == ":":
        writing = True
        name = ''
        for i in words[0][1:len(words[0])-1]:
            if i == ' ' or i == '!':
                writing = False
            else:
                if writing == True:
                    name = name +i
    if words[1] == '001' and not connected:
        # As per section 5.1 of the RFC, 001 is the numeric response for
        # a successful connection/welcome message.
        connected = True
        if not PASSWORD == False:
            s.sendall("PRIVMSG NickServ :" +"ghost " +NICK +" " +PASSWORD +"\r\n")
            s.sendall("PRIVMSG NickServ :" +"identify " +NICK +" " +PASSWORD +"\r\n")
            print "Waiting for NickServ (this will take 10 seconds, and is necessary to make sure other instances are ghosted appropriately)..."
            time.sleep(10)
        s.sendall("NICK %s\r\n"%(NICK))
        s.sendall("JOIN %s\r\n"%(CHANNEL))
        print "Joining..."
    elif words[1] == 'PRIVMSG' and (words[2] == CHANNEL or words[2] == NICK) and ('@quotethat' in words[3]) and connected:
        # Someone probably said `@quotethat`.
        print "Caught."
        quotes.append("\n".join(last10Messages))
        "\n".join(last10Messages)
        saveDb()
        sendQuote("\n".join(last10Messages) +"\n\nSubmitted by quotebot on " +str(datetime.now))
        s.sendall("PRIVMSG %s :"%(CHANNEL if words[2] == CHANNEL else name) +name +": Quoted!" + "\r\n")
    elif words[1] == 'PRIVMSG' and (words[2] == CHANNEL or words[2] == NICK) and '@help' in words[3] and connected and not CLASSICMODE:
        s.sendall("PRIVMSG %s :"%(CHANNEL if words[2] == CHANNEL else name) +"This bot uses the quotebot software, which is created by Nathan Krantz-Fire (a.k.a zippynk), based on Jokebot by Hardmath123." +"\r\n")
        if "d" in thisVersion:
            s.sendall("PRIVMSG %s :"%(CHANNEL if words[2] == CHANNEL else name) +"WARNING: THIS IS A DEVELOPMENT VERSION! USE AT YOUR OWN RISK!" +"\r\n")
        s.sendall("PRIVMSG %s :"%(CHANNEL if words[2] == CHANNEL else name) +" " +"\r\n")
        s.sendall("PRIVMSG %s :"%(CHANNEL if words[2] == CHANNEL else name) +"Commands:" +"\r\n")
        s.sendall("PRIVMSG %s :"%(CHANNEL if words[2] == CHANNEL else name) +" " +"\r\n")
        s.sendall("PRIVMSG %s :"%(CHANNEL if words[2] == CHANNEL else name) +"`@quote Start:Time-End:Time` quotes the messages sent between the start and end times and adds them to the DB. Must be from the past 24 hours. Use Pacific 24-Hour time for your timestamps." +"\r\n")
        s.sendall("PRIVMSG %s :"%(CHANNEL if words[2] == CHANNEL else name) +"`@quotethat` quotes the last 10 messages and adds them to the DB." +"\r\n")
        s.sendall("PRIVMSG %s :"%(CHANNEL if words[2] == CHANNEL else name) +"`@help` displays a message similar to this guide, but tailored to IRC users." +"\r\n")
        s.sendall("PRIVMSG %s :"%(CHANNEL if words[2] == CHANNEL else name) +" " +"\r\n")
        s.sendall("PRIVMSG %s :"%(CHANNEL if words[2] == CHANNEL else name) +"Quotebot source code: https://github.com/zippynk/quotebot (available under the Mozilla Public License 2.0)" +"\r\n")
        s.sendall("PRIVMSG %s :"%(CHANNEL if words[2] == CHANNEL else name) +"Jokebot source code: https://github.com/hardmath123/jokebot (available under the Unlicense)" +"\r\n")
    if words[1] == 'PRIVMSG' and words[2] == CHANNEL:
        last10Messages.append(str(datetime.now()) +" - " +name +": " +" ".join(words[3:len(words)])[1:len(" ".join(words[3:len(words)]))])
        if len(last10Messages) > 10:
            last10Messages.pop(0)

read_loop(got_message)