from flask import Flask, render_template, redirect, url_for, make_response, request
import time
import AlphaBot
import sqlite3
import random
import hashlib
import datetime
import pandas as pd

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

"""Inizio funzioni per controllo form e inserimento dati nel database"""
# return data e l'ora
def DataOra():
    data = str(datetime.datetime.now())[:10]
    ora = str(datetime.datetime.now())[11:-7]
    return f"{data} {ora}"

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

# Controlla che il codice admin sia corretto
def controllaAdmin(code):
    completion = False
    con = sqlite3.connect(f'./{nome_database}')
    cur = con.cursor()
    cur.execute("SELECT code FROM Admin")
    rows = cur.fetchall()
    for row in rows:
        completion=check_password(row[0], hash_string(code))
    con.close()
    return completion

# Controllo per la registrazione utente
def registra(username, password, confirm, admin):
    """
    OUTPUT:
    0 = tutto è andata a buon fine
    1 = lo username esiste
    2 = La password di verifica è diversa da quella inserita prima
    """
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
        return 2
    # controllo se i comandi degli utenti sono disattivati oppure attivati
    if admin == False:
        cur.execute("SELECT DISTINCT users_logins.attivo FROM users_logins WHERE users_logins.Tipo = false")
        rows = cur.fetchall()
        if len(rows) == False:
            row = True
        else: row = rows[0][0]
    cur.execute(f'INSERT INTO users_logins VALUES("{username}","{psw}", {admin}, {row});')
    con.commit()
    con.close()
    return 0

# crea nel database il log delle azioni degli utenti basandosi sui cookie
def cookieLog(name, string):
    con = sqlite3.connect(f'./{nome_database}')
    cur = con.cursor()
    cur.execute(f'INSERT INTO Cookie VALUES(NULL, "{name}", "{string}", "{DataOra()}");')
    con.commit()
    con.close()

# Controlla se la password che si trova nel database è uguale a quella inserita dall'utente
def check_password(hashed_password, user_password):
    return hashed_password == user_password

def ottieniRuolo():
    con = sqlite3.connect(f'./{nome_database}')
    cur = con.cursor()
    cur.execute(f'SELECT Tipo FROM users_logins WHERE Utente = "{request.cookies.get('username')}"')
    rows = cur.fetchall()
    con.close()
    return rows[0][0]

# disabilita i controlli degli utenti non admin
def disabilitaUtente():
    con = sqlite3.connect(f'./{nome_database}')
    cur = con.cursor()
    cur.execute("UPDATE users_logins SET Attivo = 0 WHERE users_logins.Tipo = 0")
    con.commit()
    con.close()

# abilita il controlli degli utenti non admin
def abilitaUtente():
    con = sqlite3.connect(f'./{nome_database}')
    cur = con.cursor()
    cur.execute("UPDATE users_logins SET Attivo = 1 WHERE users_logins.Tipo = 0")
    con.commit()
    con.close()

# controlla se i controlli per l'Alphabot sono attivi.
def comandiAttivi():
    con = sqlite3.connect(f'./{nome_database}')
    cur = con.cursor()
    cur.execute(f"SELECT users_logins.Attivo FROM users_logins WHERE users_logins.Utente='{request.cookies.get('username')}'")
    rows = cur.fetchall()
    con.close()
    return rows[0][0]

# Crea una stringa casuale per mascherare l'indirizzo della pagini index
def stringa_casuale():
    stringa = ""
    for _ in range(40):
        stringa += str(random.randint(0,1000))
    return stringa

"""Fine funzioni per controllo form e inserimento dati nel database"""

"""Inizio funzioni per controllo stringhe e movimento Alphabot"""
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

"""Fine funzioni per controllo stringhe e movimento Alphabot"""


"""Inizio funzioni per funzionamento delle pagine"""
# Menu iniziale
@app.route('/', methods=['POST', 'GET'])
def menu():
    return render_template('menu.html')

# Pagina di registazione per admin
@app.route('/adminReg', methods=['POST', 'GET'])
def adminReg():
    error = None
    ConfirmError = None
    adminError = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['passwordConfirm']
        admincode = request.form['adminCode']

        # Controlla se il codice admin è corretto
        if controllaAdmin(admincode):
            esiste = registra(username, password, confirm, admin = True)

            if esiste == 0:
                username_cookie = request.cookies.get('username')
                # se il cookie è diverso da nome utente lo cambia
                if username_cookie != username:
                    resp = make_response(redirect(url_for("index")))
                    resp.set_cookie('username', f'{username}')
                    cookieLog(username, "Un nuovo admin si è registrato.")
                else: 
                    resp = make_response(redirect(url_for("index")))
                return resp # restituisce l'url del nome scritto dentro  
            elif esiste == 1: 
                error = 'This Username already exist.'
            else: 
                ConfirmError = 'The passwords are different.'
        else: adminError = 'Incorrect Admin Code.'

    return render_template('adminReg.html', error=error, ConfirmError=ConfirmError, adminError=adminError)

# Pagina di registrazione per utenti
@app.route('/registration', methods=['POST', 'GET'])
def registration():
    error = None
    ConfirmError = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['passwordConfirm']
        esiste = registra(username, password, confirm, admin = False)

        if esiste == 0:
            username_cookie = request.cookies.get('username')
            # se il cookie è diverso da nome utente lo cambia
            if username_cookie != username:
                resp = make_response(redirect(url_for("index")))
                resp.set_cookie('username', f'{username}')
                cookieLog(username, "L'Utente si è registrato.")
            else: 
                resp = make_response(redirect(url_for("index")))
            return resp # restituisce l'url del nome scritto dentro
        elif esiste == 1: 
            error = 'This Username already exist.'
        else: 
            ConfirmError = 'The passwords are different.'

    return render_template('registration.html', error=error, ConfirmError=ConfirmError)

