import os, re
import html
from flask import Flask,render_template,url_for,request,redirect,session,flash


from werkzeug.security import generate_password_hash,check_password_hash

import mysql.connector
import mariadb

from flask_security import login_required

from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user



import ast


app=Flask(__name__)
app.secret_key="tajni_kljuc_aplikacije"
login_manager = LoginManager()
login_manager.init_app(app)

konekcija=mysql.connector.connect(
    passwd="",
    user="root",
    database="bookstore",
    port=3306,
    auth_plugin='mysql_native_password'
)
kursor = konekcija.cursor(dictionary=True)

def vrati_korisnika(email):
	upit = "SELECT * FROM korisnik WHERE Email = %s"
	vrednosti = (email,)
	kursor.execute(upit, vrednosti)
	user = kursor.fetchone()
	return user


def ulogovan():
    if "ulogovani_korisnik" in session:
        return True
    else:
        return False

def rola():
    if ulogovan():
        return ast.literal_eval(session["ulogovani_korisnik"]).pop("Rola")
    
class User(UserMixin):
    def __init__(self, user_id, role):
        self.id = user_id
        self.role = role

@login_manager.user_loader
def load_user(user_id):
	upit = "SELECT KorisnikID, Rola FROM korisnik WHERE KorisnikID = %s"
	vrednosti = (user_id,)
	kursor.execute(upit, vrednosti)
	user = kursor.fetchone()
	if user:
		return User(user["KorisnikID"], user["Rola"])
	return None
    
@app.route('/')
def index():
	return redirect(url_for("render_login"))


@app.route('/login' ,methods=['GET','POST'])
def render_login() :
    if request.method=='GET':
        return render_template('start.html')
    elif request.method=='POST':
        forma=request.form
        user=vrati_korisnika(forma["email"])
        if user:
            print(check_password_hash(user["Lozinka"], forma["lozinka"]))
            if check_password_hash(user["Lozinka"], forma["lozinka"]):
                  user_obj=User(user["KorisnikID"],user["Rola"])
                  login_user(user_obj)
                  flash("Ulogovani ste!", 'success')
                  if current_user.is_authenticated and current_user.role=="administrator":
                       return redirect(url_for('render_korisnici'))
                  else:
                       return redirect(url_for("render_knjige"))
            else:
                flash("pogresna lozinka!", 'danger')
                return redirect(url_for("render_login"))
        else:
            flash("Ne postoji korisnik s ovim nalogom", 'danger')
            return redirect(url_for("render_login"))



@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("render_login"))


@app.route('/knjige', methods=['GET', 'POST'])
def render_knjige():
    args = request.args.to_dict()
    strana = request.args.get("page", "1")
    offset = int(strana) * 10 - 10
    prethodna_strana=""
    sledeca_strana="/korisnici?page=2"
    if "=" in request.full_path:
        split_path = request.full_path.split("=")
        del split_path[-1]
        sledeca_strana = "=".join(split_path) + "=" + str(int(strana) + 1)
        prethodna_strana = "=".join(split_path) + "=" + str(int(strana) - 1)
    order_by="KnjigaID"
    order_type="asc"
    if order_by in args:
         order_by=args["order_by"].lower()
         if("prethodni_order_by" in args and args["prethodni_order_by"] == args["order_by"]):
              if args["order_type"] == "asc":
                   order_type="desc"
    upit="select * from knjiga order by %s%s limit 10 offset %s"
    vrednost=(order_by,order_type,offset,)
    kursor.execute(upit,vrednost)
    knjiga=kursor.fetchall()
    return render_template('knjige.html',
    knjiga=knjiga,
    args=args,
    strana=strana,
    sledeca_strana=sledeca_strana,
    prethodna_strana=prethodna_strana,
    order_type=order_type
    )
   

@app.route("/knjiga_nova", methods=[ 'GET','POST'])
@login_required
def knjiga_nova():
    if current_user.is_authenticated and current_user.role=="administrator":
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
        flash("nije vam omogucen pristup", 'danger')
        return redirect(url_for('render_login'))
       


