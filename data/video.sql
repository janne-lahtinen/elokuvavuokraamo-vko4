PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS Vuokraus;
DROP TABLE IF EXISTS Elokuva;
DROP TABLE IF EXISTS Lajityyppi;
DROP TABLE IF EXISTS Jasen;


CREATE TABLE Jasen (
JasenID INTEGER PRIMARY KEY AUTOINCREMENT,
Nimi VARCHAR(100) NOT NULL,
Osoite VARCHAR(150) NOT NULL,
LiittymisPVM DATE NOT NULL CHECK(Liittymispvm > Syntymavuosi AND Liittymispvm <= CURRENT_DATE),
Syntymavuosi INTEGER NOT NULL CHECK(Syntymavuosi >= 1900)
)
;

CREATE TABLE Lajityyppi (
LajityyppiID INTEGER PRIMARY KEY AUTOINCREMENT,
Tyypinnimi VARCHAR(100) NOT NULL
)
;

CREATE TABLE Elokuva (
ElokuvaID INTEGER PRIMARY KEY AUTOINCREMENT,
Nimi VARCHAR(256) NOT NULL,
Julkaisuvuosi INTEGER NOT NULL CHECK(julkaisuvuosi >= 1900 AND julkaisuvuosi <= 2017),
Vuokrahinta NUMERIC(5) NOT NULL CHECK(vuokrahinta > 0),
Arvio INTEGER NOT NULL CHECK(arvio >= 0 AND arvio <= 10),
LajityyppiID INTEGER NOT NULL,

CONSTRAINT Elokuva_LajityyppiID 
	FOREIGN KEY (LajityyppiID)
	REFERENCES Lajityyppi (LajityyppiID)
		ON DELETE NO ACTION
		ON UPDATE CASCADE
)
;

CREATE TABLE Vuokraus (
JasenID INTEGER NOT NULL,
ElokuvaID INTEGER NOT NULL,
VuokrausPVM DATE DEFAULT CURRENT_DATE,
PalautusPVM DATE CHECK (Palautuspvm >= Vuokrauspvm),
Maksettu NUMERIC(6) DEFAULT 5.0 CHECK (Maksettu >= 0),
CONSTRAINT Vuokraus_PK
	PRIMARY KEY (JasenID,ElokuvaID,VuokrausPVM),
CONSTRAINT Vuokraus_JasenID 
	FOREIGN KEY (JasenID)
	REFERENCES Jasen (JasenID)
		ON DELETE NO ACTION
		ON UPDATE CASCADE,
CONSTRAINT Vuokraus_ElokuvaID 
	FOREIGN KEY (ElokuvaID)
	REFERENCES Elokuva (ElokuvaID)
		ON DELETE NO ACTION
		ON UPDATE CASCADE
)
;


INSERT INTO jasen (jasenid, nimi, osoite,liittymispvm, syntymavuosi) 
VALUES (1,'Tommi Lahtonen', 'Nörttikuja 3','2009-01-01', 1998)
;
INSERT INTO jasen (jasenid, nimi, osoite,liittymispvm, syntymavuosi) 
VALUES (2,'Matti Virtanen','Tavallinentie 1','2009-02-15', 1990)
;
INSERT INTO jasen (jasenid, nimi, osoite,liittymispvm, syntymavuosi) 
VALUES (3,'Petri Heinonen','Kivakatu 2','2008-12-13', 1998)
;
INSERT INTO jasen (jasenid, nimi, osoite,liittymispvm, syntymavuosi) 
VALUES (4,'Matti Meikäläinen','Meikämannentie 12','2009-02-15', 1990)
;
INSERT INTO jasen (jasenid, nimi, osoite,liittymispvm, syntymavuosi) 
VALUES (5,'Maija Meikäläinen','Meikämannentie 12','2008-04-01', 1991)
;
INSERT INTO jasen (jasenid, nimi, osoite,liittymispvm, syntymavuosi) 
VALUES (6,'Olli Opiskelija','Nörttikatu 15','2014-01-01', 1990)
;
INSERT INTO jasen (jasenid, nimi, osoite,liittymispvm, syntymavuosi) 
VALUES (7,'Ville Vidiootti','Nörttikuja 3','2010-04-05', 1990)
;
INSERT INTO jasen (jasenid, nimi, osoite,liittymispvm, syntymavuosi) 
VALUES (8,'Leila Leffafani','Leffatie 1','2010-01-01', 1993)
;
INSERT INTO jasen (jasenid, nimi, osoite,liittymispvm, syntymavuosi) 
VALUES (9,'Matti Virtanen','Metsäpolku 22','2010-02-15', 2000)
;


INSERT INTO lajityyppi (tyypinnimi)
VALUES ('Komedia')
;

INSERT INTO lajityyppi (tyypinnimi)
VALUES ('Toiminta')
;

INSERT INTO lajityyppi (tyypinnimi)
VALUES ('Draama')
;

INSERT INTO lajityyppi (tyypinnimi)
VALUES ('Kauhu')
;




INSERT INTO elokuva (elokuvaid, nimi,julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (1,'Zootopia',2016,3,6,3)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (2,'What women want',2001, 3, 5, 1)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (3,'Chocolat',1999,3,5, 1)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (4,'Ghostbusters',1984,5,10,3)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (5,'Deadpool',2016, 3, 7, 2)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (6,'Almost Famous',2000,3,8,3)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (7,'La La Land',2016,3,9,3)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (8,'Crouching tiger, hidden dragon',2002,5,10,2)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (9,'Gladiator',2002,5,10,2)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (10,'Traffic',2001,5,8,3)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (11,'Ghostbusters',2016,5,7,3)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (12,'Hannibal',2002,5,10,4)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (13,'Remember the Titans',2001,3,5,3)
;
INSERT INTO elokuva (elokuvaid, nimi, julkaisuvuosi, vuokrahinta, arvio, lajityyppiid) 
VALUES (14,'Clockwork Orange',1972,3,6,3)
;


INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (2,1,'2013-05-13','2013-05-14')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (3,2,'2014-05-13','2014-05-14')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (3,3,'2015-05-13','2015-05-14')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (7,4,'2016-05-13','2016-05-14')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (7,5,'2011-05-13','2011-05-14')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (7,6,'2015-06-13','2015-06-14')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (7,7,'2013-05-11','2013-05-12')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (7,8,'2013-07-09','2013-07-10')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (5,9,'2013-06-13','2013-06-14')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (3,10,'2013-06-13','2013-06-14')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (2,1,'2013-06-13','2013-06-14')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (5,8,'2013-02-13','2013-02-14')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (5,11,'2013-01-01','2013-01-02')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (5,3,'2013-06-10','2013-06-11')
;

INSERT INTO vuokraus (jasenid,elokuvaid,vuokrauspvm,palautuspvm) 
VALUES (5,4,'2013-06-18','2013-06-19')
;




