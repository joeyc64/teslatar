# teslatar V2
Projekt 'Teslatar' ist speziell für Teslas und für den Stromanbieter aWATTar entwickelt, lädt das Auto anhand verschiedener Kriterien möglichst optimal, so dass jeden morgen ein geladenes Auto zu Verfügung steht. Dabei funktioniert das unabhängig der verwendeten Ladestruktur (Wallboxen). Es wird ein Raspberry Pi Mini Computer benötigt und dieser muss dauerhaft laufen und mit dem Internet verbunden sein.

Hinweis zum Update Teslatar V2:
Tesla hat Ende 2020 die Passwort-Logik verändert bzw. erweitert. Man kann nun eine 2-Faktor Authorisierung hinterlegen. Teslatar berücksichtigt dies nun mit Hilfe der "TeslaPy" Library. Es wird also nicht mehr "Teslajson" verwendet.

Worum geht's hier?
Elektroautos müssen geladen werden. Möglichst zu einem günstigen Tarif, zu einer Zeit an der die Belastung des Stromnetzes gering ist und natürlich möglichst mit Ökostrom. Stromanbieter gibt es wie Sand am Meer und es lohnt sich hier jährlich umzusehen und evtl. den Anbieter zu wechseln.

Dieses Projekt ist speziell für den Stromanbieter aWATTar.de ausgelegt. aWATTar kommt ursprünglich aus Österreich und bietet seit Anfang 2019 auch in Deutschland seinen Strom an. Das besondere an aWATTar ist, dass hier der Stromtarif anhand dem aktuellen Börsenstrompreis abgebildet wird. Stand 09/2019 ist das meines Wissens nach der einzige Anbieter der das so macht.
Der Börsenstrompreis wird anhand Angebot und Nachfrage gebildet und ändert sich stündlich. aWATTar gibt diesen Strompreis 1:1 weiter, abfragbar über eine einfache Datenschnittstelle die immer die zukünftigen 24 Stunden vorhält. D.h. es ist recht einfach zu ermitteln, wann der Strom 'günstig' ist (d.h. im Überschuss vorhanden ist) und man dann sein Elektroauto laden sollte.

Wie der Name Teslatar schon andeutet geht es hier auch speziell um Autos der Marke Tesla. Warum? Weil ich Tesla fahre ;-) Und weil Tesla eine offene Datenschnittstelle zur Verfügung stellt, die eine sehr komfortable Ladesteuerung ermöglicht. Das tolle daran ist, dass es völlig egal ist, _wie_ der Tesla geladen wird. Ob mit einer Wallbox oder mit dem Tesla-UMC-Ladestecker der im Lieferumfang dabei ist. Das Auto muss lediglich eingesteckt sein, ab dann übernimmt dieses Projekt die Steuerung und lädt das Auto nach verschiedenen Kriterien. (Man braucht also keine Datenschnittstelle zur Wallbox)

Das Programm selbst ist ein Python Script, dass 24/7 auf einem Raspberry Pi laufen muss mit dauerhafter Internetanbindung.

Was 'macht' Teslatar?
Teslatar steuert in erster Linie den Ladevorgang so, dass nur in den Stunden geladen wird, an denen der Strompreis am günstigsten ist. 
Das funktioniert so: Das Ladekabel wird eingesteckt. Teslatar erkennt das über die Online-Tesla-Schnittstelle. Es wird ein kurzer Ladevorgang gestartet, um zu ermitteln wie lange es dauern _würde_ das Auto bis zum eingestellten Ladestand zu laden. Teslatar berechnet die Ladedauer also _nicht_ selber, sondern überlässt das dem Auto, was sehr, sehr genau ist. Nun weiß Teslatar also wie lange es dauern würde um das Auto zu laden und es werden jetzt die günstigsten Ladestunden ermittelt, die derzeit von aWATTar über die Schnittstelle bereitgestellt sind. Teslatar ist so programmiert, dass spätestens um 7 Uhr morgens das Auto den eingestellten Ladestand erreichen wird. Die Ladung erfolgt also ausschließlich in den günstigen Stunden ABER spätestens um 7 Uhr ist das Auto voll.
Die aWATTar Preisdaten werden jede neue Stunde erneut ausgelesen. Um 14 Uhr jeden Tag werden übrigens die Börsendaten des Folgetags bereitgestellt. Und falls sich Änderungen in den Stundenpreisen ergeben sollten wird Teslatar die Ladezeiten neu errechnen. Ebenso werden die Ladezeiten neu berechnet, wenn über die Tesla-App manuell der Ladebalken verändert wird. Es wird dann wieder kurz eine Ladung gestartet, damit das Auto dem Script die neuen Ladedauern mitteilen kann.
Außerdem muss Teslatar der GPS-Standort des eigenen Hauses konfiguriert werden. Denn nur hier soll ja die Ladelogik aktiv werden, nicht an anderen Ladestationen/Superchargern.

