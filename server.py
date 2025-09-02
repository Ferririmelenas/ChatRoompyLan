import socket
import threading
import json

colorIndex = 1

clients = []
nicknames = []
colors =  []

HOST = "0.0.0.0"
CHAT_PORT = 50000  # TCP for chat messages
PING_PORT = 50020  # UDP for server discovery


def GetServerName():
    global serverName
    serverName = input("Select server name\n")
    if serverName == "":
        serverName = "DefaultServer"

GetServerName()
print(serverName + " is listening...")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, CHAT_PORT))
server.listen()

serverPing = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverPing.bind((HOST, PING_PORT))

def broadcast(message):
    for client in clients:
        try:
            client.send(message)
        except:
            pass  # ignore broken connections

def handle(client):
    index = clients.index(client)
    while True:
        try:

            jsonTupleMessage = client.recv(1024).decode()
            rawTuple = tuple(json.loads(jsonTupleMessage))


            nickname,message = rawTuple

            if message == "":
                continue 
            elif message == "EXIT":
                print(f"{nickname} left!")
                disconnectClient(client)
                break
            concatenatedMessage = f"\033[3{str(colors[index])}m{nickname}\033[0m: {message}".encode("ascii")
            broadcast(concatenatedMessage)
        except:
            if client in clients:
               disconnectClient(client)
            break
def disconnectClient(client):
    index = clients.index(client)
    client.send("EXIT".encode("ascii"))
    client.close()
    nickname = nicknames[index]
    clients.pop(index)
    nicknames.pop(index)
    colors.pop(index)
    broadcast(f"[SERVER] \033[3{str(colors[colorIndex])}m{nickname}\033[0m left the chat!".encode("ascii"))
def getping():
    while True:
        print("listening for pings...")
        data, addr = serverPing.recvfrom(1024)
        print(f"Recieved ping from {addr}")
        payload = {
            "serverName": serverName,
            "clientCount": len(clients),
            "chatPort": CHAT_PORT,
        }
        serverPing.sendto(json.dumps(payload).encode(), addr)


def getNewUsers():
    global colorIndex
    while True:
        newSocket, Address = server.accept()
        print(f"Connected with {str(Address)}")
        if colorIndex == 7:
            colorIndex = 3
        colors.append(colorIndex)
        newSocket.send("NICKNAME1234".encode("ascii"))
        nickname = newSocket.recv(1024).decode()
        nicknames.append(nickname)
        clients.append(newSocket)
        
        broadcast(f"[SERVER] \033[3{str(colors[colorIndex])}m{nickname}\033[0m joined the chat!".encode("ascii"))
        newSocket.send("Connected to server!".encode("ascii"))

        thread = threading.Thread(target=handle, args=(newSocket,))
        thread.start()
        colorIndex += 1

threading.Thread(target=getNewUsers).start()
threading.Thread(target=getping).start()

input("Press enter to exit server")
print("exiting")
broadcast("SERVER IS CLOSING")
server.close()
for client in clients:
    client.send("EXIT".encode("ascii"))
    client.close()
    
exit()
