***********  SYSTEM-ANFORDERUNGEN  ************

Diese Implementierung wurde in Linux mit der Python-Distribution 'Anaconda' getestet:

Python 2.7.9 :: Anaconda 2.2.0 (64-bit)

Download-Link:

http://continuum.io/downloads
 - bitte waehlen Sie "Linux 64-Bit — Python 2.7"

Anaconda kann parallel zu anderen Python-Distributionen installiert werden.
Waehrend der Installation werden Sie gefragt, ob Anaconda zu Ihrem $PATH hinzugefuegt werden sollte. Falls Sie unsicher sind, was dies bedeutet, antworten Sie mit ja (dies kann spaeter wieder rueckgaengig gemacht werden).

Auf dem System sollten (bei einem 2700x1500-Bild) mind. 1,5 GB RAM verfuegbar sein.



*******************  VERWENDUNG  *******************

Um das Programm zu starten, oeffnen Sie ein Terminal-Fenster, navigieren in das Verzeichnis mit den Python-Quellcode-Dateien und geben ein:


    python main.py -f "Pfad/zum/Eingabebild.png"


Dies startet das Programm mit den default-Parametern. Diese wurden vor allem fuer Bilder der Groesse 2700x1500 Pixel optimiert, fuer andere Bildausmasse wird aber auch automatisch versucht, optimale Parameter zu finden.
Fuer eine Liste aller verfuegbaren Parameter geben Sie im Terminal-Fenster ein:
    
    python main.py --help

Falls die default-Parameter keine guten Ergebnisse liefern sollten, schalten Sie detailliertere Ausgaben ein, sowie das Anlegen von Hilfsdateien, an welchen der Konvertierungsprozess besser beobachtet werden kann:
    
    python main.py -f "Pfad/zum/Eingabebild.png" --verbose --otherfiles

Sind z. B. zu wenige Details zu erkennen, versuchen Sie, die Pinselstriche zu verkleinern. Falls das --verbose-Flag im vorigen Schritt eine Pinselstrichgroesse 'strokeWidth' von 80 Pixeln anzeigte, versuchen Sie es diesmal mit 50:
    
    python main.py -f "Pfad/zum/Eingabebild.png" --verbose --otherfiles --width=50

Oder schalten Sie zusaetzlich randomisierte Pinselstrichgroesse ein, mit Werten zwischen 40% und 100% der maximalen Pinselstrichbreite:
    
    python main.py -f "Pfad/zum/Eingabebild.png" --verbose --otherfiles --width=50 --randSizes=40

Aehnlich kann man mit anderen Parametern die Dichte der Pinselstriche, oder das Verhaeltnis zwischen der Anzahl der simplen und der komplexen Pinselstriche anpassen, sowie die Farbsaettigung, oder das Hintergrundbild, und vieles mehr.



**************  LAUFZEIT  ***************

Auf einem i5-Computer mit 8 GB RAM dauert die Bearbeitung eines 2700x1500-Bildes ungefaehr 2-4 Minuten.

Diese Zeit haengt vom Detailgrad des Bildes und von den gewaehlten Parametern ab.


***************  KONTAKT  ****************

Bei Fragen zum Programm schreiben Sie an

    afremize@gmail.com

Ich werde versuchen, zu antworten.