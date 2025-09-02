import socket
import threading
import json

clients = []
nicknames = []
colors = []

HOST = "0.0.0.0"
CHAT_PORT = 50000  # TCP for chat messages
PING_PORT = 50020  # UDP for server discovery

colorIndex = 1  # Global color index for new clients

# Ask for server name
serverName = input("Select server name\n").strip() or "DefaultServer"
print(f"{serverName} is listening...")

# TCP for chat messages
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, CHAT_PORT))
server.listen()

# UDP for discovery pings
serverPing = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverPing.bind((HOST, PING_PORT))


def broadcast(message, exclude_client=None):
    """Send message to all clients, except optional excluded one."""
    for client in clients:
        if client == exclude_client:
            continue
        try:
            client.send(message)
        except:
            pass


def handle(client):
    """Handle chat messages from a single client."""
    try:
        index = clients.index(client)
        clientColor = colors[index]
    except ValueError:
        return  # client not in list

    while True:
        try:
            data = client.recv(1024)
            if not data:
                disconnectClient(client)
                break

            rawTuple = tuple(json.loads(data.decode("ascii")))
            nickname, message = rawTuple

            if message.strip() == "":
                continue
            elif message == "EXIT":
                disconnectClient(client)
                break

            formatted = f"\033[3{clientColor}m{nickname}\033[0m: {message}".encode("ascii")
            broadcast(formatted)
        except:
            disconnectClient(client)
            break


def disconnectClient(client):
    """Remove client safely."""
    try:
        index = clients.index(client)
    except ValueError:
        return  # already removed

    clientColor = colors[index]
    nickname = nicknames[index]

    try:
        client.send("EXIT".encode("ascii"))
        client.close()
    except:
        pass

    clients.pop(index)
    nicknames.pop(index)
    colors.pop(index)

    broadcast(f"[SERVER] \033[3{clientColor}m{nickname}\033[0m left the chat!".encode("ascii"))


def getping():
    """Respond to UDP ping requests."""
    while True:
        data, addr = serverPing.recvfrom(1024)
        if not data:
            continue
        payload = {
            "serverName": serverName,
            "clientCount": len(clients),
            "chatPort": CHAT_PORT,
        }
        serverPing.sendto(json.dumps(payload).encode("ascii"), addr)


def getNewUsers():
    """Accept new clients and assign colors."""
    global colorIndex

    while True:
        clientSocket, addr = server.accept()
        print(f"Connected with {addr}")

        # Assign color
        assignedColor = colorIndex + 2
        colors.append(assignedColor)
        colorIndex += 1
        if colorIndex > 5:
            colorIndex = 1

        # Handle nickname
        clientSocket.send("NICKNAME1234".encode("ascii"))
        nickname = clientSocket.recv(1024).decode("ascii")
        nicknames.append(nickname)
        clients.append(clientSocket)

        broadcast(f"[SERVER] \033[3{assignedColor}m{nickname}\033[0m joined the chat!".encode("ascii"))
        clientSocket.send("Connected to server!".encode("ascii"))

        threading.Thread(target=handle, args=(clientSocket,), daemon=True).start()


# Start threads
threading.Thread(target=getNewUsers, daemon=True).start()
threading.Thread(target=getping, daemon=True).start()

# Wait for server admin to exit
input("Press enter to exit server\n")
print("Exiting...")
broadcast("SERVER IS CLOSING".encode("ascii"))
for client in clients:
    try:
        client.send("EXIT".encode("ascii"))
        client.close()
    except:
        pass
server.close()