@app.route('/registracija', methods=['GET', 'POST'])
def registracija():
    if request.method=='GET':
        return render_template('registracija.html')
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
        return redirect(url_for('render_login'))
    

@app.route('/knjiga_izmena/<id>', methods=['GET', 'POST'])
@login_required
def knjiga_izmena(id):
    if current_user.is_authenticated and current_user.role=="administrator":
        if request.method == 'GET':
            upit = "SELECT * FROM knjiga WHERE KnjigaID=%s"
            vrednost = (id, )
            kursor.execute(upit, vrednost)
            knjiga=kursor.fetchone()

            return render_template('knjiga_izmena.html', knjiga=knjiga)
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
         flash("nije vam omogucen pristup", 'danger')
         return redirect(url_for("render_login"))
        

    
@app.route('/knjiga_brisanje/<id>', methods=['POST'])
@login_required
def knjiga_brisanje(id):
    if current_user.is_authenticated and current_user.role == 'administrator':

        upit=""" 
                delete from knjiga where KnjigaID=%s
        """
        vrednost=(id,)
        kursor.execute(upit,vrednost)
        konekcija.commit()
        return redirect(url_for('render_knjige'))
    else:
        flash("nije vam omogucen pristup", 'danger')
        return redirect(url_for("render_login"))
    
@app.route("/knjiga/<id>",methods=['GET', 'POST'] )
@login_required
def knjiga(id):
     upit='select * from knjiga where KnjigaID=%s'
     vrednosti=(id, )
     kursor.execute(upit,vrednosti)
     knjiga=kursor.fetchone()
     return render_template("knjiga.html",knjiga=knjiga)


@app.route('/korisnici', methods= ['GET'])
@login_required
def render_korisnici() :
    if current_user.is_authenticated and current_user.role == 'administrator':
        args = request.args.to_dict()
        strana = request.args.get("page", "1")
        offset = int(strana) * 10 - 10
        prethodna_strana=""
        sledeca_strana="/korisnici?page=2"
        if "=" in request.full_path:
            split_path = request.full_path.split("=")
            del split_path[-1]
            sledeca_strana = "=".join(split_path) + "=" + str(int(strana) + 1)
            prethodna_strana = "=".join(split_path) + "=" + str(int(strana) - 1)

        upit="""
                SELECT * FROM korisnik
                LIMIT 10 OFFSET %s
"""
        vrednost=(offset,)
        kursor.execute(upit,vrednost)
        korisnik=kursor.fetchall()

        return render_template('korisnici.html',
        korisnik = korisnik,
        strana=strana,
        sledeca_strana=sledeca_strana,
        prethodna_strana=prethodna_strana,
        args=args
        )
       
    else:
         flash("nije vam omogucen pristup", 'danger')
         return redirect(url_for("render_login"))



@app.route('/korisnici_novi', methods=['GET', 'POST'])
@login_required
def korisnik_novi():
    if current_user.is_authenticated and current_user.role == 'administrator':
         
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
            flash("nije vam omogucen pristup", 'danger')
            return redirect(url_for("render_login"))

    
@app.route('/korisnik_izmena<id>', methods=['POST','GET'])
@login_required
def korisnik_izmena(id):
    if current_user.is_authenticated and current_user.role == 'administrator':
        if request.method == "GET":
            upit = "SELECT * FROM korisnik WHERE KorisnikID=%s"
            vrednost = (id,)
            kursor.execute(upit, vrednost)
            korisnik = kursor.fetchone()
                        
            return render_template("korisnik_izmena.html", korisnik=korisnik)
            
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
         flash("nije vam omogucen pristup", 'danger')
         return redirect(url_for("render_login"))

@app.route("/korisnik_brisanje/<id>", methods=["POST"])
@login_required
def korisnik_brisanje(id):
    if current_user.is_authenticated and current_user.role == 'administrator':
        upit = """
                    DELETE FROM korisnik WHERE KorisnikID=%s
                    """
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()
        return redirect(url_for("render_korisnici"))
    else:
         flash("nije vam omogucen pristup", 'danger')
         return redirect(url_for("render_login"))



app.run(debug=True)