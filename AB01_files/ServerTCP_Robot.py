import socket
from threading import Thread
import AlphaBot
import time

# dichiaro l'indirizzo il buffer size e la lista dei client
my_address = ("192.168.1.137", 6969)
buffer_size = 4096
client_list = []

# creo il robot
gino = AlphaBot.AlphaBot()

# socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind
s.bind(my_address)
# listen
s.listen()

class InvioContinuo(Thread):
    def __init__(self, connection, address):
        super().__init__()
        self.conn = connection
        self.add = address

    def run(self):
        ost = "OB_N"
        while True:
            sens = gino.sensors()
            if ost != sens:
                if sens == "OB_R" and ost != "OB_R":
                    self.conn.sendall(f"Ostacolo a destra".encode())
                elif sens == "OB_L" and ost != "OB_L":
                    self.conn.sendall(f"\nOstacolo a sinistra".encode()) 
                elif sens == "OB_ALL" and ost != "OB_ALL":
                    self.conn.sendall(f"\nC'è un muro davanti a me".encode())
                else:
                    self.conn.sendall(f"\nNon vedo nulla".encode())
            ost = sens
            time.sleep(0.5)


class ClientThread(Thread):
    def __init__(self, connection, address):
        super().__init__()
        self.tempo = InvioContinuo(connection,address)
        self.conn = connection
        self.add = address
        self.isRunning = True


    def run(self):
        #LOOP
        cont = False
        while self.isRunning:
            # ricevo il messaggio dal client
            text_recived = self.conn.recv(buffer_size).decode()

            if cont == False:
                self.tempo.start()
                cont = True

            # creo un dizionatio con i comandi
            dict_commands = {"f":gino.forward,"b":gino.backward,"l":gino.left,"r":gino.right, "s":gino.stop }

            # salvo il comando ricevuto
            com = text_recived.split(";")
            comando = com[0]
            distanza = float(com[1])

            if distanza <= 0:
                distanza = 0.0
            elif distanza > 5:
                distanza = 5.0
            else: pass

            # stampo quello che riceve il robot
            print(f"{comando} da {add}")

            # controllo il comando e eseguo una azione
            if comando == "e":
                break
            elif comando == "?":
                self.conn.sendall(f"f = avanti\nb = indietro\nr = destra\nl = sinistra\ns = ferma\n".encode())
            else:
                print(f"{comando}")
            if comando in dict_commands:
                dict_commands["s"]()
                dict_commands[comando]()
                time.sleep(distanza)
                dict_commands["s"]()
            else:
                dict_commands["s"]()


while True:
# accept e carica il client nel thread
    conn, add = s.accept()
    client = ClientThread(conn, add)
    client_list.append(client)
    client.start()

s.close()

