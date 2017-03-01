#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, session, redirect, url_for, escape, request, Response, render_template
import hashlib
import sqlite3
import logging
import os
import sys
import datetime

logging.basicConfig(filename=os.path.abspath('data/flask.log'),level=logging.DEBUG)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route("/", methods=['POST','GET'])
def index():
	# os.path.abspath muuntaa suhteellisen polun absoluuttiseksi, joka taasen kelpaa sqlitelle
	con = sqlite3.connect(os.path.abspath('data/video'))

	# voidaan käsitellä palautettuja tietueita niiden kenttien nimillä
	con.row_factory = sqlite3.Row

	sql = """
	SELECT E.Nimi, J.Nimi, V.VuokrausPVM, V.PalautusPVM, V.Maksettu
	FROM Vuokraus AS V, Jasen AS J, Elokuva AS E
	WHERE V.JasenID = J.JasenID AND E.ElokuvaID = V.ElokuvaID
	"""

	cur = con.cursor()

	try:
	   cur.execute(sql)
	except: 
	   # vaatii koodin alkuun rivin: import sys
	   logging.debug(sys.exc_info()[0])

	# sama kuin edellä mutta käytetään kenttien nimiä eikä indeksejä
	vuokraukset = []
	for row in cur.fetchall():
		vuokraukset.append( dict(eNimi=row[0], jNimi=row[1], vuokrausPVM=row[2], palautusPVM=row[3], maksettu=row[4]) )

	return render_template("index.html", vuokraukset=vuokraukset)


@app.route("/vuokraus", methods=['POST','GET'])
def vuokraus():
	# os.path.abspath muuntaa suhteellisen polun absoluuttiseksi, joka taasen kelpaa sqlitelle
	con = sqlite3.connect(os.path.abspath('data/video'))

	# os.path.abspath muuntaa suhteellisen polun absoluuttiseksi, joka taasen kelpaa sqlitelle
	sovellus = os.path.abspath('video.py')

	# voidaan käsitellä palautettuja tietueita niiden kenttien nimillä
	con.row_factory = sqlite3.Row

	cur = con.cursor()

	try:
		cur.execute("""
		SELECT Nimi, JasenID
		FROM Jasen
		""")
	except: 
	   # vaatii koodin alkuun rivin: import sys
	   logging.debug(sys.exc_info()[0])

	# sama kuin edellä mutta käytetään kenttien nimiä eikä indeksejä
	vuokraajat = []
	for row in cur.fetchall():
		vuokraajat.append( dict(nimi=row[0], jasenID=row[1]) )

	try:
		cur.execute("""
		SELECT Nimi, ElokuvaID
		FROM Elokuva
		""")
	except: 
	   # vaatii koodin alkuun rivin: import sys
	   logging.debug(sys.exc_info()[0])

	# sama kuin edellä mutta käytetään kenttien nimiä eikä indeksejä
	elokuvat = []
	for row in cur.fetchall():
		elokuvat.append( dict(nimi=row[0], elokuvaID=row[1]) )

	try:
		cur.execute(""" SELECT JasenId, nimi FROM Jasen
    	""")
	except: 
	   # vaatii koodin alkuun rivin: import sys
	   logging.debug(sys.exc_info()[0])

	jasenet = []
	for row in cur.fetchall():
		jasenet.append( dict(jasenID=row[0], nimi=row[1]) )

	# Virheilmoituksen alustaminen
	herja = ""

	# Lomakkeen käsittely -----------------------------------------------    
	# jos on valittu vuokraa-painike
	if request.form.get("vuokraa", None):
		insert_sql = """
			INSERT INTO Vuokraus (JasenID, ElokuvaID, VuokrausPVM, PalautusPVM, Maksettu)
			VALUES (:jasenid, :elokuvaid, :vuokrauspvm, :palautuspvm, :maksettu )
			"""
		# http://werkzeug.pocoo.org/docs/0.11/datastructures/
		# request.form on multidict-tyyppinen objekti
		elokuva = request.form.get("eNimi")
		# Jos jasenta ei ole annettu käytetään -1, joka kaataa executen
		jasen = request.form.get("vNimi", -1)
		vuokraus = request.form.get("vuokrausPVM")
		palautus = request.form.get("palautusPVM")
		maksettu = request.form.get("maksettu")

		# Syötettyjen päivämäärien muodon tarkistus
		try:
			 datetime.datetime.strptime(vuokraus, '%Y-%m-%d')
		except ValueError:
			herja = u"Vuokrauspäivä syötetty väärässä muodossa, pitäisi olla, vuosi-kuukausi-päivä eli vvvv-kk-pp"
			return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, sovellus=sovellus)
		try:
			 datetime.datetime.strptime(palautus, '%Y-%m-%d')
		except ValueError:
			herja = u"Palautuspäivä syötetty väärässä muodossa, pitäisi olla, vuosi-kuukausi-päivä eli vvvv-kk-pp"
			return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, sovellus=sovellus)

		# Syötettyjen päivämäärien tarkistus, palautus pitää olla suurempi
		try:
			if palautus <= vuokraus:
				herja = u"Palautuspäivämäärän pitää olla vuokrauspäivää myöhemmin!"
				return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, sovellus=sovellus)
		except:
			logging.debug( "Palautuspäivän tarkistus ei onnistunut!" )
			logging.debug( sys.exc_info()[0] )

		# Syötetyn maksun tarkistukset, jos nolla tai vähemmän --> try, jos ei INT, except
		try:
			maksettuINT = int(maksettu)
			if maksettuINT <= 0:
				herja = u"Syötit liian pieniä arvoja, yritä uudestaan."
		except:
			herja = u"Syötit vääriä arvoja, yritä uudestaan."
			logging.debug( "Maksetun summan tarkistus ei onnistu!" )
			logging.debug( sys.exc_info()[0] )

		# return Response(str(elokuva) + " / " + str(jasen) + " / " + str(vuokraus) + " / " + str(palautus) + " / " + str(maksettu), content_type="text/plain; charset=UTF-8")
		# Lisäys kaatuu jos yritetään vuokrata sama elokuva samalle henkilölle useammin kuin kerran		
		try:
			cur.execute(insert_sql, {"jasenid":jasen, "elokuvaid":elokuva, "vuokrauspvm":vuokraus, "palautuspvm":palautus, "maksettu":maksettu})
			con.commit() # tehdään commit vaikka osa lisäyksistä epäonnistuisikin
			return redirect(url_for('index'))

		except:
			herja = "Elokuva on jo henkilöllä vuokrattuna!"
			logging.debug( "Vuokraus ei onnistu!" )
			logging.debug( sys.exc_info()[0] )
			logging.debug( sys.exc_info()[1] )

		return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, sovellus=sovellus)
			
	return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat, herja=herja, sovellus=sovellus)

if __name__ == "__main__":
	app.run(debug=True)