import json
import os
import datetime
import sqlite3
from sys import argv
from shutil import copyfile

#output_dir = "/sne/home/fmijnen/discord_extract_windows/"
output_dir = argv[1]
working_dir = output_dir + "/data/"

conn = sqlite3.connect(working_dir + "sqlite_db/" + 'discord.db')
c = conn.cursor()

c.execute("""CREATE TABLE "chat_log" (
    `ChannelID`	INTEGER,
    `Datetime`	TEXT,
    `Username`	TEXT,
    `Content`	TEXT,
    `Call`	TEXT,
    `Attachment`	TEXT,
    `Edit`	TEXT
)""")

c.execute("""CREATE TABLE "friend_list" (
    `ID`	INTEGER,
    `Name`	TEXT
)""")

c.execute("""CREATE TABLE `known_users` (
    `ID`	INTEGER,
    `Username`	TEXT
)""")

c.execute("""CREATE TABLE "user_info" (
    `ID`	INTEGER,
    `Username`	TEXT,
    `Email`	TEXT
)""")

try:
    user_info = json.load(open(working_dir + "userinfo.json", "r"))
except:
    user_info = {"id" : "null", "username": "null", "user_info": "null"}

try:
    friend_list = json.load(open(working_dir + "friendlist.json", "r"))
except:
    friend_list = []

c.execute("INSERT INTO user_info VALUES (?, ?, ?)", [user_info["id"], user_info["username"], user_info["email"]])

# Build chat log
working_dir += "/chat_history/"


chat_dir = os.listdir(working_dir)
chat_log = []

for json_file in chat_dir:
    chat_log.append(json.load(open(working_dir + json_file)))

# Build known users
users_known = {user_info["id"]: user_info["username"]}

for friend in friend_list:
    if friend["user"]["id"] not in users_known:
        users_known[friend["user"]["id"]] = friend["user"]["username"]
    c.execute("INSERT INTO friend_list VALUES (?, ?)", [ friend["user"]["id"], friend["user"]["username"]])


# Build a list of known users + ID's
for chat_entry in chat_log:
    for entry in chat_entry:
        if entry["author"]["id"] not in users_known:
            users_known[entry["author"]["id"] ]= entry["author"]["username"]

# print("Known users:")
for user in users_known.items():
    # print("ID:", user[0], "name:", user[1])
    c.execute("INSERT INTO known_users VALUES (?, ?)", user)
# print()

for chat_entry in chat_log:
    # print("Displaying data for channel", chat_entry[0]["channel_id"])
    for entry in reversed(chat_entry):
        call_info = ""
        attachment_info = ""
        edit_time = ""
        message_date = datetime.datetime.strptime(entry["timestamp"].split(".")[0], "%Y-%m-%dT%H:%M:%S")
        if "call" in entry:
            # print("\nCall found")
            # print("Participants:")
            edit_time = ""

            for participant in entry["call"]["participants"]:
                try:
                    # print(users_known[participant])
                    call_info += users_known[participant] + ","
                except KeyError:
                    # print("Unknown user:\t\t", participant)
                    call_info += participant + ","

            call_info = call_info[:-1] + ";"
            end_call = datetime.datetime.strptime(entry["call"]["ended_timestamp"].split(".")[0], "%Y-%m-%dT%H:%M:%S")
            # print("Call start:\t\t", message_date)
            call_info += str(message_date) + ";"
            # print("Call end:\t\t", end_call)
            call_info += str(end_call) + ";"
            # print("Call duration:\t", end_call - message_date, "\n")
            call_info += str(end_call - message_date)

        if entry["attachments"]:
            # print("\nAttachment found:")
            # print(message_date, entry["author"]["username"] + ":", entry["content"])
            for att_entry in entry["attachments"]:
                # print("filename:", att_entry["filename"])
                # print("URL:", att_entry["url"] + "\n")
                attachment_info += att_entry["filename"] + ";" + att_entry["url"] + ","
                os.system("wget -q --directory-prefix " + str(output_dir) + "attachments/ " + str(att_entry["url"]))
            attachment_info = attachment_info[:-1]



            # print(message_date, entry["author"]["username"] + ":", entry["content"])

        if entry["edited_timestamp"]:
            edit_time = datetime.datetime.strptime(entry["edited_timestamp"].split(".")[0], "%Y-%m-%dT%H:%M:%S")
            # print("This message was edited on:", edit_time)

        c.execute("INSERT INTO chat_log VALUES (?, ?, ?, ?, ?, ?, ?)", [chat_entry[0]["channel_id"],
                                                                    str(message_date), entry["author"]["username"],
                                                                     entry["content"], call_info, attachment_info,
                                                                     str(edit_time)
                                                                     ])


conn.commit()
conn.close()

copyfile(output_dir + "/data/sqlite_db/discord.db", "/tmp/discord.db")
os.system("export FLASK_APP=serv.py ; flask run")
