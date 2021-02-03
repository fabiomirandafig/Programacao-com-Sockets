#Fábio Miranda Figueiredo 92550
#Eliel N de Souza         92564
import socket
import threading
import time
import tqdm
import sys
import os

HOST = '127.0.0.1'
PORT = 20000
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest = (HOST, PORT)
SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 32
msgEspecial = ""

#----------Envia a primeira mensagem contendo o nome do cliente---------------
username = input('Nome de usuário: ')
udp.sendto(username.encode(), dest)
print('Para sair digite "/bye"\n')

#----------Estabelece conexão TCP --------------------------------------------
def tcpConnection(msgTcp):
    time.sleep(0.1) #Delay para que dê tempo do servidor ficar esperando conexão
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.connect(dest)
    #-------Trata o envio de um arquivo---------------------------------------
    if "/file" in msgTcp:
        filename = msgTcp[6:]

        filesize = os.path.getsize(filename)
        tcp.send(f"{filename}{SEPARATOR}{filesize}".encode())

        progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "rb") as f:
            for _ in progress:
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    break
                tcp.sendall(bytes_read)
                progress.update(len(bytes_read))
    #-------Trata o recebimento de um arquivo--------------------------------
    elif "/get" in msgTcp:
        filename = ''
        received = tcp.recv(BUFFER_SIZE).decode()
        filename, filesize = received.split(SEPARATOR)
        filename = os.path.basename(filename)
        filesize = int(filesize)

        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "wb") as f:
            for _ in progress:
                bytes_read = tcp.recv(BUFFER_SIZE)
                if not bytes_read:
                    break
                f.write(bytes_read)
                progress.update(len(bytes_read))
    tcp.close()
    return
#------Função para receber mensagens----------------------------------------
def toRecv():
    while True:
        msgFromServer, serv = udp.recvfrom(1024)
        msgDecoded = msgFromServer.decode()
        global msgEspecial
        if msgDecoded == "/bye":
            sys.exit()
            break
        if "/get" in msgEspecial:
            if msgDecoded == "O arquivo requisitado está disponível!":
                tcpConnection(msgEspecial)
                msgEspecial = ""
            if msgDecoded == "O arquivo requisitado não está disponível!":
                print(msgDecoded)
                msgEspecial = ""
        elif "/get" not in msgEspecial:
            print(msgDecoded)
    return
#------Função para enviar mensagens-----------------------------------------
def toSend():
    msg = input()
    while True:
        if msg == "/bye":
            udp.sendto(msg.encode(),dest)
            break
        if "/file" in msg or "/get" in msg:
            if "/file" in msg and os.path.isfile(msg[6:]) == False:
                print("O arquivo não existe no diretório!")
            elif "/file" in msg and os.path.isfile(msg[6:]) == True:
                udp.sendto(msg.encode(),dest)
                tcpConnection(msg)
            if "/get" in msg:
                global msgEspecial
                msgEspecial = msg
                udp.sendto(msg.encode(),dest)
            msg = input()
            continue
        udp.sendto(msg.encode(),dest)
        msg = input()
    udp.close()
    sys.exit()
    return

t = threading.Thread(target=toSend, args=()) #----- Thread para enviar mensagens -------
t1 = threading.Thread(target=toRecv, args=()) #---- Thread receber mensagens -----------
t.start()
t1.start()
