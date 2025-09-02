import socket
import threading
import json
import time

CHAT_PORT = 50000  # TCP for chat messages
PING_PORT = 50020  # UDP for server discovery


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
pingClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
pingClient.bind(("0.0.0.0", PING_PORT))
pingClient.settimeout(2)

selectedServers = []
doLoop = False

def GetPing():
    global doLoop
    mockIndex = 1
    while doLoop:
        try:
            data, addr = pingClient.recvfrom(1024)
            if data.decode() == "Ping":
                continue
            payload = json.loads(data.decode())
            print(f"{mockIndex}. {payload['serverName']} {payload['clientCount']} active")
            # Use the *source addr* as server IP
            selectedServers.append((addr[0], payload['chatPort']))
            mockIndex += 1
        except socket.timeout:
            continue

def PingAllServers():
    selectedServers.clear()
    global doLoop
    doLoop = True
    threading.Thread(target=GetPing, daemon=True).start()

    pingClient.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    pingClient.sendto("Ping".encode("ascii"), ("192.168.0.255", PING_PORT))

    time.sleep(2)
    doLoop = False

def askForName():
    global nickname
    nickname = input("Whats your name\n").strip()
    if nickname == "":
        print("cant be nothing!")
        return askForName()

def startConnection(addr):
    global client  # make sure we reassign
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # create a new socket
    try:
        client.connect(addr)
    except Exception as e:
        print(f"Could not connect to server: {e}")
        return
    threading.Thread(target=recieve, daemon=True).start()
    send()
def recieve():
    while True:
        try:
            message = client.recv(1024).decode("ascii")
            if message == "NICKNAME1234":
                client.send(nickname.encode("ascii"))
            elif message == "EXIT":
                client.close()
            else:
                # Print message cleanly above the prompt
                print(f"\n{message}")
                print("> ", end="", flush=True)
        except:
            client.close()
            break

def send():
    while True:
        try:
            # Show prompt nicely
            message1 = input("> ")
            if not message1.strip():
                continue  # skip empty sends
            realMessage = json.dumps((nickname, message1))
            client.send(realMessage.encode())
        except:
            break

def selectServer():
    option = input("Which server (numbers): ")
    if not option.isnumeric():
        print("invalid!!!")
        return selectServer()
    option = int(option)
    if 1 <= option <= len(selectedServers):
        addr = selectedServers[option - 1]
        print(f"Selected {addr}...")
        return startConnection(addr)
    else:
        print("invalid!!!")

def MainLoop():
    while True:
        print("\n1.Refresh Servers\n2.Select server to connect\n3.Change nickname")
        option = input()
        if option == "1":
            PingAllServers()
        elif option == "2":
            selectServer()
        elif option == "3":
            askForName()
        else:
            print("Invalid option!")

askForName()
MainLoop()