#Pagin di Login
@app.route(f'/login', methods=['POST', 'GET'])
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
            # se il cookie è diverso da nome utente lo cambia
            if username_cookie != username:
                resp = make_response(redirect(url_for("index")))
                resp.set_cookie('username', f'{username}')
            else: 
                resp = make_response(redirect(url_for("index")))
            cookieLog(username, "Ha fatto il Login")
            return resp # restituisce l'url del nome scritto dentro
        
    return render_template('login.html', error=error)

# Pagina dove viene mostrato il oge dell'utente
@app.route("/Log", methods=['POST', 'GET'])
def logPage():
    LogData = {"Data e ora": [], "Nome": [], "Azione": []} # inserisco i dati del database in un dizionario
    con = sqlite3.connect(f'./{nome_database}')
    cur = con.cursor()
    cur.execute(f"SELECT Tipo FROM users_logins WHERE Utente = '{request.cookies.get('username')}'")
    rows = cur.fetchall()
    # se l'utente è un admin vedrà la cronologia di tutti gli utenti
    if rows[0][0] == 1:
        cur.execute(f"SELECT data_e_ora, cookie_name, azione FROM Cookie ORDER BY n_log DESC")
    else:
        cur.execute(f"SELECT data_e_ora, cookie_name, azione FROM Cookie WHERE cookie_name = '{request.cookies.get('username')}' ORDER BY n_log DESC")
    rows = cur.fetchall()
    for row in rows:
        dataora = row[0]
        name = row[1]
        action = row[2]
        LogData["Data e ora"].append(dataora)
        LogData["Nome"].append(name)
        LogData["Azione"].append(action)

    # creo un dataframe con pandas per poi aggiungerlo come tabella in formato html
    data = pd.DataFrame(LogData)
    con.close()
    return render_template('logPage.html') + data.to_html(col_space=200, justify= "left", index = False, border = 0)

# Pagina Comandi
@app.route(f"/{stringa_casuale()}", methods=['POST', 'GET'])
def index():
    global comando, comandoricevuto, con, cursor
    text_rec = "s;0"
    mascheraComando = "Nessun comando selezionato"
    comandoAdmin = False

    if ottieniRuolo() == 1:
        comandoAdmin = True

    # Prende i valori che vengono premuti dall'utente e esegue l'azione
    if request.method == 'POST':

        if comandiAttivi() == 1:
            if request.form.get('button_pressed') == 'avanti':
                mascheraComando = "Avanti"
                text_rec = "f;1000"
            elif request.form.get('button_pressed') == 'indietro':
                mascheraComando = "Indietro"
                text_rec = "b;1000"
            elif request.form.get('button_pressed') == 'destra':
                mascheraComando = "Destra"
                text_rec = "r;400"
            elif request.form.get('button_pressed') == 'sinistra':
                mascheraComando = "Sinistra"
                text_rec = "l;400"
            elif request.form.get('esegui') == 'esegui':
                text_rec = request.form['stringaSpeciale']
                mascheraComando = text_rec.upper()

            # Gino va avanti all'infinito finché non viene selezionata un'altra azione
            elif request.form.get('start') == 'start':
                mascheraComando = "Continua Avanti"
                while True:
                    gino.forward()
                    return render_template("index.html", comando=mascheraComando, admin=comandoAdmin)
            elif request.form.get('stop') == 'stop':
                mascheraComando = "Fermo"
                gino.stop()
            else: 
                mascheraComando = "Comando non riconosciuto"
            
            cookieLog(request.cookies.get('username'), mascheraComando)
            
            # controlla il tipo di comando ricevuto
            if len(text_rec) == 1:
                comando = text_rec
                iniDatabase()
                comandiDatabase()
                con.close()
                comandoricevuto = False
            else:
                comandiNormali(text_rec)
            
        else: mascheraComando = "I comandi sono stati disabilitati da un Admin."

        # il log out setta il cookie ad 'UtenteGenerico' e riporta alla pagina home
        if request.form.get("LogOut") == 'esci': 
            mascheraComando = "L'utente è uscito."
            cookieLog(request.cookies.get('username'), mascheraComando)
            resp = make_response(redirect(url_for("menu")))
            resp.set_cookie('username', "UtenteGenerico")
            return resp
        
        # comandi visibili solo agli admin
        elif request.form.get("disable") == "disable":
            mascheraComando = "Comandi utenti disabilitati"
            cookieLog(request.cookies.get('username'), mascheraComando)
            disabilitaUtente()
        elif request.form.get("enable") == "enable":
            mascheraComando = "Comandi utenti abilitati"
            cookieLog(request.cookies.get('username'), mascheraComando)
            abilitaUtente()

    elif request.method == 'GET':
        return render_template('index.html', comando=mascheraComando, admin=comandoAdmin)
    return render_template("index.html", comando=mascheraComando, admin=comandoAdmin)

"""Fine funzioni per funzionamento delle pagine"""


if __name__ == '__main__':
    app.run(debug=True, host='192.168.43.84', port= 6969)