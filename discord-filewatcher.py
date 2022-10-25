#!/usr/bin/env python3

import os
import sys
import sqlite3
import datetime
import time
import re
from discord_webhook import DiscordWebhook

PATH_TO_WATCH="/something"
WEBHOOK_URL = ""

conn = sqlite3.connect("new_files.sqlite")
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS files (mtime REAL NOT NULL, filename VARCHAR NOT NULL, unique(mtime,filename));")
max_mtime = 0

def second_try():
    time.sleep(60) # hold on a minute
    res = webhook.execute()
    print(datetime.datetime.now().replace(microsecond=0).isoformat(), "Second try:", res)
    sys.exit(0)

def scan_and_import():
    new_files = []
    skip_counter = 0
    add_counter = 0
    for dirname, subdirs, files in os.walk(PATH_TO_WATCH):

        for fname in files:
            full_path = os.path.join(dirname, fname)
            mtime = os.stat(full_path).st_mtime
            try:
                cur.execute(
                    f'INSERT INTO files (mtime,filename) values ("{mtime}","{full_path}")'
                )
                conn.commit()
                add_counter += 1
                new_files.append(full_path)
            except Exception as e:
                skip_counter += 1
    return add_counter,skip_counter,new_files

cur.execute("SELECT COUNT(*) FROM files")

newfiles = []

if int(cur.fetchone()[0]) <= 0:
    print("This is an initial run, it will take some time to fill the database. Be patient.")
    print("No new files will be returned, since there's nothing to compare to.")
    print("Folders to check:", len(list(os.walk(PATH_TO_WATCH))))
    scan_and_import()
    print("Done. Create a new file and run me again to test.")
    conn.commit()
    conn.close()
else:
    add, skip, new = scan_and_import()
    conn.commit()
    conn.close()
    if not new:
        curtime = datetime.datetime.now().replace(microsecond=0).isoformat()
        print(f"{curtime} Skipped {skip} files, nothing new")
        sys.exit(0)
    else:
        # check if the file ending should be ignored before appending to newfiles
        ignore_files = ["srt","nfo","txt","sfv","ini","md5","srr","bat"]
        for i in new:
            if i.split('.')[-1] not in ignore_files:
                path = i.split('/')
                newfiles.append(path[-2] + "/" + path[-1])

if newfiles:
    # newfiles.sort(key=lambda test_string : list(map(int, re.findall(r'\d+', test_string)))[0])
    newfiles.sort()
    lines = len(newfiles)
    # initialize values
    linecount = 0
    begin = 0
    end = 10

    while linecount <= lines:
        multiline = """
New files:
```
{}
```
""".format("\n".join(newfiles[begin:end]).strip())
        begin += 10
        end += 10
        linecount += 10
        webhook = DiscordWebhook(url=WEBHOOK_URL, content=multiline)

        try:
            webhook.execute()
        except discord.HTTPException as exc:
            print(datetime.datetime.now().replace(microsecond=0).isoformat(), "HTTP exception:", exc)
            second_try()
        except discord.DiscordException as exc:
            print(datetime.datetime.now().replace(microsecond=0).isoformat(), "Discord exception:", exc)
            second_try()
        else:
            print(datetime.datetime.now().replace(microsecond=0).isoformat(), "New files, sent webhook")

    sys.exit(0)
