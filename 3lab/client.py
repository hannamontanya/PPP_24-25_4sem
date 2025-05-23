import threading
import requests
import websocket
import getpass
import os.path
import json

from app.core.config import SERVER_HOST, SERVER_PORT, OAUTH_ENDPOINT


def on_open(ws):
    #print("\nopened connection")
    #ws.send("Halo!")
    pass

def on_message(ws, message):
    try:
        res = json.loads(message)
    except ValueError as e:
        print("\n" + message)
        return
    if 'status' in res:
        if res['status'] == 'STARTED':
            print(f"\nBruteforce task started. Task id={res['task_id']}")
        elif res['status'] == 'COMPLETED':
            print(f"\nBruteforce task completed. Task id={res['task_id']}")
        elif res['status'] == 'CANCELLED':
            print(f"\nBruteforce task cancelled. Task id={res['task_id']}")
    print(json.dumps(res))

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    #print("\nclosed connection")
    pass

def print_help():
    print("Enter your command below. Available commands:")
    print("help - print help")
    print("start hash charset maxlen - start bruteforce task. Parameters:")
    print("\thash - string or file with RAR hash")
    print("\tcharset - string with letters from a password")
    print("\tmaxlen - maximum length of a password")
    print("stop task-id - cancel and stop bruteforce task. Parameters:")
    print("\ttask-id - id of a bruteforce task to stop")
    print("info task-id - print bruteforce task information. Parameters:")
    print("\ttask-id - id of a bruteforce task")
    print("exit - exit client\n")

def send_start_bruteforce_task(ws, data):
    args = list(filter(None, data.split()))
    if len(args) != 4:
        raise ValueError("Wrong number of arguments! Command format is 'start hash-string-or-file password-charset max-password-length")
    # if first argument (args[1]) is a file - read file contents and use them as a hash
    if os.path.isfile(args[1]):
        with open(args[1], 'r') as file:
            hash = file.read()
            data = data.replace(args[1], hash.strip())
    if not args[3].isdigit():
        raise ValueError("maxlen (argument 3) should be a number")
    ws.send(data)

def send_stop_bruteforce_task(ws, data):
    args = list(filter(None, data.split()))
    if len(args) != 2:
        raise ValueError("Wrong number of arguments! Command format is 'stop task-id")
    if not args[1].isdigit():
        raise ValueError("task-id (argument 1) should be a number")
    ws.send(data)

def send_info_bruteforce_task(ws, data):
    args = list(filter(None, data.split()))
    if len(args) != 2:
        raise ValueError("Wrong number of arguments! Command format is 'info task-id")
    if not args[1].isdigit():
        raise ValueError("task-id (argument 1) should be a number")
    ws.send(data)


# ********************** MAIN ***********************

print("\nRAR password finder websocket client\n")

# authorization
authenticated = False
while not authenticated:
    login = input('Email: ')
    password = getpass.getpass()
    response = requests.post(f"http://{SERVER_HOST}:{SERVER_PORT}{OAUTH_ENDPOINT}", data={ "username": login, "password": password })
    data = response.json()
    if 'access_token' not in data:
        print(str(data))
        print('No access token in response. Wrong email or password maybe?')
    else:
        authenticated = True

header="Authorization: Bearer " + data['access_token']
#print(header)
#websocket.enableTrace(True)

#conn = websocket.create_connection(f"ws://{SERVER_HOST}:{SERVER_PORT}/ws", header=[header])
#conn.send("Halo!")
#result = conn.recv()
#assert result is not None

print_help()

# init websocket
ws = websocket.WebSocketApp(f"ws://{SERVER_HOST}:{SERVER_PORT}/ws", header=[header], 
                            on_open=on_open, 
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close) 

wst = threading.Thread(target=lambda: ws.run_forever())
wst.daemon = True
wst.start()

# main loop
cmd = ""
while cmd != "exit":
    data = input("")
    cmd = data.strip().lower()
    if cmd == "help":
        print_help()
    elif cmd.find("start") == 0:    
        try:
            send_start_bruteforce_task(ws, data)
        except ValueError as e:
            print(str(e))
    elif cmd.find("stop") == 0:    
        try:
            send_stop_bruteforce_task(ws, data)
        except ValueError as e:
            print(str(e))
    elif cmd.find("info") == 0:    
        try:
            send_info_bruteforce_task(ws, data)
        except ValueError as e:
            print(str(e))
    else:
        ws.send(cmd)

ws.close()