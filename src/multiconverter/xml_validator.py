# https://www.perplexity.ai/search/erstelle-ein-python-skript-das-PjbssWsRRIef5.vs8CI7uA
#
import xml.etree.ElementTree as ET
from enum import Enum

from lxml import etree
import os
from typing import List, Dict, Optional
from dataclasses import dataclass

class Error(Enum):
    FILE_NOT_FOUND = 1
    ENCODING_ERROR = 2
    XSD_ERROR = 3
    EXTENSION_ERROR = 4
    XML_ERROR = 5
    PERMISSION_DENIED = 6
    UNKNOWN_ERROR = 100

@dataclass
class ValidationResult:
    filename: str
    is_valid: bool
    errors: List[str]
    xml_content: Optional[ET.Element] = None

class XMLValidator:
    def __init__(self, xsd_path: str):
        self.xsd_path = xsd_path
        self.schema = None
        self._load_schema()

    def _load_schema(self):
        try:
            if not os.path.exists(self.xsd_path):
                raise FileNotFoundError(f"XSD-Schema-Datei nicht gefunden: {self.xsd_path}")
            with open(self.xsd_path, 'r', encoding='utf-8') as schema_file:
                schema_doc = etree.parse(schema_file)
                self.schema = etree.XMLSchema(schema_doc)
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Fehler beim Parsen der XSD-Schema-Datei: {e}")
        except Exception as e:
            raise RuntimeError(f"Unerwarteter Fehler beim Laden des Schemas: {e}")

    def validate_file(self, xml_file_path: str) -> ValidationResult:
        errors = []
        xml_content = None
        try:
            if not os.path.exists(xml_file_path):
                errors.append((Error.FILE_NOT_FOUND,f"Datei nicht gefunden: {xml_file_path}"))
                return ValidationResult(xml_file_path, False, errors)
            if not xml_file_path.lower().endswith('.xml'):
                errors.append((Error.EXTENSION_ERROR, f"Datei hat keine .xml-Erweiterung: {xml_file_path}"))
                return ValidationResult(xml_file_path, False, errors)
            try:
                with open(xml_file_path, 'r', encoding='utf-8') as xml_file:
                    xml_doc = etree.parse(xml_file)
            except UnicodeDecodeError:
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        with open(xml_file_path, 'r', encoding=encoding) as xml_file:
                            xml_doc = etree.parse(xml_file)
                        break
                    except (UnicodeDecodeError, etree.XMLSyntaxError):
                        continue
                else:
                    errors.append((Error.ENCODING_ERROR, "Encoding-Fehler: Datei konnte nicht gelesen werden"))
                    return ValidationResult(xml_file_path, False, errors)

            if self.schema is None:
                errors.append((Error.UNKNOWN_ERROR, "Kein XSD-Schema geladen"))
                return ValidationResult(xml_file_path, False, errors)

            is_valid = self.schema.validate(xml_doc)
            if not is_valid:
                for error in self.schema.error_log:
                    errors.append((Error.XSD_ERROR, f"Zeile {error.line}: {error.message}"))
            else:
                xml_content = ET.fromstring(etree.tostring(xml_doc, encoding='unicode'))
            return ValidationResult(xml_file_path, is_valid, errors, xml_content)
        except etree.XMLSyntaxError as e:
            errors.append((Error.XML_ERROR, f"XML-Syntax-Fehler: {e}"))
            return ValidationResult(xml_file_path, False, errors)
        except PermissionError:
            errors.append((Error.PERMISSION_DENIED, f"Keine Berechtigung zum Lesen der Datei: {xml_file_path}"))
            return ValidationResult(xml_file_path, False, errors)
        except Exception as e:
            errors.append((Error.UNKNOWN_ERROR, f"Unerwarteter Fehler: {e}"))
            return ValidationResult(xml_file_path, False, errors)

    def validate_files(self, file_list: List[str]) -> Dict[str, ValidationResult]:
        results = {}
        for file_path in file_list:
            result = self.validate_file(file_path)
            results[file_path] = result
        return results

    def get_valid_documents(self, results: Dict[str, ValidationResult]) -> Dict[str, ET.Element]:
        return {fn: res.xml_content for fn, res in results.items() if res.is_valid and res.xml_content is not None}

    def get_invalid_documents(self, results: Dict[str, ValidationResult]) -> Dict[str, ET.Element]:
        return {fn: res.xml_content for fn, res in results.items() if not res.is_valid}

    def validate_xml_string(self, xml_string: str) -> ValidationResult:
        """Validiert einen XML-String"""
        errors = []
        xml_content = None
        
        try:
            if not xml_string.strip():
                errors.append((Error.XML_ERROR, "XML-String ist leer"))
                return ValidationResult("xml_string", False, errors)

        # Parse XML string with lxml
            try:
                xml_doc = etree.fromstring(xml_string.encode('utf-8'))
            except etree.XMLSyntaxError as e:
                errors.append((Error.XML_ERROR, f"XML-Syntax-Fehler: {e}"))
                return ValidationResult("xml_string", False, errors)

            if self.schema is None:
                errors.append((Error.UNKNOWN_ERROR, "Kein XSD-Schema geladen"))
                return ValidationResult("xml_string", False, errors)

        # Validate against schema
            is_valid = self.schema.validate(xml_doc)
            if not is_valid:
                for error in self.schema.error_log:
                    errors.append((Error.XSD_ERROR, f"Zeile {error.line}: {error.message}"))
            else:
                # Convert to ElementTree format
                xml_content = ET.fromstring(etree.tostring(xml_doc, encoding='unicode'))
            
            return ValidationResult("xml_string", is_valid, errors, xml_content)
        
        except Exception as e:
            errors.append((Error.UNKNOWN_ERROR, f"Unerwarteter Fehler: {e}"))
            return ValidationResult("xml_string", False, errors)


# Beispielaufruf:
def main():
    file_list = ["tests/demo.xml"]
    print(os.getcwd())
    xsd_path = "src/multiconverter/xml/llmquestions.xsd"
    validator = XMLValidator(xsd_path)
    validation_results = validator.validate_files(file_list)
    for filename, document in validation_results.items():
        if document.is_valid:
            print(f"Gültig: {filename} Root-Tag: {document.xml_content.tag}")
        else:
            print(f"Ungültig: {filename}")
            for error in document.errors:
                print(f"- {error}")


if __name__ == "__main__.py":
    main()