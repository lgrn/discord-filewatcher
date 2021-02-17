#!/usr/bin/env python3

import os
import sys
import sqlite3
import datetime
from discord_webhook import DiscordWebhook

PATH_TO_WATCH="/tmp"
WEBHOOK_URL = ""
# "ignore" means don't notify, nothing more.
IGNORE_FILES = ["txt","tmp"]

conn = sqlite3.connect("new_files.sqlite")
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS files (mtime REAL NOT NULL, filename VARCHAR NOT NULL, unique(mtime,filename));")
max_mtime = 0
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
if int(cur.fetchone()[0]) <= 0:
    print("This is an initial run, it will take some time to fill the database. Be patient.")
    print("No new files will be returned, since there's nothing to compare to.")
    print("Estimated folders to check:", len(list(os.walk(PATH_TO_WATCH))))
    scan_and_import()
    print("Done. Create a new file and run me again to test.")
    conn.commit()
    conn.close()
else:
    add, skip, new = scan_and_import()
    conn.commit()
    conn.close()
    newfiles = []
    if not new:
        curtime = datetime.datetime.now().replace(microsecond=0).isoformat()
        print(f"{curtime} Skipped {skip} files, nothing new")
        sys.exit(0)
    else:
        for i in new:
            # -1 refers to the file ending at the end of the path
            if i.split('.')[-1] not in IGNORE_FILES:
                path = i.split('/')
                # -1 refers to the filename
                newfiles.append(path[-1])
if newfiles:
    newfiles.sort()
    multiline = """
    New files:
    ```
    {}
    ```
    """.format("\n".join(newfiles[0:]))
    webhook = DiscordWebhook(url=WEBHOOK_URL, content=multiline)
    response = webhook.execute()
    print(datetime.datetime.now().replace(microsecond=0).isoformat(), "Discord notified, response:", response)
    sys.exit(0)
else:
    print(datetime.datetime.now().replace(microsecond=0).isoformat(), "New files, but nothing of note.")
    sys.exit(0)
