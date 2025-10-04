# src/multiconverter/gui/main_app.py
"""
Hauptapplikationsklasse für die multiconverter GUI - Wizard-Style Interface
"""
import flet as ft
import pyperclip
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import io
import os
from pathlib import Path

from ..converter5 import QuestionHandlers
from ..xml_validator import XMLValidator
from ..tools import get_local_tag
from .question_editor import QuestionEditorView
from .xml_display import XMLDisplayWidget


# Template-Verzeichnis relativ zum Skript finden
script_dir = os.path.dirname(os.path.abspath(__file__))
xsd_path = os.path.join(script_dir, "../xml/llmquestions.xsd")


class MultiConverterApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "MultiConverter GUI"
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.theme_mode = ft.ThemeMode.LIGHT

        # Datenstrukturen
        self.selected_question_types = set()
        self.custom_prompt = ""
        self.xml_output = ""
        self.validated_questions = []
        self.processed_questions = []
        self.question_handlers = QuestionHandlers()
        self.xml_validator = XMLValidator(xsd_path)

        # UI Komponenten
        self.current_step = 1
        self.setup_ui()

    def setup_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.page.add(self.build_wizard())

    def build_wizard(self):
        """Erstellt das Wizard-Interface"""
        return ft.Column([
            ft.AppBar(
                title=ft.Text("MultiConverter - Frage Generator"),
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE
            ),
            ft.Container(
                content=self.get_current_step_content(),
                expand=True,
                padding=20
            )
        ])

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

        checkboxes = []
        for key, label in question_types.items():
            checkbox = ft.Checkbox(
                label=label,
                value=key in self.selected_question_types,
                on_change=lambda e, qtype=key: self.toggle_question_type(qtype, e.control.value)
            )
            checkboxes.append(checkbox)

        prompt_field = ft.TextField(
            label="Benutzerdefinierter Prompt",
            multiline=True,
            min_lines=3,
            max_lines=8,
            value=self.custom_prompt,
            on_change=lambda e: setattr(self, 'custom_prompt', e.control.value)
        )

        output_field = ft.TextField(
            label="Generierter Prompt mit XSD",
            multiline=True,
            read_only=True,
            min_lines=10,
            max_lines=15,
            value=self.generate_prompt_with_xsd()
        )

        return ft.Column([
            ft.Text("Schritt 1: Fragetypen auswählen", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            ft.Text("Wählen Sie die gewünschten Fragetypen aus:"),
            ft.Column(checkboxes),
            ft.Divider(),
            prompt_field,
            ft.Divider(),
            output_field,
            ft.Row([
                ft.ElevatedButton(
                    "Copy to Clipboard",
                    on_click=lambda _: self.copy_to_clipboard(output_field.value),
                    icon=ft.Icons.COPY
                ),
                ft.ElevatedButton(
                    "Weiter",
                    on_click=lambda _: self.next_step(),
                    disabled=len(self.selected_question_types) == 0
                )
            ])
        ])

    def build_step2(self):
        """Schritt 2: XML Validierung"""
        xml_input = ft.TextField(
            label="XML Ausgabe des LLM",
            multiline=True,
            min_lines=15,
            max_lines=20,
            value=self.xml_output,
            on_change=lambda e: setattr(self, 'xml_output', e.control.value)
        )

        validation_result = ft.TextField(
            label="Validierungsergebnis",
            multiline=True,
            read_only=True,
            min_lines=5,
            max_lines=10
        )

        return ft.Column([
            ft.Text("Schritt 2: XML Validierung", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            xml_input,
            ft.Row([
                ft.ElevatedButton(
                    "Validieren",
                    on_click=lambda _: self.validate_xml(validation_result),
                    icon=ft.Icons.CHECK_CIRCLE
                ),
                ft.ElevatedButton(
                    "Copy to Clipboard",
                    on_click=lambda _: self.copy_to_clipboard(validation_result.value),
                    icon=ft.Icons.COPY,
                    disabled=not validation_result.value
                )
            ]),
            validation_result,
            ft.Row([
                ft.ElevatedButton(
                    "Zurück",
                    on_click=lambda _: self.previous_step()
                ),
                ft.ElevatedButton(
                    "Weiter",
                    on_click=lambda _: self.next_step(),
                    disabled=not self.validated_questions
                )
            ])
        ])

    def build_step3(self):
        """Schritt 3: Fragen bearbeiten"""
        if not self.validated_questions:
            return ft.Text("Keine validierten Fragen verfügbar")

        return QuestionEditorView(
            self.page,
            self.validated_questions,
            self.on_question_processed,
            self.on_all_questions_processed
        ).build()

    def build_step4(self):
        """Schritt 4: Export und weitere Optionen"""
        return ft.Column([
            ft.Text("Schritt 4: Export", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            ft.Text(f"Verarbeitete Fragen: {len(self.processed_questions)}"),
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
                    on_click=lambda _: self.page.window_close(),
                    icon=ft.Icons.EXIT_TO_APP
                )
            ])
        ])

    def toggle_question_type(self, question_type: str, selected: bool):
        """Verwaltet die Auswahl der Fragetypen"""
        if selected:
            self.selected_question_types.add(question_type)
        else:
            self.selected_question_types.discard(question_type)
        self.update_step1()

    def generate_prompt_with_xsd(self) -> str:
        """Generiert den Prompt mit XSD"""
        if not self.selected_question_types:
            return ""

        xsd_path = Path(__file__).parent.parent / "xml" / "llmquestions.xsd"
        try:
            with open(xsd_path, 'r', encoding='utf-8') as f:
                xsd_content = f.read()
        except FileNotFoundError:
            xsd_content = "XSD Datei nicht gefunden"

        selected_types = ", ".join(self.selected_question_types)
        prompt = f"Erstelle Fragen der Typen: {selected_types}\n\n"
        if self.custom_prompt:
            prompt += f"Zusätzlicher Prompt:\n{self.custom_prompt}\n\n"
        prompt += f"XSD Schema:\n{xsd_content}"

        return prompt

    def copy_to_clipboard(self, text: str):
        """Kopiert Text in die Zwischenablage"""
        try:
            pyperclip.copy(text)
            self.show_snackbar("Text wurde in die Zwischenablage kopiert")
        except Exception as e:
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
                result_field.value = f"Validierungsfehler:\n{validation_result.error_message}"
                self.validated_questions = []
        except Exception as e:
            result_field.value = f"Fehler bei der Validierung: {str(e)}"
            self.validated_questions = []

        self.page.update()

    def extract_questions_from_xml(self):
        """Extrahiert Fragen aus dem validierten XML"""
        try:
            root = ET.fromstring(self.xml_output)
            self.validated_questions = list(root)
        except Exception as e:
            self.show_snackbar(f"Fehler beim Extrahieren der Fragen: {str(e)}")
            self.validated_questions = []

    def on_question_processed(self, question, action: str):
        """Callback für verarbeitete Fragen"""
        if action == "save":
            self.processed_questions.append(question)
        # Bei "discard" wird die Frage nicht hinzugefügt

    def on_all_questions_processed(self):
        """Callback wenn alle Fragen verarbeitet wurden"""
        self.next_step()

    def save_xml_document(self):
        """Speichert XML Dokument"""
        # Hier würde normalerweise ein Dateidialog geöffnet
        self.show_snackbar("XML Dokument Speicherung nicht implementiert")

    def save_zip_archive(self):
        """Speichert ZIP Archiv"""
        try:
            zip_data = self.question_handlers.get_zip()
            # Hier würde normalerweise ein Dateidialog geöffnet
            self.show_snackbar("ZIP Archiv Speicherung nicht implementiert")
        except Exception as e:
            self.show_snackbar(f"Fehler beim Erstellen des ZIP Archivs: {str(e)}")

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

    def update_step1(self):
        """Aktualisiert Schritt 1"""
        if self.current_step == 1:
            self.update_ui()

    def update_ui(self):
        """Aktualisiert die gesamte UI"""
        self.page.clean()
        self.page.add(self.build_wizard())
        self.page.update()

    def show_snackbar(self, message: str):
        """Zeigt eine Snackbar-Nachricht"""
        self.page.show_snack_bar(ft.SnackBar(content=ft.Text(message)))

    def run(self):
        """Startet die Applikation"""
        pass