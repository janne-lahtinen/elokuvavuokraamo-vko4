#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, session, redirect, url_for, escape, request, Response, render_template
from functools import wraps
import hashlib
import sqlite3
import logging
import os
import sys
import datetime
import urllib
import cgi
import cgitb
cgitb.enable()

logging.basicConfig(filename=os.path.abspath('data/flask.log'),level=logging.DEBUG)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# Flask vaatii sessioiden käyttämiseen salaisen avaimen. Tätä ei pidä paljastaa muille:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

def auth(f):
	''' Tämä decorator hoitaa kirjautumisen tarkistamisen ja ohjaa tarvittaessa kirjautumissivulle
	'''
	@wraps(f)
	def decorated(*args, **kwargs):
	# tässä voisi olla monimutkaisempiakin tarkistuksia mutta yleensä tämä riittää
		if not 'kirjautunut' in session:
			return redirect(url_for('login'))
		return f(*args, **kwargs)
	return decorated

@app.route("/", methods=['POST','GET'])
@auth
def index():
	# os.path.abspath muuntaa suhteellisen polun absoluuttiseksi, joka taasen kelpaa sqlitelle
	con = sqlite3.connect(os.path.abspath('data/video'))

	# voidaan käsitellä palautettuja tietueita niiden kenttien nimillä
	con.row_factory = sqlite3.Row

	# Kysely etusivun listausta vartens
	sql = """
	SELECT J.Nimi, J.JasenID, E.Nimi, E.ElokuvaID, V.VuokrausPVM, V.PalautusPVM, V.Maksettu
	FROM Vuokraus AS V, Jasen AS J, Elokuva AS E
	WHERE V.JasenID = J.JasenID AND E.ElokuvaID = V.ElokuvaID
	ORDER BY J.Nimi, J.JasenID, V.VuokrausPVM DESC, V.PalautusPVM
	"""

	# Luo Cursor-objektin
	cur = con.cursor()

	# Ajetaan kysely
	try:
	   cur.execute(sql)
	except: 
	   # Virheilmoitus lokiin, jos kysely ei onnistu
	   logging.debug( sys.exc_info()[0] )
	   logging.debug( sys.exc_info()[1] )

	# Valmistellaan vuokrauslistaus templatea varten, apumuuttuja aloitukseen
	verrokki = -1

	# Muodostetaan vuokrauslista kyselystä saadulla datalla
	vuokraukset = []
	for row in cur.fetchall():
		if verrokki == -1:
			verrokki = row[0]
			vuokraukset.append( dict(jNimi=row[0], jasenID=row[1], eNimi=row[2], elokuvaID=row[3], vuokrausPVM=row[4], palautusPVM=row[5], maksettu=row[6]) )
		elif row[0] != verrokki:
			verrokki = row[0]
			vuokraukset.append( dict(loppu="2") )
			vuokraukset.append( dict(jNimi=row[0], jasenID=row[1], eNimi=row[2], elokuvaID=row[3], vuokrausPVM=row[4], palautusPVM=row[5], maksettu=row[6]) )
		else:
			vuokraukset.append( dict(taso= "2", jasenID=row[1], eNimi=row[2], elokuvaID=row[3], vuokrausPVM=row[4], palautusPVM=row[5], maksettu=row[6]) )
	vuokraukset.append( dict(loppu="2") )

	return render_template("index.html", vuokraukset=vuokraukset)

