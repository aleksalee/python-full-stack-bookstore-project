import html
from flask import Flask,render_template,url_for,request,redirect,session

from werkzeug.security import generate_password_hash,check_password_hash

import mysql.connector
import mariadb

import ast


app=Flask(__name__)
app.secret_key="tajnki_kljuc_aplikacije"

konekcija=mysql.connector.connect(
    passwd="",
    user="root",
    database="bookstore",
    port=3306,
    auth_plugin='mysql_native_password'
)
kursor = konekcija.cursor(dictionary=True)

def ulogovan():
    if "ulogovani_korisnik" in session:
        return True
    else:
        return False

def rola():
    if ulogovan():
        return ast.literal_eval(session["ulogovani_korisnik"]).pop("Rola")

@app.route('/' ,methods=['GET','POST'])
def render_login() :
    if request.method=='GET':
        return render_template('start.html')
    if request.method=='POST':
        forma=request.form
        upit="""
            select * from korisnik
            where Email=%s
"""
        vrednost=(forma['email'],)
        kursor.execute(upit,vrednost)
        korisnik=kursor.fetchone()
        if korisnik != None:
            if check_password_hash(korisnik['Lozinka'], forma['lozinka']):
                if korisnik['lozinka']==forma['lozinka']:
                    session["ulogovani_korisnik"]=str(korisnik)
                    rola=rola()
                    return redirect(url_for('render_korisnici'))
            else:
                return render_template('start.html')
        else:
            return render_template('start.html')

@app.route("/logout")
def logout():
    session.pop("ulogovani_korisnik", None)
    return redirect(url_for("render_login"))


@app.route('/knjige', methods=['GET', 'POST'])
def render_knjige():
    upit="select * from knjiga"
    kursor.execute(upit)
    knjiga=kursor.fetchall()
    return render_template('knjige.html', knjiga=knjiga, rola=rola())
   

@app.route("/knjiga_nova", methods=[ 'GET','POST'])
def knjiga_nova():
    if rola()=='korisnik':
        return redirect(url_for('render_login'))
    if ulogovan():
        if request.method == 'GET':
            return render_template('knjiga_nova.html')
        if request.method == 'POST':
            forma=request.form
            vrednosti = (
                        forma['naslov'],
                        forma['autor'],
                        forma['isbn'],
                        forma['zanr'],
                        forma['cena']
                        )
            upit= """
                            insert into knjiga(Naslov,Autor,ISBN,Zanr,Cena)
                            values(%s,%s,%s,%s,%s)
            """
            kursor.execute(upit,vrednosti)
            konekcija.commit()
            return redirect(url_for('render_knjige'))
       
    else:
        return redirect(url_for('render_login'))

@app.route('/registracija', methods=['GET', 'POST'])
def render_registracija():
    return render_template('registracija.html')

@app.route('/knjiga_izmena/<id>', methods=['GET', 'POST'])
def knjiga_izmena(id):
    if rola()=='korisnik':
        return redirect(url_for('render_knjige'))
    if ulogovan():
        if request.method == 'GET':
            upit = "SELECT * FROM knjiga WHERE KnjigaID=%s"
            vrednost = (id, )
            kursor.execute(upit, vrednost)
            knjiga=kursor.fetchone()

            return render_template('knjiga_izmena.html', knjiga=knjiga,rola=rola())
        if request.method=='POST':
            upit = """
                        update knjiga set
                        Naslov=%s,Autor=%s,ISBN=%s,Zanr=%s,Cena=%s
                        where KnjigaID=%s
                    """
            forma=request.form
            vrednosti=(
                        forma['naslov'],
                        forma['autor'],
                        forma['isbn'],
                        forma['zanr'],
                        forma['cena'],
                        id
                    )
            kursor.execute(upit,vrednosti)
            konekcija.commit()
            return redirect(url_for('render_knjige'))
        else:
            return redirect(url_for('render_knjige'))
    else:
        return redirect(url_for('render_login'))
    
@app.route('/knjiga_brisanje/<id>', methods=['POST'])
def knjiga_brisanje(id):
    if rola() == 'korisnik':
        return redirect(url_for('render_knjige'))
    if ulogovan():
        upit=""" 
            delete from knjiga where KnjigaID=%s
    """
        vrednost=(id,)
        kursor.execute(upit,vrednost)
        konekcija.commit()
        return redirect(url_for('render_knjige'))
    else:
        return redirect(url_for('render_knjige'))

@app.route('/korisnici', methods= ['GET'])
def render_korisnici() :
    if rola()=='korisnik':
        return redirect(url_for('render_knjige'))
    if ulogovan():
        upit="select * from korisnik"
        kursor.execute(upit)
        korisnik=kursor.fetchall()
        return render_template('korisnici.html', korisnik = korisnik,rola=rola())

@app.route('/korisnici_novi', methods=['GET', 'POST'])
def korisnik_novi():
    if rola()=='korisnik':
        return redirect(url_for('render_knjige'))
    if ulogovan():
        if request.method=='GET':
            return render_template("korisnik_novi.html")
        if request.method=='POST':
            forma=request.form
            hesovana_lozinka=generate_password_hash(forma['lozinka'])
            vrednosti=(
                        forma['ime'],
                        forma['prezime'],
                        forma['email'],
                        forma['rola'],
                        hesovana_lozinka
                    )
            upit="""
                        insert into korisnik(Ime,Prezime,Email,Rola,Lozinka)
                            values(%s,%s,%s,%s,%s)
            """
            kursor.execute(upit,vrednosti)
            konekcija.commit()

            return redirect(url_for('render_korisnici'))
        else:
            return redirect(url_for('render_knjige'))
    else:
        return redirect(url_for('render_login'))
    
@app.route('/korisnik_izmena<id>', methods=['POST','GET'])
def korisnik_izmena(id):
    if rola()=='korisnik':
        return redirect(url_for('render_knjige'))
    if ulogovan():
        if request.method == "GET":
            upit = "SELECT * FROM korisnik WHERE KorisnikID=%s"
            vrednost = (id,)
            kursor.execute(upit, vrednost)
            korisnik = kursor.fetchone()
                    
            return render_template("korisnik_izmena.html", korisnik=korisnik,rola=rola())
        if request.method == "POST":
                upit = '''
                        update korisnik set
                        Ime=%s,Prezime=%s,Email=%s,Rola=%s,Lozinka=%s
                        where KorisnikID=%s
            '''
        forma=request.form
        vrednosti = (
                        forma['ime'],
                        forma['prezime'],
                        forma['email'],
                        forma['rola'],
                        forma['lozinka'],
                        id
                    )   
        kursor.execute(upit,vrednosti)
        konekcija.commit()
        return redirect(url_for('render_korisnici'))
    else:
        return redirect(url_for('render_login'))
    
@app.route("/korisnik_brisanje/<id>", methods=["POST"])
def korisnik_brisanje(id):
    if rola() == 'korisnik':
        return redirect(url_for('render_knjige'))
    if ulogovan():
        upit = """
                DELETE FROM korisnik WHERE KorisnikID=%s
                """
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()
        return redirect(url_for("render_korisnici"))


app.run(debug=True)