Wie kann man Teslatar steuern?
1. Wenn im Auto am Ladebildschirm auf "Laden geplant" gestellt wird, also üblicherweise dann auf eine Uhrzeit, NUR DANN ist die Teslatar Ladelogik mit aWATTar Preisen aktiv. Die Uhrzeit kann hier keine Bedeutung mehr, da ja Teslatar die Steuerung übernommen hat. (Trotzem: Hier auf 00:00 stellen, falls sich der Raspi mal aufhängt, so dass dennoch geladen wird!)
2. Das bedeutet im Umkehrschluss: Sobald man im Ladebildschirm auf "Sofort laden" schaltet, wird auch immer der Ladevorgang sofort gestartet und geladen. Unabhängig von den momentanen Preisen. Diese Funktion ist dann wichtig, wenn man zuhause ankommt und z.B. weiß, dass man in 2 Stunden wieder eine längere Fahrt hat, oder aus welchem Grund auch immer.
3. Es gibt noch eine dritte Möglichkeit zu steuern. Man stellt den Ladebalken auf 100% und das Laden beginnt sofort, bis die 100% erreicht sind. Wafür das?
Normalerweise würde man den Ladebalken nicht täglich auf 100% setzen, sondern üblicherweise auf 80% um die Batterie zu schonen. Plant man für morgen aber eine lange Fahrt und möchte die vollen 100% nutzen, dann geht man so vor: Den Ladebalken auf 95% stellen, d.h. um 7 Uhr morgens ist die Batterie garantiert auf 95% geladen mit aWATTar Preisen. Wenn man nun um 10 Uhr losfahren möchte stellt man ca.30 Minuten vorher den Ladebalken auf 100%, das Laden beginnt nun sofort und man hat zum gewünschten Zeitpunkt die volle Ladung.
Hinweis: Die Einstellung "Laden geplant" kann man nur im Auto vornehmen, den Ladebalken setzen kann man im Auto oder in der Tesla-App, was natürlich bequemer ist.

Was sonst noch?
* Teslatar überwacht zwar ständig 24/7 die Autos, berücksichtigt aber den Schlaf-Modus. D.h. es wird dem Auto Gelegenheit gegeben in den Stromsparmodus zu gehen. Das funktioniert und ist getestet mit Model S, X und 3, in den HW-Versionen 2.5 und 3.0 (Tipp: Innenraumtemperaturüberwachung ausschalten, ansonsten wacht S/X jede 60 Minuten auf!)
* Update Teslatar2 - Auch mit eingestecktem Ladekabel geht das Auto in den Schlafmodus
* Teslatar funktioniert auch mit mehreren Tesla gleichzeitig, getestet mit 3 Teslas sichtbar in der Tesla-App. Es können auch z.B. 2 Teslas an 2 Wallboxen eingesteckt sein.
* Fällt das Internet aus oder sind die APIs von Tesla oder aWATTar nicht abrufbar, wird alles in der Software abgefangen und es wird fortgesetzt, wenn wieder alles funktioniert. Daher ist es wichtig, dass der Ladezeitpunkt bei "Laden geplant" auf 00:00 Uhr gesetzt wird. So ist genügend Zeit bis morgens vorhanden und die Strompreise sind nachts sowieso auch bei aWATTar immer günstig (->Nachtüberschuss, Preise gehen runter).
* Ist der Ladestand < 10% beim Einstecken dann wird immer sofort geladen bis 10% erreicht sind um die Batterie zu schonen, erst dann setzt die Ladelogik ein.