@app.route("/vuokraus", methods=['POST','GET'])
@auth
def vuokraus():
	# os.path.abspath muuntaa suhteellisen polun absoluuttiseksi, joka taasen kelpaa sqlitelle
	con = sqlite3.connect(os.path.abspath('data/video'))

	# voidaan käsitellä palautettuja tietueita niiden kenttien nimillä
	con.row_factory = sqlite3.Row

	cur = con.cursor()

	# Kysely vuokraajista tietokannassa
	try:
		cur.execute("""
		SELECT Nimi, JasenID
		FROM Jasen
		""")
	except: 
	   # Virheilmoitus lokiin, jos kysely ei onnistu
	   logging.debug( sys.exc_info()[0] )
	   logging.debug( sys.exc_info()[1] )

	# Muodostetaan lista kyselystä saadulla datalla
	vuokraajat = []
	for row in cur.fetchall():
		vuokraajat.append( dict(nimi=row[0], jasenID=row[1]) )

	# Kysely elokuvista tietokannassa
	try:
		cur.execute("""
		SELECT Nimi, ElokuvaID
		FROM Elokuva
		""")
	except: 
	   # Virheilmoitus lokiin, jos kysely ei onnistu
	   logging.debug( sys.exc_info()[0] )
	   logging.debug( sys.exc_info()[1] )

	# Muodostetaan lista kyselystä saadulla datalla
	elokuvat = []
	for row in cur.fetchall():
		elokuvat.append( dict(nimi=row[0], elokuvaID=row[1]) )

	# Virheilmoitusten alustaminen
	herja = ""
	herja2 = ""
	herja3 = ""
	herja4 = ""

	# Lomakkeen käsittely, jos on valittu vuokraa-painike -----------------------------------------------
	if request.form.get("vuokraa", None):
		insert_sql = """
			INSERT INTO Vuokraus (JasenID, ElokuvaID, VuokrausPVM, PalautusPVM, Maksettu)
			VALUES (:jasenid, :elokuvaid, :vuokrauspvm, :palautuspvm, :maksettu )
			"""
		# Haetaan annetut arvot lomakkeelta
		elokuva = request.form.get("eNimi")
		jasen = request.form.get("vNimi", -1) # Jos jasenta ei ole annettu käytetään -1, joka kaataa executen
		vuokraus = request.form.get("vuokrausPVM")
		palautus = request.form.get("palautusPVM")
		maksettu = request.form.get("maksettu")

		# Syötettyjen päivämäärien muodon tarkistus
		try:
			 datetime.datetime.strptime(vuokraus, '%Y-%m-%d')
		except ValueError:
			herja = u"Vuokrauspäivä syötetty väärässä muodossa"
			return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4)
		try:
			 datetime.datetime.strptime(palautus, '%Y-%m-%d')
		except ValueError:
			herja2 = u"Palautuspäivä syötetty väärässä muodossa"
			return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4)

		# Syötettyjen päivämäärien tarkistus, palautus pitää olla suurempi
		try:
			if palautus <= vuokraus:
				herja2 = u"Palautuspäivämäärän pitää olla vuokrauspäivää myöhemmin!"
				return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4)
		except:
			logging.debug( "Palautuspäivän tarkistus ei onnistunut!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )

		# Syötetyn maksun tarkistukset, jos nolla tai vähemmän --> try, jos ei INT, except
		try:
			maksettuINT = int(maksettu)
			if maksettuINT <= 0:
				herja3 = u"Syötit liian pieniä arvoja, yritä uudestaan."
		except:
			herja3 = u"Syötit vääriä arvoja, yritä uudestaan."
			logging.debug( "Maksetun summan tarkistus ei onnistu!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )

		# Lisäys kaatuu jos yritetään vuokrata sama elokuva samalle henkilölle useammin kuin kerran		
		try:
			cur.execute(insert_sql, {"jasenid":jasen, "elokuvaid":elokuva, "vuokrauspvm":vuokraus, "palautuspvm":palautus, "maksettu":maksettu})
			con.commit() # tehdään commit vaikka osa lisäyksistä epäonnistuisikin
			return redirect(url_for('index'))
		except:
			con.rollback()
			herja4 = "Elokuva on jo henkilöllä vuokrattuna!"
			logging.debug( "Vuokraus ei onnistu!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )

		return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4)
			
	return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4)

@app.route("/muokkaa", methods=['POST','GET'])
@auth
def muokkaa():
	# os.path.abspath muuntaa suhteellisen polun absoluuttiseksi, joka taasen kelpaa sqlitelle
	con = sqlite3.connect(os.path.abspath('data/video'))

	# voidaan käsitellä palautettuja tietueita niiden kenttien nimillä
	con.row_factory = sqlite3.Row

	cur = con.cursor()

	# Kysely vuokraajista tietokannassa
	try:
		cur.execute("""
		SELECT Nimi, JasenID
		FROM Jasen
		""")
	except: 
	   # Virheilmoitus lokiin, jos kysely ei onnistu
	   logging.debug( sys.exc_info()[0] )
	   logging.debug( sys.exc_info()[1] )

	# Muodostetaan lista kyselystä saadulla datalla
	vuokraajat = []
	for row in cur.fetchall():
		vuokraajat.append( dict(nimi=row[0], jasenID=row[1]) )

	# Kysely elokuvista tietokannassa
	try:
		cur.execute("""
		SELECT Nimi, ElokuvaID
		FROM Elokuva
		""")
	except: 
	   # Virheilmoitus lokiin, jos kysely ei onnistu
	   logging.debug( sys.exc_info()[0] )
	   logging.debug( sys.exc_info()[1] )

	# Muodostetaan lista kyselystä saadulla datalla
	elokuvat = []
	for row in cur.fetchall():
		elokuvat.append( dict(nimi=row[0], elokuvaID=row[1]) )

	# Virheilmoituksen alustaminen
	herja = ""
	herja2 = ""
	herja3 = ""
	herja4 = ""

	# Linkin mukana tuotu muuttuja, oletusarvo tyhjä string
	INjasenID = int(request.values.get('jasenID', ''))

	# Linkin mukana tuotu muuttuja, oletusarvo tyhjä string
	INelokuvaID = int(request.values.get('elokuvaID', ''))

	# Linkin mukana tuotu muuttuja, oletusarvo tyhjä string
	INvuokrausPVM = request.values.get('vuokrausPVM', '')

	# Linkin mukana tuotu muuttuja, oletusarvo tyhjä string
	INpalautusPVM = request.values.get('palautusPVM', '')  

	# Linkin mukana tuotu muuttuja, oletusarvo tyhjä string
	INmaksettu = request.values.get('maksettu', '')

	# Lomakkeen käsittely, jos on valittu muokkaa-painike -----------------------------------------------
	if request.form.get("muokkaa", None):
		update_sql = """
			UPDATE Vuokraus SET JasenID = :jasenid, ElokuvaID = :elokuvaid, VuokrausPVM = :vuokrauspvm, PalautusPVM = :palautuspvm, Maksettu = :maksettu
			WHERE Vuokraus.JasenID = :INjasen 
				AND Vuokraus.ElokuvaID = :INelokuva 
				AND Vuokraus.VuokrausPVM = :INvuokraus
			"""
		# Haetaan annetut arvot lomakkeelta
		elokuva = request.form.get("eNimi")
		jasen = request.form.get("vNimi", -1) # Jos jasenta ei ole annettu käytetään -1, joka kaataa executen
		vuokraus = request.form.get("vuokrausPVM")
		palautus = request.form.get("palautusPVM")
		maksettu = request.form.get("maksettu")

		# Syötettyjen päivämäärien muodon tarkistus
		try:
			 datetime.datetime.strptime(vuokraus, '%Y-%m-%d')
		except ValueError:
			herja = u"Vuokrauspäivä syötetty väärässä muodossa!"
			return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)
		try:
			 datetime.datetime.strptime(palautus, '%Y-%m-%d')
		except ValueError:
			herja2 = u"Palautuspäivä syötetty väärässä muodossa!"
			return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)

		# Syötettyjen päivämäärien tarkistus, palautus pitää olla suurempi
		try:
			if palautus <= vuokraus:
				herja = u"Palautuspäivämäärän pitää olla vuokrauspäivää myöhemmin!"
				return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)
		except:
			logging.debug( "Palautuspäivän tarkistus ei onnistunut!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )

		# Syötetyn maksun tarkistukset, jos nolla tai vähemmän --> try, jos ei INT, except
		try:
			maksettuINT = int(maksettu)
			if maksettuINT <= 0:
				herja3 = u"Syötit liian pieniä arvoja, yritä uudestaan."
				return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)
		except:
			herja3 = u"Syötit vääriä arvoja, yritä uudestaan."
			logging.debug( "Maksetun summan tarkistus ei onnistu!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )
			return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)

		# Yritetään päivittää kenttien tietoja		
		try:
			cur.execute(update_sql, {"jasenid":jasen, "elokuvaid":elokuva, "vuokrauspvm":vuokraus, "palautuspvm":palautus, "maksettu":maksettu, "INjasen":INjasenID, "INelokuva":INelokuvaID, "INvuokraus":INvuokrausPVM})
			con.commit() # tehdään commit vaikka osa lisäyksistä epäonnistuisikin
			return redirect(url_for('index'))
		except:
			con.rollback()
			herja4 = "Muokkaus ei onnistu!"
			logging.debug( "Muokkaus ei onnistu!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )

		return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)

	# Lomakkeen käsittely, jos on valittu poista-painike -----------------------------------------------
	if request.form.get("poista", None):
		delete_sql = """
			DELETE FROM Vuokraus
			WHERE Vuokraus.JasenID = :INjasen 
				AND Vuokraus.ElokuvaID = :INelokuva 
				AND Vuokraus.VuokrausPVM = :INvuokraus
			"""
		# Linkin mukana tuotu muuttuja, oletusarvo tyhjä string
		INjasenID = int(request.values.get('jasenID', ''))

		# Linkin mukana tuotu muuttuja, oletusarvo tyhjä string
		INelokuvaID = int(request.values.get('elokuvaID', ''))

		# Linkin mukana tuotu muuttuja, oletusarvo tyhjä string
		INvuokrausPVM = request.values.get('vuokrausPVM', '')

		# Linkin mukana tuotu muuttuja, oletusarvo tyhjä string
		INpalautusPVM = request.values.get('palautusPVM', '')  

		# Linkin mukana tuotu muuttuja, oletusarvo tyhjä string
		INmaksettu = request.values.get('maksettu', '')

		# Yritetään poistaa tietue		
		try:
			cur.execute(delete_sql, {"INjasen":INjasenID, "INelokuva":INelokuvaID, "INvuokraus":INvuokrausPVM})
			con.commit() # tehdään commit vaikka osa lisäyksistä epäonnistuisikin
			return redirect(url_for('index'))
		except:
			con.rollback()
			herja = "Poistaminen ei onnistu!"
			logging.debug( "Poistaminen ei onnistu!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )

	return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)

