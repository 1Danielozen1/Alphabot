import socket
from threading import Thread

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_adress = ("192.168.1.137",6969)
s.connect(server_adress)
buffer_size = 4096
inizia = False

class ContinuaARicevere(Thread):
    def __init__(self):
        super().__init__()
        self.tempo = 0

    def run(self):
        while True:
            self.tempo = s.recv(buffer_size)
            print(self.tempo.decode())

temp = ContinuaARicevere()

while True:
    com = input("Inserisci il comando: ")

    # sendall
    s.sendall(f"{com}".encode())
    
    if inizia == False:
        temp.start()
        inizia = True

    if com == "e": # se il testo è uguale a uno di questi messaggi esce dal ciclo.
        break

s.close()
