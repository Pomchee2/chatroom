from flask import Flask, request, send_from_directory, json
import pymysql
from flask_cors import CORS, cross_origin
import time
import os
app = Flask(__name__, static_url_path='')

conn = pymysql.connect(host="localhost",
		       user="admin",
		       passwd=os.environ["SQLPASS"],
		       database="chatroom",
		       port=3306
		       )

CORS(app)

currID = 0
connections = {} 

def generate_connectionID():
  global currID
  currID += 1
  return currID

@app.route("/chatroom/showmessages", methods=["POST"])
def show_messages():
    global conn
    global connections
    cursor = conn.cursor()
    content = request.json
    print(content)
    timestamp = int(content["timestamp"])
    ret = []
    print(type(timestamp))
    cursor.execute("SELECT users.USERNAME, messages.MESSAGE_CONTENT, messages.TIMESTAMP FROM users, messages WHERE users.USER_ID = messages.USER_ID AND messages.TIMESTAMP > %s ORDER BY messages.TIMESTAMP ASC", [timestamp])
    for message in cursor.fetchall():
      ret.append({"username": message[0], "message": message[1], "timestamp": message[2]})


    if len(ret) == 0:
        connectionID = generate_connectionID()    
        connections[connectionID] = None
        while connections[connectionID] == None:
          time.sleep(0.5)
        ret.append(connections[connectionID])

    cursor.close()

    return json.dumps(ret)

@app.route("/")
def hello():
    return "<h1>Hello World!</h1>"


@app.route("/chatroom/sendmessage", methods=["POST"])
def add_message():
    global conn
    global connections
    cursor = conn.cursor()
    content = request.json
    timestamp = int(time.time() * 1000)

    print("Name:",content["name"])
    cursor.execute("SELECT USER_ID FROM users WHERE USERNAME=%s", [content["name"]])
    userID = cursor.fetchone()
    print(userID)

    if userID == None:
        cursor.execute("INSERT INTO users (USERNAME) VALUES (%s)", [content["name"]])
        conn.commit()
        cursor.execute("SELECT LAST_INSERT_ID()")
        userID = cursor.fetchone()
        print(userID)
    userID = userID[0]

    if userID != 13:
        print("user id unexpected error")
    cursor.execute("INSERT INTO messages (USER_ID, MESSAGE_CONTENT, TIMESTAMP) VALUES (%s, %s, %s)", [int(userID), content["message"], timestamp])
    conn.commit()
    for key in connections:
        connections[key] = {"username": content["name"], "message": content["message"], "timestamp": timestamp}

    cursor.close()
    return ("", 200)


@app.route("/public/<path:path>")
def send_js(path):
    return send_from_directory(public, path)

if __name__ == "__main__":
    app.run(threaded=True, host="0.0.0.0")
