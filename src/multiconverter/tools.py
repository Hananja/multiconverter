from jinja2 import Environment, FileSystemLoader, pass_context
import os
from lxml import etree
import re


# https://www.perplexity.ai/search/wie-kann-ich-bei-jinja2-eine-d-HV5LDp.hS0OXXn2t3BR0qw
@pass_context
def include_min_xsd_file(context, name):
    # Pfad relativ zum Template-Verzeichnis
    template_dir = context.environment.loader.searchpath[0]
    file_path = os.path.join(template_dir, name)

    with open(file_path, 'r', encoding='utf-8') as f:
        return minimize_xsd_advanced(f.read())


# https://www.perplexity.ai/search/erstelle-mir-ein-python-modul-OLgHn3VYSJO1CeB2QIof8g
def minimize_xsd_advanced(xml_string: str) -> str:
    """
    Minimiert eine XSD-XML-Datei mit erweiterten Optionen:
    - Entfernt unnötige Attribute (Beispiel: spezifische unnötige Attribute)
    - Verkürzt Namespace-Deklarationen (Präfix auf 1 Zeichen reduzieren)
    - Vermeidet unnötige Zeilenumbrüche und mehrfache Leerzeichen
    - Gibt leere Elemente kompakt als Self-Closing Tags aus
    - Entfernt reine Whitespace-Texte im Baum
    - Erhält XML-Kommentare

    :param xml_string: XML-Input als String der XSD-Datei.
    :return: Minimierter und optimierter XML-String mit erhaltenen Kommentaren.
    """
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_string.encode('utf-8'), parser=parser)

    # Entfernen unnötiger Attribute (Beispielattribute)
    def remove_unnecessary_attributes(element):
        attrs_to_remove = ["unused", "extra"]  # Beispielattribute, anpassen nach Bedarf
        for attr in attrs_to_remove:
            if attr in element.attrib:
                del element.attrib[attr]
        for child in element:
            remove_unnecessary_attributes(child)

    remove_unnecessary_attributes(root)

    # Namespace-Deklarationen: Präfixe auf 1 Zeichen verkürzen (z.B. n1, n2 ...)
    nsmap = root.nsmap
    prefix_map = {}
    new_prefix_char = ord('a')
    for prefix in nsmap:
        if prefix is not None:
            prefix_map[prefix] = f"n{chr(new_prefix_char)}"
            new_prefix_char += 1

    def rewrite_namespaces(elem):
        # Namespace-Deklarationen im Attribut-Baum umschreiben
        for key, value in list(elem.attrib.items()):
            if key.startswith("xmlns:"):
                original_prefix = key[6:]
                if original_prefix in prefix_map:
                    new_key = f"xmlns:{prefix_map[original_prefix]}"
                    elem.attrib[new_key] = value
                    del elem.attrib[key]
        for child in elem:
            rewrite_namespaces(child)

    rewrite_namespaces(root)

    # Mehrfache Leerzeichen in Text und Tail auf eins reduzieren, und Whitespace entfernen
    def reduce_multiple_spaces(text):
        if text is None:
            return None
        return re.sub(r" +", " ", text.strip())

    def clean_text(elem):
        if elem.text is not None:
            t = reduce_multiple_spaces(elem.text)
            elem.text = t if t else None
        if elem.tail is not None:
            tail = reduce_multiple_spaces(elem.tail)
            elem.tail = tail if tail else None
        for child in elem:
            clean_text(child)

    clean_text(root)

    # lxml gibt leere Elemente bereits als Self-Closing Tags aus, keine zusätzliche Behandlung nötig

    # Ausgabe als kompakter XML-String ohne zusätzliche Einrückung oder Zeilenumbrüche
    minimized_xml_bytes = etree.tostring(root, encoding='utf-8', xml_declaration=True, pretty_print=False)
    return minimized_xml_bytes.decode('utf-8')


if __name__ == "__main__":
    # XSD-Datei einlesen (Pfad anpassen)
    input_path = "example.xsd"
    with open(input_path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    minimized_xsd = minimize_xsd_advanced(xml_content)

    # Minimierte XSD ausgeben oder in Datei speichern
    print(minimized_xsd)
    # Optional: Ausgabe in Datei speichern
    # with open("example_minimized.xsd", "w", encoding="utf-8") as f:
    #     f.write(minimized_xsd)


def get_local_tag(element):
    return etree.QName(element.tag).localname

def escape_content_data(text):
    """
        Replaces < and > if they are standing alone and are not part of a tag.
    """
    if text is None:
        return text

    result = []
    in_tag = False
    for i, char in enumerate(text):
        if char == '<':
            # Check if it's likely starting a tag (followed by valid tag chars)
            if i + 1 < len(text) and (text[i + 1].isalnum() or text[i + 1] in '!?/'):
                in_tag = True
                result.append(char)
            else:
                result.append('&lt;')
        elif char == '>':
            if in_tag:
                in_tag = False
                result.append(char)
            else:
                result.append('&gt;')
        else:
            result.append(char)

    return ''.join(result)
