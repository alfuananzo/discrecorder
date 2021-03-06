from flask import Flask, render_template, url_for, request
app = Flask(__name__)
import sqlite3
#from sys import argv
from operator import itemgetter

conn = sqlite3.connect('/tmp/discord.db')
c = conn.cursor()

@app.route('/')
def home():
    url_for('static', filename='style.css')
    return render_template('index.html')

@app.route('/user')
def userinfo():
    url_for('static', filename='style.css')
    userinfo = c.execute("SELECT * from user_info").fetchall()
    return render_template('userinfo.html', userinfo=userinfo)
#
@app.route('/friends')
def friendlist():
    url_for('static', filename='style.css')
    friendlist = c.execute("SELECT * from friend_list").fetchall()
    return render_template('friendlist.html', friendlist=friendlist)

@app.route('/users')
def knownusers():
    url_for('static', filename='style.css')
    knownusers = c.execute("SELECT * from known_users").fetchall()
    return render_template('knownusers.html', knownusers=knownusers)

#
@app.route('/chat', methods=['GET', 'POST'])
@app.route('/chat/<sort>')
def chatlog(sort=""):
    url_for('static', filename='style.css')

    results = c.execute('SELECT * FROM chat_log').fetchall()
    if request.method == 'POST':
        filter = request.form['filter']
    else:
        filter = ""

    chatlog_list = []
    channel_list = []
    for log_entry in results:
        filter_in = False

        if any(str(filter).lower() in str(entry).lower() for entry in log_entry):
            filter_in = True
        call_entry = ""
        attachments = ""
        edited = ""
        if log_entry[0] not in channel_list:
            channel_list.append(log_entry[0])
        if log_entry[4] != "":
            tmp_entry = log_entry[4].split(";")
            call_participants = tmp_entry[0].split(",")
            call_entry = [call_participants, tmp_entry[1], tmp_entry[2], tmp_entry[3]]
            if filter == "call":
                filter_in = True

        if log_entry[5] != "":
            if filter == "attachment":
                filter_in = True
            attachments = log_entry[5].split(";")

        if log_entry[6] != "":
            if filter == "edited":
                filter_in = True
            edited = " Message edited on: " + str(log_entry[6])

        if filter_in:
            chatlog_list.append((log_entry[0], log_entry[1], log_entry[2], log_entry[3], call_entry, attachments, edited))

    if sort != "":
        if sort == "channelID":
            if request.args["order"] == "asc":
                chatlog_list.sort(key=itemgetter(0))
            else:
                chatlog_list.sort(key=itemgetter(0))
                chatlog_list = reversed(chatlog_list)
        if sort == "time":
            if request.args["order"] == "asc":
                chatlog_list.sort(key=itemgetter(1))
            else:
                chatlog_list.sort(key=itemgetter(1))
                chatlog_list = reversed(chatlog_list)
        if sort == "user":
            if request.args["order"] == "asc":
                chatlog_list.sort(key=itemgetter(2))
            else:
                chatlog_list.sort(key=itemgetter(2))
                chatlog_list = reversed(chatlog_list)
        if sort == "content":
            if request.args["order"] == "asc":
                chatlog_list.sort(key=itemgetter(3))
            else:
                chatlog_list.sort(key=itemgetter(3))
                chatlog_list = reversed(chatlog_list)


    return render_template('chatlogs.html', chatlog=chatlog_list, channels=channel_list)
app.run(host= '0.0.0.0')