@app.route("/elokuvat", methods=['POST','GET'])
@auth
def elokuvat():	
	# os.path.abspath muuntaa suhteellisen polun absoluuttiseksi, joka taasen kelpaa sqlitelle
	con = sqlite3.connect(os.path.abspath('data/video'))

	# voidaan käsitellä palautettuja tietueita niiden kenttien nimillä
	con.row_factory = sqlite3.Row

	cur = con.cursor()

	# Sarake järjestystä varten taulukolle, jos tullaan uudestaan sivulle session aikana,
	# järjestysvalinta pysyy tallessa
	order = request.values.get('order', '')
	# Tämä sessiomuuttuja toimi kehitysympäristössä, mutta kaatoi
	# sovelluksen yliopiston serverillä
	# ---------------------------------
	# if len(order) > 0:
	# 	session['jarj'] = order
	# if len(order) == 0 and len(session['jarj']) > 0:
	# 	order = session['jarj']

	# Järjestäminen vuoden mukaan
	if order == 'vuosi':
		update_sql = """
		SELECT E.Nimi, E.Julkaisuvuosi, E.Vuokrahinta, E.Arvio, L.Tyypinnimi
		FROM Elokuva AS E, Lajityyppi AS L
		WHERE E.LajityyppiID = L.LajityyppiID
		ORDER BY E.Julkaisuvuosi
		"""

		try:
			cur.execute(update_sql)
			#con.commit() # tehdään commit vaikka osa lisäyksistä epäonnistuisikin
		except:
			logging.debug( "Järjestäminen ei onnistu!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )

	# Järjestäminen hinnan mukaan
	elif order == 'hinta':
		update_sql = """
		SELECT E.Nimi, E.Julkaisuvuosi, E.Vuokrahinta, E.Arvio, L.Tyypinnimi
		FROM Elokuva AS E, Lajityyppi AS L
		WHERE E.LajityyppiID = L.LajityyppiID
		ORDER BY E.Vuokrahinta
		"""

		try:
			cur.execute(update_sql)
			#con.commit() # tehdään commit vaikka osa lisäyksistä epäonnistuisikin
		except:
			logging.debug( "Järjestäminen ei onnistu!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )

	# Järjestäminen arvion mukaan
	elif order == 'arvio':
		update_sql = """
		SELECT E.Nimi, E.Julkaisuvuosi, E.Vuokrahinta, E.Arvio, L.Tyypinnimi
		FROM Elokuva AS E, Lajityyppi AS L
		WHERE E.LajityyppiID = L.LajityyppiID
		ORDER BY E.Arvio
		"""

		try:
			cur.execute(update_sql)
			#con.commit() # tehdään commit vaikka osa lisäyksistä epäonnistuisikin
		except:
			logging.debug( "Järjestäminen ei onnistu!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )

	# Järjestäminen lajityypin mukaan
	elif order == 'genre':
		update_sql = """
		SELECT E.Nimi, E.Julkaisuvuosi, E.Vuokrahinta, E.Arvio, L.Tyypinnimi
		FROM Elokuva AS E, Lajityyppi AS L
		WHERE E.LajityyppiID = L.LajityyppiID
		ORDER BY L.Tyypinnimi
		"""

		try:
			cur.execute(update_sql)
			#con.commit() # tehdään commit vaikka osa lisäyksistä epäonnistuisikin
		except:
			logging.debug( "Järjestäminen ei onnistu!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )

	# Järjestäminen nimen mukaan
	else:
		update_sql = """
		SELECT E.Nimi, E.Julkaisuvuosi, E.Vuokrahinta, E.Arvio, L.Tyypinnimi
		FROM Elokuva AS E, Lajityyppi AS L
		WHERE E.LajityyppiID = L.LajityyppiID
		ORDER BY E.Nimi
		"""

		try:
			cur.execute(update_sql)
			#con.commit() # tehdään commit vaikka osa lisäyksistä epäonnistuisikin
		except:
			logging.debug( "Järjestäminen ei onnistu!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )

	# Muodostetaan lista kyselystä saadulla datalla
	elokuvat = []
	for row in cur.fetchall():
		elokuvat.append( dict(nimi=row[0], vuosi=row[1], hinta=row[2], arvio=row[3], genre=row[4]) )

	return render_template("elokuvat.html", elokuvat=elokuvat, order=order)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# Testataan käyttäjätunnus, pitää olla tiea218@foobar.example
		# Käyttäjätunnuksen virheilmoitus
		herja = ""
		tunnus = request.form['username']
		# tunnus = tunnus.decode('utf-8')
		# Salasanan virheilmoitus
		herja2 = ""
		salasana = request.form['password']

		# En saanut piilotettua salasanavertailua toimimaan --> "Unicode-objects must be encoded before hashing"
		# salasana = salasana.encode('utf-8')
		if tunnus == "tiea218@foobar.example" and salasana == "web-sovellukset":
			# jos kaikki ok niin asetetaan sessioon tieto kirjautumisesta ja ohjataan laskurisivulle
			session['kirjautunut'] = "ok"
			return redirect(url_for('index'))			
		elif tunnus != "tiea218@foobar.example" and salasana == "web-sovellukset":
			herja = u"Väärä käyttäjätunnus!"
			return render_template('login.html', herja=herja, herja2=herja2)
		elif tunnus == "tiea218@foobar.example" and salasana != "web-sovellukset":
			herja2 = u"Väärä salasana!"
			return render_template('login.html', herja=herja, herja2=herja2)
		else:
			herja = u"Väärä käyttäjätunnus!"
			herja2 = u"Väärä salasana!"
			return render_template('login.html', herja=herja, herja2=herja2)
		# ---------------------------------------
		# En saanut tätä toimimaan mitenkään, erroreita ei enää tullut, mutta salasana ei ollut
		# koskaan oikein sisään kirjautuessa
		# ---------------------------------------
		# username = request.form['username']
		# username = username.encode('utf-8') --> decode antaa herjan "AttributeError: 'str' object has no attribute 'decode'"
		# m = hashlib.sha512()
		# avain = "omasalainenavain"
		# avain = avain.encode('utf-8')
		# m.update(avain)
		# m.update(salasana)
		# tarkistussana = "b'I\xe7E`\xa3\xa4/\xfdebIu\xb3\x90a\xbb\x9d^\xdb\xb4\xf5\x01l\xcd\xaf\x1e\x80\xddJ\n0\x95\xb8\x8cR\xb9\x84]s\xe2\xc0\x10\x80v\xa5\xfd\xd8\xf1\x18\xff]\xd0z\xb9D\xec\xf11\xb8r\xce^z\xb8'"
		# tarkistussana = tarkistussana.encode('utf-8')
		# if m.digest() == tarkistussana:
		# 	# jos kaikki ok niin asetetaan sessioon tieto kirjautumisesta ja ohjataan laskurisivulle
		# 	session['kirjautunut'] = "ok"
		# 	return redirect(url_for('index'))
		# else:
		# 	herja2 = u"Väärä salasana!"
		return render_template('login.html', herja=herja)
	# jos ei ollut oikea salasana niin pysytään kirjautumissivulla.
	return render_template('login.html')

@app.route('/logout')
def logout():
	# Poistetaan tunnus sessiosta
	session.pop('kirjautunut', None)
	return redirect(url_for('index'))

if __name__ == "__main__":
	app.run(debug=True)