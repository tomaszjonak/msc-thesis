# import socketserver
import socket

sock = socket.create_connection(('localhost', 1234))
while True:
    sock.send(input('$ ').encode('utf8'))
    print(sock.recv(8192))
