Entwickle ein GUI Frontend für diese Applikation 
mit folgenden Eigenschaften:

* Schreibe den Dateinamen und die Verzeichnisstruktur in die Dateien oben in einer Kommentarzeile.
* Die GUI soll im gleichen Projekt in einem eigenen Paket mit dem Namen
    multiconverter.gui abgelegt werden. Entsprechende Abhängigkeiten werden in der
    vorhandenen Datei pyproject.toml ergänzt.
* Die Desktop GUI soll sich starten lassen mit
    `python -m multiconverter_gui`, so dass eine entsprechende __main__.py
    erforderlich ist. Außerdem soll die GUI über ein entry_point in der
    pyproject.toml Datei mit dem Befehl `multiconverter-gui` gestartet werden
    können.
* Die GUI soll plattformunabhängig sein und auf Windows, MacOS und Linux lauffähig sein.
* Verwendet werden soll das Framework `flet`. Das Programm ist
    im Wizard UI Style aufgebaut:
    * Auf der ersten Seite kann aus den vorhandenen Fragetypen ausgewählt werden (siehe question_handlers_map in der
        Klasse QuestinHandlers). Die Auswahl erfolgt über Checkboxen. Außerdem kann ein mehrzeiliger Prompt eingegeben
        werden. Darunter befindet sich ein Ausgabefeld, in dem der eingegebene Prompt zusammen mit der XSD angezeigt wird.
        Darunter befindet sich ein Button 'Copy to Clipboard', der den Inhalt des Ausgabefeldes in die Zwischenablage kopiert.
        Ein weiterer Button 'Weiter' startet den nächsten Schritt.
    * Auf der zweiten Seite kann in einem mehrzeiligen Eingabefeld die XML Ausgabe des LLM hineinkopiert werden. Darunter  befindet sich
        ein Button 'Validieren', der die XML Ausgabe anhand der XSD validiert. Wenn die Validierung erfolgreich ist, wird
        der Button 'Weiter' aktiviert, der zum nächsten Schritt führt. Bei fehlerhafter Validierung wird eine
        Fehlermeldung für das LLM angezeigt, wie sie auch von der Kommandozeile bekannt ist. Darunter befindet sich ein Button 'Copy to Clipboard',
        der die Fehlermeldung in die Zwischenablage kopiert.
    * Auf der dritten Seite werden die validierten Fragen nacheinander in einem Editorfenster angezeigt. In dem Fenster werden
        Tags farbig hervorgehoben. In diesem Fenster kann der Nutzer den Quelltext der Frage bearbeiten und hat anschließend als Buttons 'Sichern' und 'Verwerfen' zur
        Auswahl. Verwerfen löscht die jeweilige Frage. Sichern prüft das editierte XML anhand der XSD und wenn es fehlerhaft ist, wird der Nutzer aufgefordert, das
        XML zu korrigieren. So bald ein gültiges XML Dokument gesichert werden soll, wird die Frage in die Hauptliste übernommen.
    * Nachdem alle erzeugten Fragen vom Nutzer entweder gesichert oder verworfen wurden, wird dem Nutzer über Buttons das Speichern von zwei Dokumenten
        ermöglicht: eine XSD konformes XML Dokuments der gesicherten Fragen und ein vom vorhandenen multiconverter code erzeugten zip Archiv.  Außerdem kann über die
        Auswahl 'Weitere Fragen hinzufügen' ein weiterer Durchlauf durch den Wizard gestartet werden, der weitere Fragen ergänzt.