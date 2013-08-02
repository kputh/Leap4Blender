********************************************************************************
* Projekteserver Subversion ****************************************************
********************************************************************************

Diese Datei wurde beim ersten automatischen Import gemeinsam mit den Ordnern
branches, tags und trunk erstellt. Du kannst sie gefahrlos löschen.

Falls du dich fragst, was diese drei Ordner zu bedeuten haben, solltest du
weiter lesen:

trunk
=====
Dies ist der Hauptentwicklungszweig eines Projektes. Im Grunde ist dies der ein-
zige wirklich notwendige Ordner. Er ist in jedem Repository enthalten, und sei
es nur implizit durch das fehlen einer normalen tags/branches-Struktur. Hier
werden neue Features eingeführt und das Projekt aktiv entwickelt. Anfänger
nutzen im einfachsten Fall nur diesen Ordner. Tags und Branches sind leicht
fortgeschrittene Konzepte.

Trunk ist die "Spitze" der Entwicklung.

tags
====
Tags sind Schnappschüsse des Entwicklungsstandes eines Repositories. Da Sub-
version niemals Dateien im Ganzen speichert, sondern lediglichdie Differenzen
zur vorigen Version dieser Datei, ist es möglich, mit "svn copy" einfach das
Repository in diesen Ordner zu kopieren (ganz wichtig: Niemals ein normales copy
wie das des Windows Explorers nutzen!), ohne dass das Repository auf dem Server
dadurch an Größe gewinnt.
Tags sind nicht veränderbar. Dies hat im realen Leben vorteile, wenn z.B. Dritt-
anbieter von der Unverändertheit eines Codes zum Entwickeln eigener Plugins
abhängig sind.

Tags sind feste Versionen, mit denen bspw. Pluginentwickler arbeiten.

branch
======
Ein Branch ist, ähnlich wie ein Tag, ein Schnappschuss des Entwicklungsstandes
eines Projektes. Im Gegensatz zum Tag kann und sollte ein Branch weiterentwick-
elt werden, jedoch werden hier keine neuen Features eingeführt, sondern Bugs
gefixt.

Branches sind somit Entwicklungszweige, die parallel zum Trunk geführt werden.
In der Realität sind das meist ältere Programmversionen, welche mit Sicherheits-
patches versorgt werden, während in anderen, neueren Branches (Versionen) auch
neue Features enthalten sind. Mit svn merge können Bugfixes aus einem Branch
ganz einfach in den Trunk überführt werden.



Subversion setzt die Konzepte Tag und Branch nicht hart durch. Das sind alles
ganz normale Ordner - Es liegt an eurer Projektorganisation, Regeln zu schaffen,
wie ihr mit diesen Konzepten umgeht. Viele Subversion-Fähige Tools enthalten
diese Strukturen jedoch auch als Konvention, sodass es sich anbietet, die gege-
bene Ordnerstruktur beizubehalten.
Für weitere Informationen hält Google unter den Stichworten subversion, tags,
trunk und branches viele nützliche Tutorials bereit.