from threading import Thread
from flask import Flask, render_template, redirect, url_for, make_response, request
import time
import AlphaBot
import sqlite3
import random
import hashlib

# creo il robot
gino = AlphaBot.AlphaBot()

# creo l'app
app = Flask(__name__)

dict_commands = {"f":gino.forward,"b":gino.backward,"l":gino.left,"r":gino.right, "s":gino.stop } 
com = None
comando = None
distanza = None
comandoricevuto = False
nome_database = "AB01.db"
cursor = None
con = None


# hasha le poassword prima di inserirle nel database
def hash_string(input_string):
    hash_object = hashlib.sha256()
    hash_object.update(input_string.encode('utf-8'))
    hashed_string = hash_object.hexdigest()
    return hashed_string

# Controlla il login dell'utente
def validate(username, password):
    completion = False
    con = sqlite3.connect(f'./{nome_database}')
    cur = con.cursor()
    cur.execute("SELECT Utente, Password FROM users_logins")
    rows = cur.fetchall()
    for row in rows:
        dbUser = row[0]
        dbPass = row[1]
        if dbUser==username:
            completion=check_password(dbPass, hash_string(password))
    con.close()
    return completion

# Controllo per la registrazione utente
def registra(username, password, confirm, admin):
    con = sqlite3.connect(f'./{nome_database}')
    cur = con.cursor()
    cur.execute("SELECT Utente FROM users_logins")
    rows = cur.fetchall()

    for row in rows:
        if row[0] == username:
            con.close()
            return 1
        
    psw = hash_string(password) 
    conf = hash_string(confirm) 

    if not check_password(psw, conf):
        con.close()
        return 3

    if admin == 'on':
        admin = True
    else: admin = False

    cur.execute(f'INSERT INTO users_logins VALUES("{username}","{psw}", {admin});')
    con.commit()
    con.close()
    return 0

def check_password(hashed_password, user_password):
    return hashed_password == user_password

def stringa_casuale():
    stringa = ""
    for _ in range(40):
        stringa += str(random.randint(0,1000))
    return stringa

# Esegue i comandi basici
def comandiNormali(text):

    splitStringa(text)

    controlloStringa()

    # controllo se il comando è nel dizionario
    if comando in dict_commands:
        eseguiComando()
    else:
        dict_commands["s"]()

# legge i comandi del database e li esegue
def comandiDatabase():
        res = cursor.execute(f"SELECT seq_mov FROM tab_mov WHERE tab_mov.Shortcut = '{comando}'")
        l_complessa = res.fetchall()

        if len(l_complessa) < 1:
            l_comandi = ["s;0"]
        else:
            l_comandi = str(l_complessa[0][0]).split(",")

        for a in l_comandi:
            splitStringa(a)
            controlloStringa()
            if comando in dict_commands:
                eseguiComando()
            else:
                dict_commands["s"]()
    
# splitta la stringa e controlla se è nel formato fiusto
def splitStringa(text):
    global com
    # controllo stringa
    if text[1] != ";" or len(text) <= 3 :
        text = "s;0"

    # salvo il comando ricevuto    
    com = text.split(";")

# controlla se la stringa data in input è consentita
def controlloStringa():
    global comando, distanza
    try:
        comando = com[0]
        distanza = float(com[1])/1000
    except:
        comando = "s"
        distanza = 0.0

    if distanza < 0.15:
        distanza = 0.0
    elif distanza > 5:
        distanza = 5.0

# esegue il comando dato
def eseguiComando():
    dict_commands["s"]()
    dict_commands[comando]()
    time.sleep(distanza)
    dict_commands["s"]()

# Apre il database
def iniDatabase():
    global con, cursor, comandoricevuto
    if comandoricevuto == False:
        con = sqlite3.connect(f"./{nome_database}")
        cursor = con.cursor()
        comandoricevuto = True


@app.route('/', methods=['GET', 'POST'])
def registration():
    error = None
    ConfirmError = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['passwordConfirm']
        admin = request.form.get('checkbox')
        esiste = registra(username, password, confirm, admin)
        if esiste == 0:
            return redirect(url_for("index"))
        elif esiste == 1: 
            error = 'This Username already exist.'
        else: 
            ConfirmError = 'The passwords are different.'
    return render_template('registration.html', error=error, ConfirmError=ConfirmError)


@app.route(f'/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        completion = validate(username, password)
        if completion == False:
            error = 'Incorrect Username or Password.'
        else:
            username_cookie = request.cookies.get('username')
            if username_cookie=="Danielozen" or username == "Danielozen":
                resp = make_response(redirect(url_for("index")))
                resp.set_cookie('username', 'Danielozen')
                return resp
            else:
                #settare il cookie
                resp = make_response(redirect(url_for("login")))
                resp.set_cookie('username', 'utentegenerico')
            return resp # restituisce l'url del nome scritto dentro
    return render_template('login.html', error=error)


# Pagina Comandi
@app.route(f"/{stringa_casuale()}", methods=['GET', 'POST'])
def index():
    global comando, comandoricevuto, con, cursor
    text_rec = "s;0"
    if request.method == 'POST':
        if request.form.get('avanti') == 'avanti':
            print("avanti")
            text_rec = "f;1000"
        elif request.form.get('indietro') == 'indietro':
            print("indietro")
            text_rec = "b;1000"
        elif request.form.get('destra') == 'destra':
            print("destra")
            text_rec = "r;600"
        elif request.form.get('sinistra') == 'sinistra':
            print("sinistra")
            text_rec = "l;600"
        elif request.form.get('esegui') == 'esegui':
            text_rec = request.form['stringaSpeciale']
            print(text_rec)
        else:
            print("Unknown")

        if len(text_rec) == 1:
            comando = text_rec
            iniDatabase()
            comandiDatabase()
            con.close()
            comandoricevuto = False
        else:
            comandiNormali(text_rec)          

    elif request.method == 'GET':
        return render_template('index.html')
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True, host='192.168.1.5', port= 6969)