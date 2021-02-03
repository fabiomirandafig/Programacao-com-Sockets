#Fábio Miranda Figueiredo 92550
#Eliel N de Souza         92564

import threading
import socket
import tqdm
import os

HOST = ''
PORT = 20000
orig = (HOST, PORT)
SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 32

clientVector = []     #Vetor de clientes que armazena nome e endereço (HOST e porta de saída)
filename = ''

#--------------------Função para tratar envio e recebimento de arquivos--------------------------
def tcpConnection(msgTcp):
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp.bind(orig)
    tcp.listen(5)
    con, cliente = tcp.accept()
    print("Conexão TCP foi feita no servidor!!\n")
    #------------Trata o recebimento de um arquivo----------------------------------
    if "/file" in msgTcp:
        received = con.recv(BUFFER_SIZE).decode()
        filename, filesize = received.split(SEPARATOR)
        filename = os.path.basename(filename)
        filesize = int(filesize)

        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "wb") as f:
            for _ in progress:
                bytes_read = con.recv(BUFFER_SIZE)
                if not bytes_read:
                    break
                f.write(bytes_read)
                progress.update(len(bytes_read))
        print('Arquivo recebido pelo servidor!!\n')
    #------------Trata o envio de um arquivo----------------------------------------
    elif "/get" in msgTcp:
        filename = msgTcp[5:]

        filesize = os.path.getsize(filename)
        con.send(f"{filename}{SEPARATOR}{filesize}".encode())

        progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "rb") as f:
            for _ in progress:
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    break
                con.sendall(bytes_read)
                progress.update(len(bytes_read))
        print("Arquivo enviado pelo servidor!!\n")
    #----Fecha conexão TCP------------
    con.close()
    tcp.close()
    return

#--------------------Estabelece conexão UDP---------------------
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp.bind(orig)

while True:
    isIn = False
    nomeClienteOrigem = ""
    messageFromClientEncode, address = udp.recvfrom(1024)
    messageFromClient = messageFromClientEncode.decode()
    aux, portaSaidaClient = address
    #-------------------Trata o envio e recebimento de arquivos-----------------------------
    if "/file" in messageFromClient or "/get" in messageFromClient:
        for x in clientVector:
            nomeCliente, enderecoCliente = x
            if enderecoCliente == address:
                nomeClienteOrigem = nomeCliente
        if "/file" in messageFromClient:
            tcpConnection(messageFromClient)
            message = nomeClienteOrigem + ' enviou ' + messageFromClient[6:]
            for x in clientVector:
                nomeCliente, enderecoCliente = x
                if enderecoCliente != address:
                    udp.sendto(message.encode(), enderecoCliente)
        elif "/get" in messageFromClient:
            if os.path.isfile(messageFromClient[5:]) == False:
                udp.sendto('O arquivo requisitado não está disponível!'.encode(), address)
            elif os.path.isfile(messageFromClient[5:]) == True:
                udp.sendto('O arquivo requisitado está disponível!'.encode(), address)
                tcpConnection(messageFromClient)
        continue
    #-------------------Trata a saída de um cliente------------------------------------------
    if messageFromClient == '/bye':
        nomeClienteOrigem = ""
        message = ""
        nomeClienteSaindo = ""
        enderecoClienteSaindo = ""
        for x in clientVector:
            nomeCliente, enderecoCliente = x
            if enderecoCliente == address:
                nomeClienteOrigem = nomeCliente
                nomeClienteSaindo = nomeCliente
                enderecoClienteSaindo = enderecoCliente
                message = nomeClienteOrigem + " saiu"
                break;
        for x in clientVector:
            nomeCliente, enderecoCliente = x
            if enderecoCliente != address:
                udp.sendto(message.encode(), enderecoCliente)

        udp.sendto('/bye'.encode(), address)
        clientVector.remove([nomeClienteSaindo, address])
        continue

    #-------------------Trata a inclusão de um novo cliente ou envio de mendagem-------------

    #-------------------Se a porta de saída já está na lista, então é umas mensagem----------
    for x in clientVector:
        nomeCliente, enderecoCliente = x
        if enderecoCliente == address:
            nomeClienteOrigem = nomeCliente
            isIn = True
            break
    #-------------------Se a porta de saída não está na lista, então é um cliente novo-------
    if isIn == False:
        clientVector.append([messageFromClient, address])
        print('O cliente ', messageFromClient, ' foi adicionado à lista!\n')
        print('Nova lista: ', clientVector)

        for x in clientVector:
            nomeCliente, enderecoCliente = x
            if enderecoCliente != address:
                message = messageFromClient + " entrou";
                udp.sendto(message.encode(), enderecoCliente)

    else:
        #-------- Lista os clientes conectados atualmente--------------------------
        if messageFromClient == '/list':
            message = 'Clientes conectados: '
            for x in clientVector:
                nomeCliente, enderecoCliente = x
                message = message + nomeCliente + ', '
            udp.sendto(message.encode(), address)
        #-------- Envio de mensagens normais --------------------------------------
        else:
            for x in clientVector:
                nomeCliente, enderecoCliente = x
                if enderecoCliente != address:
                    message = nomeClienteOrigem + " disse: " + messageFromClient;
                    udp.sendto(message.encode(), enderecoCliente)

udp.close()