Was fehlt noch? Todo?
Ich selbst besitze zwar eine PV-Anlage, allerdings noch eine aus 2005 mit Volleinspeisung. Daher macht es für mich keinen Sinn, die Ladelogik mit der momentanen Einspeiseleistung zu koppeln. Wer aber eine PV-Anlage mit Eigennutzung hat, für den würde es tagsüber durchaus Sinn machen. Man müsste Teslatar hier erweitern um die Momentan-Überschusswerte aus der PV-Anlage zu bekommen und damit dann die Ladeleistung am Auto in Ampere zu steuern. Wie genau und zeitlich akurat das passieren könnte sei dahin gestellt. Vielleicht geht das mit der Tesla-Powerwall? Die Datenschnittstelle sollte das hoffentlich hergeben.

Installation
Benötigt an Hardware wird (mindestens):
* 1 Raspberry PI 3 - Model B (+ nicht notwenig, neuere Modelle gehen natürlich bräuchte man aber nicht)
* Gehäuse
* Netzteil
* Min. 16GB SD Karte
* HDMI Kabel + Monitor + USB-Tastatur + USB-Maus zur Installation
und Internet per Lan-Kabel oder Wifi

Die Installation hier beschreibt eine komplette NEU Installation. Wer also bereits einen Raspi am Laufen hat oder etwas mehr Ahnung hat kann natürlich 1 und 2 überspringen und direkt bei 3 weitermachen. Generell muss eben Python laufen, man muss das Paket TeslaPy und den Teslatar von Gitgub installieren, mit einem Texteditor etwas konfigurieren und das wars auch schon.

(1)
Rasperry PI OS installieren
Für Teslatar sollte das Raspberry PI OS auf eine mind.16GB SD Karte installiert werden. https://www.raspberrypi.org/software/
Zuerst von der Webseite den Raspberry Pi Imager runterladen und auf dem PC starten, es gibt auch ein kleines Video als Erklärung dazu.
Dann das Raspebrry Pi OS (32-bit) auswählen und die SD-Karte wählen, die im PC eingesteckt sein muss. Dann "Schreiben" klicken. Es wird nun die SD-Karte entsprechend formatiert und das OS geladen und installiert.


Dann die SD-Karte in den Raspberry einsetzen und Strom ein. HDMI Kabel zu einem Monitor nicht vergessen, ebenso eine Tastatur und Maus per USB.
Es wird nun ein Welcome-Fenster dargestellt, dort Country auf Germany und alles weitere einstellen.
Evtl. auch ein Wifi-Netzwerk konfigurieren. Per Kabel geht natürlich auch. Aber Internet wird benötigt. Das "Update Software" auch ausführen lassen. Dann wird ein Neustart durchgeführt.

(2)
Remote Desktop installieren
Der Raspi sollte so konfiguriert werden, dass man bequem ohne Monitor jederzeit darauf zugreifen kann. Ich verwende hier den Microsoft Remote Desktop, der wunderbar und für alle Betriebssysteme funktioniert (auch MacOS).
Unter Raspbian ein Terminal Fenster öffnen und dort folgendes eingeben (jeweils mit J bestätigen):
    sudo apt-get purge realvnc-vnc-server
    sudo apt-get install xrdp
Für den Remote-Zugriff später benötigt man natürlich die Netzwerk Adresse des Raspis, ermitteln kann man die nun mit:
    ip a
Unter ETH0 oder WLAN0 kann man die Netzwerkadresse erkennen. Die kann sich aber ändern, evtl. sollte man eine feste IP Adresse konfigurieren.
Nun den Raspi neu starten mit:
    sudo reboot
  
(3) 
Teslatar installieren! 
Als erstes wieder ein Terminal Fenster öffnen und 
    mkdir dev
    cd dev
eingeben. 
Jetzt die notwendigen Projekte von Github laden. Folgendes eingeben:
    sudo apt-get install python-pip
    python -m pip install teslapy
    git clone https://github.com/tdorssers/TeslaPy
    git clone https://github.com/Joeykarwath/teslatar
    cd teslatar
    
