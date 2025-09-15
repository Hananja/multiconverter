# multiconverter
Converter tool from LLM output to QTI itslearning test.

# Installation

```
python -m pip install git+https://github.com/Hananja/multiconverter.git
```

# Aufruf

```
python -m multiconverter <output_file>.zip <input_file1>.xml [<input_file2>.xml ...]
```

Ohne Parameter wird eine Hilfe ausgegeben:

```
$ ./bin/python -m multiconverter
Usage: python -m multiconverter <output_file>.zip <input_file1>.xml [<input_file2>.xml ...]
Process one or more AI generated XML files

Message to LLM:  ----------------------------------
Die Ausgabe soll ausschließlich im XML Format erfolgen und der folgenden XSD genügen: <?xml version='1.0' encoding='utf-8'?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/Hananja/multiconverter" elementFormDefault="qualified" targetNamespace="https://github.com/Hananja/multiconverter"><!--The comments are also used to inform AI LLM--><xs:element name="questions"><xs:complexType><xs:sequence><xs:choice minOccurs="0" maxOccurs="unbounded"><xs:element ref="multiple-choice-question"/><xs:element ref="fill-in-question"/></xs:choice></xs:sequence></xs:complexType></xs:element><xs:complexType name="option"><xs:simpleContent><xs:extension base="xs:string"><xs:attribute name="correct" use="required"><xs:simpleType><xs:restriction base="xs:string"><xs:enumeration value="true"/><xs:enumeration value="false"/></xs:restriction></xs:simpleType></xs:attribute></xs:extension></xs:simpleContent></xs:complexType><xs:element name="multiple-choice-question"><!--This question type presents a task in the <text> element. This can be one or more correct answers by selecting the correct ones from the <options>.--><xs:complexType><xs:sequence><xs:element name="text" type="xs:string"/><xs:element name="options"><xs:complexType><xs:sequence><xs:element name="option" maxOccurs="unbounded" type="option"/></xs:sequence></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element><xs:element name="fill-in-question"><!--This question type presents a task in the <text> element. The <fill-in-text> element contains a task text that may contain gaps. These are marked with <fill> and must be filled in during the test. The correct possible alternatives for the answer are contained in <alt> tags within a <fill> element.--><xs:complexType><xs:sequence><xs:element name="text" type="xs:string" minOccurs="0"/><xs:element name="fill-in-text"><xs:complexType mixed="true"><xs:sequence><xs:element name="fill" minOccurs="0" maxOccurs="unbounded"><xs:complexType><xs:sequence><xs:element name="alt" type="xs:string" maxOccurs="unbounded"/></xs:sequence></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>

Erstelle ein Beispieldokument mit je zwei Fragen pro Fragetyp
```


Es ist empfehlenswert, zunächst die gesamte erzeugte XM--Datei zu verarbeiten,
weil bei eventuellen Fehlern der KI eine Fehlermeldung ausgegeben wird, die das
LLM auffordert, die Ausgabe zu korrigieren:

```
$ ./bin/python -m multiconverter output.zip test_raw.xml 
Ungültig: test_raw.xml
The document test_raw.xml is not correct.

Message to LLM:  ----------------------------------
Überleg noch einmal: Das Dokument entspricht nicht der XSD. Der Parser liefert den Fehler "XML-Syntax-Fehler: StartTag: invalid element name, line 141, column 37 (test_raw.xml, line 141)".
```

Wenn die Kommunikation mit dem LLM  nach  mehreren  Iterationen fehlerfrei funktioniert hat, können die XML
Dateien editiert und angepasst werden (z. B. durch Löschen von Fragen).
