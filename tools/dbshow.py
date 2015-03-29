#!/usr/bin/env python
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

USEDB = True

if USEDB == True and os.path.isfile(os.path.expanduser("~") +'/.quotebot_database.p'):
    dbLoad = pickle.load(open(os.path.expanduser("~") +'/.quotebot_database.p','rb'))
    if dbLoad['version'] == [0,1,0,"d"]:
        quotes = dbLoad['quotes']
    else:
        print "This database was created with an old or unknown version of quotebot. Please use the newest version (or correct fork) and try again. If this is not possible, move or delete the file '~/.quotebot_database.p' and re-run quotebot. A new database will be created automatically."
        exit(0)
else:
    quotes = []
def saveDb():
    if USEDB == True:
        pickle.dump({'quotes':quotes,'version':thisVersion}, open(os.path.expanduser("~") +'/.quotebot_database.p','wb'))
print str(quotes[0])
for i in quotes[1:len(quotes)]:
    print "----------------------"
    print str(i)