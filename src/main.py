from flask import Flask, request, send_from_directory, json
from flask.ext.mysql import MySQL
from flask_cors import CORS, cross_origin
import time
app = Flask(__name__, static_url_path='')

mysql = MySQL()

app.config["MYSQL_DATABASE_USER"] = "root"
app.config["MYSQL_DATABASE_PASSWORD"] = ""
app.config["MYSQL_DATABASE_DB"] = "chatroom"
app.config["MYSQL_DATABASE_HOST"] = "localhost"
mysql.init_app(app)

CORS(app)

conn = mysql.connect()

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

    cursor.execute("SELECT USER_ID FROM users WHERE USERNAME=%s", [content["name"]])
    userID = cursor.fetchone()[0]
    print(userID)

    if userID == 0:
        cursor.execute("INSERT INTO users (USERNAME) VALUES (%s)", [content["name"]])
        conn.commit()
        cursor.execute("SELECT LAST_INSERT_ID()")
        userID = cursor.fetchone()[0]
        print(userID)

    cursor.execute("INSERT INTO messages (USER_ID, MESSAGE_CONTENT, TIMESTAMP) VALUES (%s, %s, %s)", [int(userID), content["message"], timestamp])
    conn.commit()
    for key in connections:
        connections[key] = {"username": content["name"], "message": content["message"], "timestamp": timestamp}

    return ("", 200)


@app.route("/public/<path:path>")
def send_js(path):
    return send_from_directory(public, path)

if __name__ == "__main__":
    app.run(threaded=True)