Als nächstes muss man sich einmalig bei Tesla authentifizieren. Es wird dann ein Access-Token und ein Refresh-Token im Teslatar-Verzeichnis abgelegt, so dass man diesen Vorgang niemals mehr ausführen muss. Ausser es ändert sich irgendwas am PW, Authenticator oder so, dann muss man das hier eben nochmals durchexerzieren.
Tesla bietet ja seit Ende 2020 eine 2-Faktor Authentifizierung an. Wenn man diese aktiv hat, dann direkt Punkt 2 ausführen. Wenn nein nur Punkt 1.

PUNKT 1:
Folgende Kommandos eingeben:
python ../TeslaPy/cli.py -e teslaaccountemail -p teslapassword
Jetzt wird die Anzahl Produkte (Autos, Wallboxen) angezeigt und und das Access- und Refresh-Token in einer Cache Datei dauerhaft abgelegt.


PUNKT 2:
Wenn die 2-Faktor Authentifizierung aktiv ist, dann muss einmalig auch hier die Authentifizierung vorgenommen werden. Dazu benötigt man natürlich die Tesla-Account-Email und das Passwort. Dann muss man den zeitabhängigen Auth-Code, z.B. im Google Authenticator, ermitteln (6 stellige Zahl) und man muss den Namen des Authenticators wissen. Am besten geht man so vor: Im Web-Browser nach TESLA.COM gehen und sich dort anmelden. Wenn man bereits angemeldet war, unbedingt zuerst abmelden, dann gleich wieder anmelden. Tesla frägt nach Account-Email und dem Passwort. Das eingeben und OK klicken. Dann auf "Einstellungen", dann auf "Multi-Faktor-Auth.", dann auf "Verwalten". Dann auf "Registrierte Geräte - Verwalten" - hier steht nun der Klartextname des Authenticators, wie er bei Tesla angemeldet ist. Exakt diesen Namen braucht man nun, genauso benötigt man den 6-stelligen Code aus der entsprechenden Authenticator App. Der Code ist nur 30 Sekunden gültig, also alles muss schnell gehen :-) Die Command-Zeile also schon mal eingeben und dann zum Ende schnell den 6-stelligen Code dazu tippen:
Folgende Kommandos eingeben:
python ../TeslaPy/cli.py -e teslaaccountemail -p "teslapassword" -u "NameAuthenticator" -t "6StellCode" 
(Tipp: Evtl. Option-Q für @ auf Mac drücken)
Jetzt wird die Anzahl Produkte (Autos, Wallboxen) angezeigt und INTERN wird nun in einem Cache das Access und Refresh Token abgelegt.
 
Nun muss die Datei 'teslatar.py' editiert werden. Ganz am Anfang müssen die Variablen für den Tesla-Zugang eingefügt werden, also Username und Password. Außerdem muss Längen- und Breitengrad der Heimat-Wallbox ermittelt werden. Dazu diesen Link aufrufen
https://www.latlong.net/convert-address-to-lat-long.html
Dann diese Daten ins das Python script einsetzen. Evtl. noch die Wallbox-Max-Leistung konfigurieren in kW - default sind hier 11, was meistens passen sollte.
Dann die Datei speichern. Weiter gehts, folgendes eingeben:
    chmod +x start
    chmod +x stop
    chmod +x install_teslatarservice
    ./install_teslatarservice
Es wird jetzt automatisch ein Reboot durchgeführt und der Remote Desktop schließt sich. Jetzt 30 Sekunden warten und dann neu den Desktop öffnen.
Die Steuerung sollte jetzt schon laufen! Kontrollieren kann man das über das log-file "file.log" im /dev/teslatar/ Verzeichnis.
Das "file.log" wächst im Laufe der Zeit an, evtl mal ein Auge drauf halten und ab und an löschen bevor es zu groß wird und die SD Karte volläuft.

Die Scripte start/stop dienen dazu den Teslatar-Dienst anzuhalten und wieder zu starten, wenn man z.B. Änderungen in "teslatar.py" gemacht hat.
