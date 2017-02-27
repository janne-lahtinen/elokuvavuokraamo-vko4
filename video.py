from flask import Flask, render_template
import sqlite3
import logging
import os
import sys

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

	return render_template("vuokraus.html", vuokraajat=vuokraajat, elokuvat=elokuvat)

if __name__ == "__main__":
	app.run(debug=True)