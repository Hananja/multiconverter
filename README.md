# multiconverter
Converter tool from LLM output to QTI itslearning test.

# Installation

with [`pipx`](https://pipx.pypa.io) (recommended):

```
pipx install git+https://github.com/Hananja/multiconverter.git
```
with plain old pip:
```
python -m pip install git+https://github.com/Hananja/multiconverter.git
```

Installation with virtual environment for non admins:

```
python -c "import venv,subprocess,os; d='multiconverter_venv'; venv.create(d, with_pip=True); py=os.path.join(d, 'Scripts' if os.name=='nt' else 'bin', 'python'); subprocess.check_call([py,'-m','pip','install','git+https://github.com/Hananja/multiconverter'])"
```


# Run commandline app

```
python -m multiconverter <output_file>.zip <input_file1>.xml [<input_file2>.xml ...]
```

(or with `pipx` just `multiconverter ...`)

Without any parameter, a help screen is displayed:

```
$ ./bin/python -m multiconverter
Usage: python -m multiconverter <output_file>.zip <input_file1>.xml [<input_file2>.xml ...]
Process one or more AI generated XML files

Message to LLM:  ----------------------------------
Die Ausgabe soll ausschließlich im XML Format erfolgen und der folgenden XSD genügen: <?xml version='1.0' encoding='utf-8'?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/Hananja/multiconverter" elementFormDefault="qualified" targetNamespace="https://github.com/Hananja/multiconverter"><!--The comments are also used to inform AI LLM--><xs:element name="questions"><xs:complexType><xs:sequence><xs:choice minOccurs="0" maxOccurs="unbounded"><xs:element ref="multiple-choice-question"/><xs:element ref="fill-in-question"/></xs:choice></xs:sequence></xs:complexType></xs:element><xs:complexType name="option"><xs:simpleContent><xs:extension base="xs:string"><xs:attribute name="correct" use="required"><xs:simpleType><xs:restriction base="xs:string"><xs:enumeration value="true"/><xs:enumeration value="false"/></xs:restriction></xs:simpleType></xs:attribute></xs:extension></xs:simpleContent></xs:complexType><xs:element name="multiple-choice-question"><!--This question type presents a task in the <text> element. This can be one or more correct answers by selecting the correct ones from the <options>.--><xs:complexType><xs:sequence><xs:element name="text" type="xs:string"/><xs:element name="options"><xs:complexType><xs:sequence><xs:element name="option" maxOccurs="unbounded" type="option"/></xs:sequence></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element><xs:element name="fill-in-question"><!--This question type presents a task in the <text> element. The <fill-in-text> element contains a task text that may contain gaps. These are marked with <fill> and must be filled in during the test. The correct possible alternatives for the answer are contained in <alt> tags within a <fill> element.--><xs:complexType><xs:sequence><xs:element name="text" type="xs:string" minOccurs="0"/><xs:element name="fill-in-text"><xs:complexType mixed="true"><xs:sequence><xs:element name="fill" minOccurs="0" maxOccurs="unbounded"><xs:complexType><xs:sequence><xs:element name="alt" type="xs:string" maxOccurs="unbounded"/></xs:sequence></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>

Erstelle ein Beispieldokument mit je zwei Fragen pro Fragetyp
```

It is recommended to process the entire generated XML file first, because if the AI encounters any errors, an error
message will be issued prompting the LLM to correct the output:

```
$ ./bin/python -m multiconverter output.zip test_raw.xml 
Ungültig: test_raw.xml
The document test_raw.xml is not correct.

Message to LLM:  ----------------------------------
Überleg noch einmal: Das Dokument entspricht nicht der XSD. Der Parser liefert den Fehler "XML-Syntax-Fehler: StartTag: invalid element name, line 141, column 37 (test_raw.xml, line 141)".
```

If communication with the LLM has worked without errors after several iterations, the XML files can be edited and
adjusted (e.g., by deleting questions).

# Supported question types

# single and multiple choice
```xml
<multiple-choice-question xmlns="https://github.com/Hananja/multiconverter">
    <text>Was bedeutet WWW?</text>
    <options>
        <option correct="false">Willy will's wissen</option>
        <option correct="false">Wow, wie wichtig</option>
        <option correct="true">World Wide Web</option>
        <option correct="false">Wo? Wer? Wann?</option>
    </options>
</multiple-choice-question>
```

# fill in text
```xml
<fill-in-question xmlns="https://github.com/Hananja/multiconverter">
    <text>Für jedes Ereignis, das weder sicher noch unmöglich ist, gilt: </text>
    <fill-in-text><fill><alt>0</alt></fill> &lt; P(E) &lt; <fill><alt>1</alt></fill> für
        die Wahrscheinlichkeit des Ereignisses</fill-in-text>
</fill-in-question>
```

# map items
```xml
<map-question xmlns="https://github.com/Hananja/multiconverter">
    <text>Match the pairs.</text>
    <mappings>
        <mapping>
            <left>1 + 1</left>
            <right>2</right>
        </mapping>
        <mapping>
            <left>2 + 2</left>
            <right>4</right>
        </mapping>
        <mapping>
            <left>3 + 5</left>
            <right>8</right>
        </mapping>
    </mappings>
</map-question>
```