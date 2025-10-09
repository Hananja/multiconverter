# src/multiconverter/gui/main_app.py
"""
Hauptapplikationsklasse für die multiconverter GUI - Wizard-Style Interface
"""
import flet as ft
import pyperclip
import xml.etree.ElementTree as ET
import os
from pathlib import Path
from lxml import etree

from ..tools import minimize_xsd_advanced
from ..converter5 import QuestionHandlers, jinja_env
from ..xml_validator import XMLValidator
from .question_editor import QuestionEditorView

DEBUG = True
def visible_debug_only(control: ft.Control) -> ft.Control:
    """Hilfsfunktion um Debug-Only Controls zu erstellen"""
    control.visible = DEBUG
    return control


# Template-Verzeichnis relativ zum Skript finden
script_dir = os.path.dirname(os.path.abspath(__file__))
xsd_path = os.path.join(script_dir, "../xml/llmquestions.xsd")


class MultiConverterApp:
    def __init__(self, page: ft.Page):
        self.next_button_step2 = None
        self.page = page
        self.page.title = "MultiConverter"
        self.page.window_width = 1200
        self.page.window_height = 900
        self.page.theme_mode = ft.ThemeMode.LIGHT

        # Datenstrukturen
        self.selected_question_types = set(QuestionHandlers.get_question_types())
        self.custom_prompt = ""
        self.xml_output = ""
        self.xml_output_field = None
        self.validation_result_field = None
        self.validated_questions = []
        self.processed_questions = []
        self.question_handlers = None
        self.xml_validator = XMLValidator(xsd_path)

        # UI Komponenten
        self.current_step = 1
        self.save_file_picker = ft.FilePicker(
            on_result=self.save_file_result
        )
        self.setup_ui()

    def setup_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.page.add(self.build_wizard())

    def build_wizard(self):
        """Erstellt das Wizard-Interface"""
        return ft.Column([
            ft.Container(
                content=ft.Text(
                    "itslearning Tests mit LLM erstellen",
                    style=ft.TextThemeStyle.HEADLINE_SMALL,
                    color=ft.Colors.WHITE
                ),
                bgcolor=ft.Colors.BLUE,
                padding=20,
                width=float('inf')
            ),
            ft.Container(
                content=ft.Column([
                    self.get_current_step_content()
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
                ),
                expand=True,
                padding=20
            )
        ],
        expand=True
        )

    def get_current_step_content(self):
        """Gibt den Inhalt für den aktuellen Schritt zurück"""
        if self.current_step == 1:
            return self.build_step1()
        elif self.current_step == 2:
            return self.build_step2()
        elif self.current_step == 3:
            return self.build_step3()
        elif self.current_step == 4:
            return self.build_step4()
        else:
            return ft.Text("Unbekannter Schritt")

    def build_step1(self):
        """Schritt 1: Fragetypen auswählen und Prompt eingeben"""
        # Verfügbare Fragetypen aus question_handlers_map
        question_types = {
            "multiple-choice-question": "Multiple Choice Fragen",
            "fill-in-question": "Lückentext Fragen",
            "map-question": "Zuordnungsfragen"
        }
        assert all(qt in QuestionHandlers.get_question_types() for qt in question_types.keys()),\
            "Fragetypen stimmen nicht mit QuestionHandlers überein"

        checkboxes = []
        for key, label in question_types.items():
            checkbox = ft.Checkbox(
                label=label,
                value=key in self.selected_question_types,
                on_change=lambda e, qtype=key: self.toggle_question_type(qtype, e.control.value),
            )
            checkboxes.append(checkbox)

        prompt_field = ft.TextField(
            label="Prompt zu den Details der Fragen",
            multiline=True,
            min_lines=4,
            max_lines=8,
            value=self.custom_prompt,
            on_change=lambda e: self.set_custom_prompt(e.control.value)
        )

        self.output_field = ft.TextField(
            label="Generierter Prompt mit XSD",
            multiline=True,
            read_only=True,
            min_lines=4,
            max_lines=6,
            value=self.generate_prompt_with_xsd()
        )

        col_controls = [
            ft.Text("Schritt 1: Fragetypen auswählen und Prompt eingeben"),
            ft.Row(checkboxes),
            prompt_field,
            visible_debug_only(self.output_field),
            ft.Row([
                ft.ElevatedButton(
                    "Kopieren (Zwischenablage)",
                    on_click=lambda _: self.copy_to_clipboard(self.output_field.value),
                    icon=ft.Icons.COPY
                ),
                ft.ElevatedButton(
                    "Weiter",
                    on_click=lambda _: self.next_step(),
                    disabled=len(self.selected_question_types) == 0
                )
            ])]
        return ft.Column(col_controls,
                         scroll=ft.ScrollMode.ALWAYS,
                         expand=True )

    def build_step2(self):
        """Schritt 2: XML Validierung"""
        self.xml_output_field = ft.TextField(
            label="XML Ausgabe des LLM hier einfügen",
            multiline=True,
            min_lines=3,
            max_lines=8,
            value=self.xml_output,
            on_change = lambda _: self.update_new_xml_output()
        )

        self.validation_result_field = ft.TextField(
            label="Validierungsergebnis",
            multiline=True,
            read_only=True,
            min_lines=2,
            max_lines=5,
        )

        # Button-Referenz für spätere Updates speichern
        self.next_button_step2 = ft.ElevatedButton(
            "Weiter",
            on_click=lambda _: self.next_step(),
            disabled=not self.validated_questions
        )

        return ft.Column([
            ft.Text("Schritt 2: XML Validierung"),
            self.xml_output_field,
            ft.Row([
                ft.ElevatedButton(
                    "Einfügen (Zwischenablage)",
                    on_click=lambda _: self.paste_from_clipboard(),
                    icon=ft.Icons.PASTE
                ),
                ft.ElevatedButton(
                    "Validieren",
                    on_click=lambda _: self.validate_xml_and_update_button(self.validation_result_field),
                    icon=ft.Icons.CHECK_CIRCLE
                ),
            ]),
            self.validation_result_field,
            ft.Row([
                ft.ElevatedButton(
                    "Kopieren (Zwischenablage)",
                    on_click=lambda _: self.copy_to_clipboard(self.validation_result_field.value),
                    icon=ft.Icons.COPY,
                ),
                ft.ElevatedButton(
                    "Zurück",
                    on_click=lambda _: self.previous_step()
                ),
                self.next_button_step2
            ])
        ])

    def build_step3(self):
        """Schritt 3: Fragen bearbeiten"""
        if not self.validated_questions:
            return ft.Column([
                ft.Text("Keine validierten Fragen verfügbar"),
                ft.ElevatedButton(
                    "Zurück",
                    on_click=lambda _: self.previous_step()
                )
            ])

        return QuestionEditorView(
            self.page,
            self.validated_questions,
            self.on_question_processed,
            self.on_all_questions_processed
        ).build()

    def build_step4(self):
        """Schritt 4: Export und weitere Optionen"""
        return ft.Column([
            ft.Text("Schritt 4: Export"),
            ft.Text(f"gesicherte Fragen: {len(self.processed_questions)}"),
            ft.Row([
                ft.ElevatedButton(
                    "XML Dokument speichern",
                    on_click=lambda _: self.save_xml_document(),
                    icon=ft.Icons.SAVE
                ),
                ft.ElevatedButton(
                    "ZIP Archiv speichern",
                    on_click=lambda _: self.save_zip_archive(),
                    icon=ft.Icons.ARCHIVE
                )
            ]),
            ft.Divider(),
            ft.Row([
                ft.ElevatedButton(
                    "Weitere Fragen hinzufügen",
                    on_click=lambda _: self.restart_wizard(),
                    icon=ft.Icons.ADD
                ),
                ft.ElevatedButton(
                    "Beenden",
                    on_click=lambda _: self.handle_quit(),
                    icon=ft.Icons.EXIT_TO_APP
                )
            ])
        ])

    def handle_quit(self):
        def button_handler(do_quit: bool):
            alert_dialog.open = False
            self.page.update()
            if do_quit:
                self.page.window.close()

        alert_dialog = ft.AlertDialog(
            title=ft.Text("Beenden"),
            content=ft.Text("Möchten Sie wirklich beenden?"),
            actions=[
                ft.TextButton("Ja", on_click=lambda _: button_handler(True)),
                ft.TextButton("Nein", on_click=lambda _: button_handler(False)),
            ],
            modal=True)

        self.page.add(alert_dialog)  # TODO: remove on close?
        alert_dialog.open = True
        self.page.update()

    def toggle_question_type(self, question_type: str, selected: bool):
        """Verwaltet die Auswahl der Fragetypen"""
        if selected:
            self.selected_question_types.add(question_type)
        else:
            self.selected_question_types.discard(question_type)
        self.update_prompt_with_xsd()

    def update_prompt_with_xsd(self):
        """Aktualisiert das Prompt-Feld mit der generierten XSD"""
        if self.current_step == 1:
            if self.output_field:
                self.output_field.value = self.generate_prompt_with_xsd()
                self.page.update()

    def update_new_xml_output(self):
        self.xml_output = self.xml_output_field.value
        self.validation_result_field.value = ""
        self.next_button_step2.disabled = True
        self.page.update()

    def generate_prompt_with_xsd(self) -> str:
        """Generiert den Prompt mit XSD und extrahiert nur die relevanten Teile basierend auf den ausgewählten Fragetypen"""
        if not self.selected_question_types:
            return ""

        try:
            # Parse XSD mit lxml
            parser = etree.XMLParser(remove_comments=False)
            tree = etree.parse(str(xsd_path), parser)
            root = tree.getroot()

            # Namespace für XSD
            ns = {"xs": "http://www.w3.org/2001/XMLSchema"}

            # remove all elements except those in selected_question_types
            for question_type in QuestionHandlers.get_question_types():
                for xpath in [ f".//xs:element[@ref='{question_type}']", f".//xs:element[@name='{question_type}']" ]:
                    question_element = root.xpath(xpath, namespaces=ns)
                    assert len(question_element) == 1
                    if question_type not in self.selected_question_types:
                        parent = question_element[0].getparent()
                        parent.remove(question_element[0])

            xsd_content = etree.tostring(root, pretty_print=True).decode()

            selected_types = ", ".join(self.selected_question_types)
            prompt = f"Erstelle Fragen der Typen: {selected_types}\n\n"
            if self.custom_prompt:
                prompt += f"Zusätzlicher Prompt:\n{self.custom_prompt}\n\n"
            prompt += f"Relevante XSD Schema-Definitionen:\n{minimize_xsd_advanced(xsd_content)}"

            return prompt + 2*"\n"

        except OSError as e:
            xsd_content = f"Fehler beim Verarbeiten der XSD: {str(e)}"


    def copy_to_clipboard(self, text: str):
        """Kopiert Text in die Zwischenablage"""
        try:
            pyperclip.copy(text)
            self.show_snackbar("Text wurde in die Zwischenablage kopiert")
        except OSError as e:
            self.show_snackbar(f"Fehler beim Kopieren: {str(e)}")

    def paste_from_clipboard(self):
        """Kopiert Text aus der Zwischenablage"""
        try:
            self.xml_output_field.value = pyperclip.paste().strip()
            self.update_new_xml_output()
            if len(self.xml_output_field.value.strip()) > 0:
                self.show_snackbar("Text wurde aus der Zwischenablage eingefügt")
            else:
                self.show_snackbar("Zwischenablage ist leer")
        except OSError as e:
            self.show_snackbar(f"Fehler beim Kopieren: {str(e)}")

    def validate_xml(self, result_field: ft.TextField):
        """Validiert das eingegebene XML"""
        if not self.xml_output.strip():
            result_field.value = "Bitte geben Sie XML-Code ein"
            self.page.update()
            return

        try:
            validation_result = self.xml_validator.validate_xml_string(self.xml_output)
            if validation_result.is_valid:
                result_field.value = "XML ist gültig!"
                # Extrahiere Fragen aus dem XML
                self.extract_questions_from_xml()
            else:
                error_messages = []
                for error_type, error_message in validation_result.errors:
                    error_messages.append(error_message)
                result_field.value = f"Validierungsfehler:\n" + "\n".join(error_messages)
                self.validated_questions = []
        except OSError as e:
            result_field.value = f"Fehler bei der Validierung: {str(e)}"
            self.validated_questions = []

        self.page.update()

    def extract_questions_from_xml(self):
        """Extrahiert Fragen aus dem validierten XML"""
        try:
            root = ET.fromstring(self.xml_output)
            self.validated_questions = list(root)
        except ET.ParseError as e:
            self.show_snackbar(f"Fehler beim Extrahieren der Fragen: {str(e)}")
            self.validated_questions = []

    def on_question_processed(self, question, action: str):
        """Callback für verarbeitete Fragen"""
        if action == "save":
            self.processed_questions.append(question)
        # Bei "discard" wird die Frage nicht hinzugefügt

    def on_all_questions_processed(self):
        """Callback wenn alle Fragen verarbeitet wurden"""
        self.question_handlers = QuestionHandlers()
        for question in self.processed_questions:
            self.question_handlers.handle_question(question)
        self.next_step()

    def save_xml_document(self):
        """Speichert XML Dokument"""
        try:
            self.xml_data = jinja_env.get_template("questions.xml.jinja").render(
                questions=map(lambda x:ET.tostring(x, encoding='utf-8').decode('utf-8'),
                              self.processed_questions))
            # Dateidialog öffnen
            if not self.save_file_picker in self.page.overlay:
                self.page.overlay.append(self.save_file_picker)
                self.page.update()
            self.save_file_picker.save_file(
                dialog_title="XML speichern",
                file_name="questions.xml",
                allowed_extensions=["xml"],
                initial_directory=Path.home().as_posix(),
                file_type=ft.FilePickerFileType.CUSTOM
            )
        except OSError as e:
            self.show_snackbar(f"Fehler beim Erstellen der XML Datei: {str(e)}")


    def save_zip_archive(self):
        """Speichert ZIP Archiv"""
        try:
            # see save_file_result()
            self.zip_data = self.question_handlers.get_zip()
            # Dateidialog öffnen
            if not self.save_file_picker in self.page.overlay:
                self.page.overlay.append(self.save_file_picker)
                self.page.update()
            self.save_file_picker.save_file(
                dialog_title="itslearning QTI ZIP Archiv speichern",
                file_name="questions.zip",
                allowed_extensions=["zip"],
                initial_directory=Path.home().as_posix(),
                file_type=ft.FilePickerFileType.CUSTOM
            )
        except OSError as e:
            self.show_snackbar(f"Fehler beim Erstellen des ZIP Archivs: {str(e)}")

    def save_file_result(self, e: ft.FilePickerResultEvent):
        """Verarbeitet das Ergebnis der Dateispeicherung"""
        if e.path:
            try:
                with open(e.path, 'wb') as f:
                    if "zip" in e.control.allowed_extensions:
                        f.write(self.zip_data)
                    elif "xml" in e.control.allowed_extensions:
                        f.write(self.xml_data.encode("utf-8"))
                    else:
                        self.show_snackbar("Unbekannter Dateityp. Nur .xml und .zip sind erlaubt.")
                        return
                self.show_snackbar(f"Datei erfolgreich gespeichert: {e.path}")
            except OSError as err:
                self.show_snackbar(f"Fehler beim Speichern: {str(err)}")

    def restart_wizard(self):
        """Startet einen neuen Wizard-Durchlauf"""
        self.current_step = 1
        self.custom_prompt = ""
        self.xml_output = ""
        self.validated_questions = []
        self.update_ui()

    def next_step(self):
        """Geht zum nächsten Schritt"""
        self.current_step += 1
        self.update_ui()

    def previous_step(self):
        """Geht zum vorherigen Schritt"""
        self.current_step -= 1
        self.update_ui()

    def update_ui(self):
        """Aktualisiert die gesamte UI"""
        self.page.clean()
        self.page.add(self.build_wizard())
        self.page.update()

    def show_snackbar(self, message: str):
        """Zeigt eine Snackbar-Nachricht"""
        snackbar = ft.SnackBar(
            content=ft.Text(message),
            open=True
        )
        self.page.snack_bar = snackbar
        self.page.overlay.append(snackbar)
        self.page.update()



    def run(self):
        """Startet die Applikation"""
        pass

    def validate_xml_and_update_button(self, result_field: ft.TextField):
        """Validiert das eingegebene XML und aktualisiert den Button"""
        if not self.xml_output.strip():
            result_field.value = "Bitte geben Sie XML-Code ein"
            self.page.update()
            return

        try:
            validation_result = self.xml_validator.validate_xml_string(self.xml_output)
            if validation_result.is_valid:
                result_field.value = "XML ist gültig!"
                # Extrahiere Fragen aus dem XML
                self.extract_questions_from_xml()
                # Button aktivieren
                if hasattr(self, 'next_button_step2'):
                    self.next_button_step2.disabled = False
            else:
                error_messages = []
                for error_type, error_message in validation_result.errors:
                    error_messages.append(error_message)
                result_field.value = ("Überleg noch einmal. Der XML Parser hat folgenden Fehler ausgegeben:\n"
                                      + "\n".join(error_messages))
                self.validated_questions = []
                # Button deaktivieren
                if hasattr(self, 'next_button_step2'):
                    self.next_button_step2.disabled = True
        except OSError as e:
            result_field.value = f"Fehler bei der Validierung: {str(e)}"
            self.validated_questions = []
            # Button deaktivieren
            if hasattr(self, 'next_button_step2'):
                self.next_button_step2.disabled = True

        self.page.update()

    def set_custom_prompt(self, value : str):
        self.custom_prompt = value
        self.update_prompt_with_xsd()