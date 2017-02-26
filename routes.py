from flask import Flask, render_template
import sqlite3
import logging
import os

# oletetaan että sovellus on kansiossa /~omatunnus/cgi-bin/ohjaus4/
# /~omatunnus/vko4site/
# ja tietokanta on kansiossa /~omatunnus/hidden/
# /~omatunnus/vko4site/data/
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
#	vuokraukset.append( dict(eNimi=row['E.Nimi'], jNimi=row['J.Nimi'], vuokrausPVM=row['V.VuokrausPVM'], palautusPVM=row['V.PalautusPVM'], maksettu=row['V.Maksettu']) )

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route("/")
def index():
	return render_template("index.html", vuokraukset=vuokraukset)

@app.route("/vuokraus")
def vuokraus():
	return render_template("vuokraus.html")

if __name__ == "__main__":
	app.run(debug=True)