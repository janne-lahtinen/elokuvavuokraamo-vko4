#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, session, redirect, url_for, escape, request, Response, render_template
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

@app.route("/", methods=['POST','GET'])
def index():
	# Jos käyttäjätunnus löytyy sessiosta niin ollaan kirjautuneita
	if 'username' in session:
		# return 'Logged in as %s' % escape(session['username'])

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

	# Jos ei löydy niin ohjataan kirjautumissivulle
	return redirect(url_for('login'))


@app.route("/vuokraus", methods=['POST','GET'])
def vuokraus():
	# Jos käyttäjätunnus löytyy sessiosta niin ollaan kirjautuneita
	if 'username' in session:
		#return 'Logged in as %s' % escape(session['username'])
	
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
				herja4 = "Elokuva on jo henkilöllä vuokrattuna!"
				logging.debug( "Vuokraus ei onnistu!" )
				logging.debug( sys.exc_info()[0] )
				logging.debug( sys.exc_info()[1] )

			return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4)
				
		return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, herja2=herja2, herja3=herja3, herja4=herja4)

	# Jos ei löydy niin ohjataan kirjautumissivulle
	return redirect(url_for('login'))

@app.route("/muokkaa", methods=['POST','GET'])
def muokkaa():
	# Jos käyttäjätunnus löytyy sessiosta niin ollaan kirjautuneita
	if 'username' in session:
		# return 'Logged in as %s' % escape(session['username'])
	
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
				herja = u"Vuokrauspäivä syötetty väärässä muodossa, pitäisi olla, vuosi-kuukausi-päivä eli vvvv-kk-pp"
				return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)
			try:
				 datetime.datetime.strptime(palautus, '%Y-%m-%d')
			except ValueError:
				herja = u"Palautuspäivä syötetty väärässä muodossa, pitäisi olla, vuosi-kuukausi-päivä eli vvvv-kk-pp"
				return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)

			# Syötettyjen päivämäärien tarkistus, palautus pitää olla suurempi
			try:
				if palautus <= vuokraus:
					herja = u"Palautuspäivämäärän pitää olla vuokrauspäivää myöhemmin!"
					return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)
			except:
				logging.debug( "Palautuspäivän tarkistus ei onnistunut!" )
				logging.debug( sys.exc_info()[0] )
				logging.debug( sys.exc_info()[1] )

			# Syötetyn maksun tarkistukset, jos nolla tai vähemmän --> try, jos ei INT, except
			try:
				maksettuINT = int(maksettu)
				if maksettuINT <= 0:
					herja = u"Syötit liian pieniä arvoja, yritä uudestaan."
					return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)
			except:
				herja = u"Syötit vääriä arvoja, yritä uudestaan."
				logging.debug( "Maksetun summan tarkistus ei onnistu!" )
				logging.debug( sys.exc_info()[0] )
				logging.debug( sys.exc_info()[1] )
				return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)

			# Yritetään päivittää kenttien tietoja		
			try:
				cur.execute(update_sql, {"jasenid":jasen, "elokuvaid":elokuva, "vuokrauspvm":vuokraus, "palautuspvm":palautus, "maksettu":maksettu, "INjasen":INjasenID, "INelokuva":INelokuvaID, "INvuokraus":INvuokrausPVM})
				con.commit() # tehdään commit vaikka osa lisäyksistä epäonnistuisikin
				return redirect(url_for('index'))
			except:
				herja = "Muokkaus ei onnistu!"
				logging.debug( "Muokkaus ei onnistu!" )
				logging.debug( sys.exc_info()[0] )
				logging.debug( sys.exc_info()[1] )

			return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)

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
				herja = "Poistaminen ei onnistu!"
				logging.debug( "Poistaminen ei onnistu!" )
				logging.debug( sys.exc_info()[0] )
				logging.debug( sys.exc_info()[1] )

		return render_template("muokkaa.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, INjasenID=INjasenID, INelokuvaID=INelokuvaID, INvuokrausPVM=INvuokrausPVM, INpalautusPVM=INpalautusPVM, INmaksettu=INmaksettu)

	# Jos ei löydy niin ohjataan kirjautumissivulle
	return redirect(url_for('login'))

@app.route("/elokuvat", methods=['POST','GET'])
def elokuvat():
	# Jos käyttäjätunnus löytyy sessiosta niin ollaan kirjautuneita
	if 'username' in session:
		# return 'Logged in as %s' % escape(session['username'])
	
		# os.path.abspath muuntaa suhteellisen polun absoluuttiseksi, joka taasen kelpaa sqlitelle
		con = sqlite3.connect(os.path.abspath('data/video'))

		# voidaan käsitellä palautettuja tietueita niiden kenttien nimillä
		con.row_factory = sqlite3.Row

		cur = con.cursor()

		# Sarake järjestystä varten taulukolle, jos tullaan uudestaan sivulle session aikana,
		# järjestysvalinta pysyy tallessa
		order = request.values.get('order', '')
		if len(order) > 0:
			session['jarj'] = order
		if len(order) == 0 and len(session['jarj']) > 0:
			order = session['jarj']

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

	# Jos ei löydy niin ohjataan kirjautumissivulle
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# Kirjaudutaan sisään. Sijoitetaan session-muuttujaan käyttäjätunnus
		session['username'] = request.form['username']
		return redirect(url_for('index'))
	return render_template('login.html')

@app.route('/logout')
def logout():
	# Poistetaan tunnus sessiosta
	session.pop('username', None)
	return redirect(url_for('index'))

if __name__ == "__main__":
	app.run(debug=True)