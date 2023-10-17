import socket
from threading import Thread
import AlphaBot
import time
import sqlite3
"""
Authors:
- Di Mantua Daniele
- Becchio Alexander
"""
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
        self.comando = None
        self.distanza = None
        self.com = None        
        self.dict_commands = {"f":gino.forward,"b":gino.backward,"l":gino.left,"r":gino.right, "s":gino.stop } # creo un dizionatio con i comandi    
        self.nome_database = "AB01.db"
        self.cursor = None
        self.con = None
        self.comandoricevuto = False
        self.inizializzaSensori = False

    def run(self):
        #LOOP
        while self.isRunning:
            
            # ricevo il messaggio dal client
            text_recived = self.conn.recv(buffer_size).decode()
            
            # stampo quello che riceve il robot
            print(f"Comando ricevuto: {text_recived} ---> Indirizzo: {self.add}")

            self.iniClasseEDatabase()

            if len(text_recived) == 1:
                self.comandiDatabase()
            else:
                self.comandiNormali(text_recived)

            self.con.close()
            self.comandoricevuto = False

    def iniClasseEDatabase(self):
            
            if self.inizializzaSensori == False:
                self.tempo.start()
                self.inizializzaSensori = True

            if self.comandoricevuto == False:
                self.con = sqlite3.connect(f"./{self.nome_database}")
                self.cursor = self.con.cursor()
                self.comandoricevuto = True

    def comandiDatabase(self):

        try:
            res = self.cursor.execute(f"SELECT seq_mov FROM tab_mov WHERE tab_mov.Shortcut = {self.comando}")
            strignaComplessa = res.fetchall()
            l_comandi = strignaComplessa.split(",")

            for a in l_comandi:
                self.splitStringa(a)
                self.controlloStringa()
                if self.comando in self.dict_commands:
                    self.eseguiComando()
                else:
                    self.dict_commands["s"]()
        except:
            self.dict_commands["s"]()

    def comandiNormali(self, text):

        self.splitStringa(text)

        self.controlloStringa()

        # controllo se il comando è nel dizionario
        if self.comando in self.dict_commands:
            self.eseguiComando()
        else:
            self.dict_commands["s"]()
    
    def splitStringa(self, text):
        # controllo stringa
        if text[1] != ";" or len(text) <= 3 :
            text = "s;0"

        # salvo il comando ricevuto    
        self.com = text.split(";")

    def controlloStringa(self):
            try:
                self.comando = self.com[0]
                self.distanza = float(self.com[1])/1000
            except:
                self.comando = "s"
                self.distanza = 0.0

            if self.distanza < 0.15:
                self.distanza = 0.0
            elif self.distanza > 5:
                self.distanza = 5.0

    def eseguiComando(self):
            self.dict_commands["s"]()
            self.dict_commands[self.comando]()
            time.sleep(self.distanza)
            self.dict_commands["s"]()


while True:
# accept e carica il client nel thread
    conn, add = s.accept()
    client = ClientThread(conn, add)
    client_list.append(client)
    client.start()

s.close()
