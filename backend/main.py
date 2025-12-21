# main.py - Haarfarben App mit Datenbankintegration
import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.clock import Clock
import threading
import os
import sys
import sqlite3
from tkinter import Tk, filedialog
from typing import Tuple

# Optionales Bildanalyse-Modul
try:
    from image_analysis import analyze_hair_image_simple

    HAS_IMAGE_ANALYSIS = True
except ImportError:
    HAS_IMAGE_ANALYSIS = False
    print("Hinweis: image_analysis.py nicht gefunden, Demo-Modus aktiv")

Window.size = (500, 700)
DB_FILENAME = "haircolor_practice.db"

# ------------------ AGB / Datenschutzerklärung ------------------

def find_agb_files():
    """Findet AGB und Datenschutz-Dateien in verschiedenen Verzeichnissen"""
    print("Suche nach AGB-Dateien...")
    
    # Mögliche Basisverzeichnisse (priorisiert)
    base_dirs = [
        os.getcwd(),  # 1. Aktuelles Arbeitsverzeichnis
        os.path.dirname(os.path.abspath(sys.argv[0])),  # 2. Wo das Skript gestartet wurde
        os.path.dirname(os.path.abspath(__file__)),  # 3. Wo main.py liegt
        os.path.join(os.path.expanduser("~"), "Desktop"),  # 4. Desktop
        "C:\\",  # 5. C: Laufwerk root (korrigiert: doppelter Backslash)
    ]
    
    # Spezifische Pfade für dein System
    custom_paths = [
        r"C:\Fertige Version für Playstore",
        r"C:\Fertige Version für Playstore\agb.txt",
        r"C:\Fertige Version für Playstore\datenschutz.txt",
    ]
    
    # Kombiniere alle Suchpfade
    search_paths = base_dirs + custom_paths
    
    agb_found = None
    datenschutz_found = None
    
    for path in search_paths:
        # Wenn es ein Dateipfad ist (nicht Verzeichnis)
        if os.path.isfile(path):
            if "agb" in path.lower() and path.lower().endswith(".txt"):
                agb_found = path
                print(f"  AGB-Datei gefunden: {agb_found}")
            elif "datenschutz" in path.lower() and path.lower().endswith(".txt"):
                datenschutz_found = path
                print(f"  Datenschutz-Datei gefunden: {datenschutz_found}")
        # Wenn es ein Verzeichnis ist
        elif os.path.isdir(path):
            agb_candidate = os.path.join(path, "agb.txt")
            datenschutz_candidate = os.path.join(path, "datenschutz.txt")
            
            if os.path.exists(agb_candidate):
                agb_found = agb_candidate
                print(f"  AGB-Datei gefunden: {agb_found}")
            
            if os.path.exists(datenschutz_candidate):
                datenschutz_found = datenschutz_candidate
                print(f"  Datenschutz-Datei gefunden: {datenschutz_found}")
    
    # Debug: Aktuelle Umgebung anzeigen
    print(f"  Aktuelles Arbeitsverzeichnis: {os.getcwd()}")
    print(f"  Skript-Verzeichnis: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"  Start-Verzeichnis: {os.path.dirname(os.path.abspath(sys.argv[0]))}")
    
    # Dateien im aktuellen Verzeichnis auflisten
    try:
        current_files = os.listdir(os.getcwd())
        print(f"  Dateien im aktuellen Verzeichnis: {current_files}")
    except:
        print("  Konnte aktuelle Dateien nicht auflisten")
    
    return agb_found, datenschutz_found

def create_default_agb():
    """Erstellt Standard-AGB-Dateien, falls keine gefunden wurden"""
    print("Erstelle Standard-AGB-Dateien...")
    
    # Standard AGB Inhalt
    agb_content = """Allgemeine Geschäftsbedingungen (AGB)
für die Haarfarben-Analyse-App

Stand: 2024

§1 Geltungsbereich
Diese Allgemeinen Geschäftsbedingungen gelten für die Nutzung der Haarfarben-Analyse-App.

§2 Leistungsbeschreibung
Die App bietet Rezeptberechnungen für Haarfärbungen basierend auf manuellen Eingaben oder Bildanalysen.

§3 Haftungsausschluss
Die App dient nur zu Übungszwecken. Für etwaige Schäden durch falsche Farbberechnungen wird keine Haftung übernommen.

§4 Datenschutz
Personenbezogene Daten werden nur lokal auf Ihrem Gerät gespeichert.

§5 Urheberrecht
Die Software und alle Inhalte sind urheberrechtlich geschützt.

§6 Schlussbestimmungen
Es gilt deutsches Recht. Gerichtsstand ist der Sitz des Anbieters."""
    
    # Standard Datenschutz Inhalt
    datenschutz_content = """Datenschutzerklärung
für die Haarfarben-Analyse-App

1. Verantwortlicher
Der Verantwortliche für die Datenverarbeitung ist der App-Nutzer selbst, da alle Daten lokal gespeichert werden.

2. Erhobene Daten
- Eingegebene Haarparameter (Tiefe, Nuance)
- Hochgeladene Bilder (werden nur lokal analysiert)
- Rezeptdaten in lokaler SQLite-Datenbank

3. Datenverarbeitung
Alle Daten werden ausschließlich lokal auf Ihrem Gerät verarbeitet. Es erfolgt keine Übermittlung an externe Server.

4. Datenspeicherung
Daten werden in einer lokaler SQLite-Datenbank gespeichert und verbleiben auf Ihrem Gerät.

5. Ihre Rechte
Sie haben jederzeit das Recht, die App zu deinstallieren, wodurch alle lokalen Daten gelöscht werden.

6. Kontakt
Bei Fragen zum Datenschutz kontaktieren Sie bitte den App-Entwickler."""
    
    # Versuche in verschiedenen Verzeichnissen zu erstellen
    create_dirs = [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
        os.path.dirname(os.path.abspath(sys.argv[0])),
        r"C:\Fertige Version für Playstore"
    ]
    
    created_agb = None
    created_ds = None
    
    for directory in create_dirs:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except:
                continue
        
        agb_path = os.path.join(directory, "agb.txt")
        ds_path = os.path.join(directory, "datenschutz.txt")
        
        try:
            with open(agb_path, "w", encoding="utf-8") as f:
                f.write(agb_content)
                created_agb = agb_path
                print(f"  AGB erstellt in: {agb_path}")
        except:
            pass
        
        try:
            with open(ds_path, "w", encoding="utf-8") as f:
                f.write(datenschutz_content)
                created_ds = ds_path
                print(f"  Datenschutz erstellt in: {ds_path}")
        except:
            pass
    
    return created_agb, created_ds

def show_agb_popup(app):
    """Zeigt das AGB-Popup an"""
    print("\n=== START AGB-PROZESS ===")
    
    # 1. Versuche existierende Dateien zu finden
    agb_path, datenschutz_path = find_agb_files()
    
    # 2. Wenn keine gefunden, erstelle Standard-Dateien
    if not agb_path or not datenschutz_path:
        print("Keine AGB-Dateien gefunden, erstelle Standard...")
        agb_path, datenschutz_path = create_default_agb()
    
    # 3. Dateien einlesen
    agb_text = ""
    datenschutz_text = ""
    
    try:
        if agb_path and os.path.exists(agb_path):
            with open(agb_path, "r", encoding="utf-8") as f:
                agb_text = f.read()
            print(f"AGB erfolgreich gelesen von: {agb_path}")
        else:
            agb_text = "AGB Datei konnte nicht gefunden oder gelesen werden."
            print("WARNUNG: AGB Datei nicht lesbar")
    except Exception as e:
        agb_text = f"Fehler beim Lesen der AGB: {str(e)}"
        print(f"FEHLER beim Lesen der AGB: {e}")
    
    try:
        if datenschutz_path and os.path.exists(datenschutz_path):
            with open(datenschutz_path, "r", encoding="utf-8") as f:
                datenschutz_text = f.read()
            print(f"Datenschutz erfolgreich gelesen von: {datenschutz_path}")
        else:
            datenschutz_text = "Datenschutz-Datei konnte nicht gefunden oder gelesen werden."
            print("WARNUNG: Datenschutz Datei nicht lesbar")
    except Exception as e:
        datenschutz_text = f"Fehler beim Lesen der Datenschutzerklärung: {str(e)}"
        print(f"FEHLER beim Lesen der Datenschutz: {e}")
    
    # Layout für das Popup
    layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
    
    # Titel
    title_label = Label(text="AGB & Datenschutzerklärung", font_size=20, size_hint_y=None, height=50)
    layout.add_widget(title_label)
    
    # Scrollbare Labels für AGB
    scroll_agb = ScrollView(size_hint=(1, 0.45))
    agb_label = Label(text=agb_text, size_hint_y=None, text_size=(450, None),
                      halign="left", valign="top")
    agb_label.bind(texture_size=agb_label.setter('size'))
    scroll_agb.add_widget(agb_label)
    
    # Trennlinie
    layout.add_widget(Label(text="-" * 50, size_hint_y=None, height=10))
    
    # Scrollbare Labels für Datenschutz
    scroll_datenschutz = ScrollView(size_hint=(1, 0.45))
    datenschutz_label = Label(text=datenschutz_text, size_hint_y=None, text_size=(450, None),
                              halign="left", valign="top")
    datenschutz_label.bind(texture_size=datenschutz_label.setter('size'))
    scroll_datenschutz.add_widget(datenschutz_label)
    
    layout.add_widget(scroll_agb)
    layout.add_widget(scroll_datenschutz)
    
    # Buttons
    button_layout = BoxLayout(size_hint_y=None, height=60, spacing=20)
    accept_btn = Button(text="Akzeptieren", background_color=(0.2, 0.8, 0.2, 1))
    decline_btn = Button(text="Ablehnen", background_color=(0.8, 0.2, 0.2, 1))
    button_layout.add_widget(decline_btn)
    button_layout.add_widget(accept_btn)
    layout.add_widget(button_layout)
    
    # Popup erstellen
    popup = Popup(title="",
                  content=layout,
                  size_hint=(0.95, 0.95),
                  auto_dismiss=False,
                  separator_color=[0.2, 0.4, 0.8, 1])
    
    # Button-Bindings
    accept_btn.bind(on_press=lambda x: accept_agb(popup, app))
    decline_btn.bind(on_press=lambda x: decline_agb(popup, app))
    
    print("AGB-Popup wird angezeigt")
    popup.open()
    
    return popup

def accept_agb(popup, app):
    """Wird aufgerufen, wenn AGB akzeptiert werden"""
    print("AGB akzeptiert")
    popup.dismiss()
    app.agb_accepted = True
    app.build_main_ui()  # UI erst nach Akzeptieren laden

def decline_agb(popup, app):
    """Wird aufgerufen, wenn AGB abgelehnt werden"""
    print("AGB abgelehnt - App wird beendet")
    popup.dismiss()
    app.stop()

# ------------------ Datenbank ------------------

class HairColorDatabase:
    """Datenbank-Manager für Haarfarben-Rezepte"""

    def __init__(self):
        self.db_path = DB_FILENAME
        self.init_database()

    def ensure_db_folder(self, path: str):
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

    def compute_recipe_text(self, s_depth: int, s_nu: float, t_depth: int, t_nu: float) -> Tuple[str, str]:
        level_diff = t_depth - s_depth
        recipe_steps = []
        oxidant = "10 Vol"
        remain_lift = min(level_diff, 4) if level_diff > 0 else 0

        if remain_lift <= 1:
            oxidant = "10 Vol"
        elif remain_lift == 2:
            oxidant = "20 Vol"
        elif remain_lift == 3:
            oxidant = "30 Vol"
        else:
            oxidant = "40 Vol"

        if level_diff > 4:
            bleach_lift = level_diff - 4
            intermediate_depth = min(s_depth + bleach_lift, t_depth - 1)
            recipe_steps.append(f"1) Blondierung: Aufhellen von {s_depth} → {intermediate_depth} ({bleach_lift} Stufen)")
            recipe_steps.append(f"2) Tonung/Farbe auf {t_depth}.{int(t_nu*10)} mit Oxidant {oxidant}")
        else:
            if level_diff > 0:
                recipe_steps.append(f"1) Farbauftrag: von {s_depth} → {t_depth} mit Oxidant {oxidant}")
            elif level_diff == 0:
                recipe_steps.append(f"1) Nuancierung / Refresh: Farbe {t_depth}.{int(t_nu*10)}")
            else:
                recipe_steps.append(f"1) Dunkeln: von {s_depth} → {t_depth} mit Oxidant {oxidant}")

        # Nuance-Korrektur
        mapping = {
            0.0: "Neutralisierung",
            0.1: "Aschbeimischung",
            0.3: "Gold/warme Nuance",
            0.4: "Kupferzugabe",
            0.6: "Rotanteile",
            0.7: "Violett",
            0.8: "Blau"
        }
        corr = mapping.get(t_nu, None)
        if corr:
            recipe_steps.append(f"Nuance-Korrektur: {corr}")

        recipe_steps.append("Mischverhältnis: Farbtube + Entwicklungsflüssigkeit nach Hersteller; evtl. 1:1.5 für Toner")
        recipe_text = "\n".join(recipe_steps)
        return recipe_text, oxidant

    def init_database(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        self.ensure_db_folder(self.db_path)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS Color_Base (
            base_id INTEGER PRIMARY KEY,
            name TEXT,
            lab_l_center REAL,
            lab_a_center REAL,
            lab_b_center REAL,
            depth INTEGER,
            nuance REAL
        );
        CREATE TABLE IF NOT EXISTS Recipe_Combination (
            combo_id INTEGER PRIMARY KEY,
            source_depth INTEGER,
            target_depth INTEGER,
            source_nuance REAL,
            target_nuance REAL,
            recipe_formula TEXT,
            oxidant_code TEXT
        );
        """)
        conn.commit()
        conn.close()

    def get_recipe_from_db(self, s_depth, s_nu, t_depth, t_nu):
        return self.compute_recipe_text(s_depth, s_nu, t_depth, t_nu)

# ------------------ App ------------------

class HairApp(App):
    def build(self):
        print("\n=== APP START ===")
        self.agb_accepted = False
        
        # Leeres Layout erstellen
        self.layout = BoxLayout()
        
        # AGB-Popup anzeigen (UI wird erst nach Akzeptieren geladen)
        Clock.schedule_once(lambda dt: show_agb_popup(self), 0.5)
        
        return self.layout
    
    def build_main_ui(self):
        """Haupt-UI erstellen (nach AGB-Akzeptanz)"""
        print("\n=== BUILD MAIN UI ===")
        self.layout.clear_widgets()
        
        # Datenbank initialisieren
        print("Initialisiere Datenbank...")
        self.database = HairColorDatabase()
        threading.Thread(target=self.init_database_background, daemon=True).start()

        # Hauptlayout
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Titel
        self.main_layout.add_widget(Label(text='HAARFARBEN ANALYSE', font_size=26, 
                                         size_hint_y=None, height=60, 
                                         color=[0.2, 0.4, 0.8, 1]))

        # Status
        self.status = Label(text='Bereit', size_hint_y=None, height=30, 
                           color=(0.6,0.6,0.6,1))
        self.main_layout.add_widget(self.status)

        # Modus-Auswahl
        mode_layout = BoxLayout(orientation='horizontal', size_hint_y=None, 
                               height=50, spacing=10)
        self.manual_btn = Button(text='Manuell', background_color=(0.2,0.6,0.8,1))
        self.image_btn = Button(text='Bild', background_color=(0.2,0.8,0.6,1))
        self.manual_btn.bind(on_press=self.show_manual)
        self.image_btn.bind(on_press=self.show_image_upload)
        mode_layout.add_widget(self.manual_btn)
        mode_layout.add_widget(self.image_btn)
        self.main_layout.add_widget(mode_layout)

        # Content Area
        self.content_area = BoxLayout(orientation='vertical', size_hint_y=1)
        self.main_layout.add_widget(self.content_area)

        self.layout.add_widget(self.main_layout)
        self.show_manual(None)
        
        print("Haupt-UI erfolgreich geladen")

    def init_database_background(self):
        try:
            self.database.init_database()
            Clock.schedule_once(lambda dt: self.update_status("Datenbank geladen", (0,0.7,0,1)), 0)
            print("Datenbank erfolgreich initialisiert")
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(f"Datenbankfehler: {e}", (1,0,0,1)), 0)
            print(f"FEHLER bei Datenbank: {e}")

    def update_status(self, text, color=(0.6,0.6,0.6,1)):
        self.status.text = text
        self.status.color = color

    def clear_content(self):
        self.content_area.clear_widgets()

    # ------------------ Manuelle Eingabe ------------------

    def show_manual(self, instance):
        self.clear_content()
        self.update_status("Manuelle Eingabe")

        self.content_area.add_widget(Label(text='Aktuelle Haarfarbe:', font_size=18, 
                                          size_hint_y=None, height=40))
        grid1 = GridLayout(cols=2, size_hint_y=None, height=80, spacing=10)
        grid1.add_widget(Label(text='Tiefe (1-10):'))
        self.current_depth = TextInput(text='5', multiline=False, input_filter='int')
        grid1.add_widget(self.current_depth)
        grid1.add_widget(Label(text='Nuance:'))
        self.current_nuance = TextInput(text='0.3', multiline=False)
        grid1.add_widget(self.current_nuance)
        self.content_area.add_widget(grid1)

        self.content_area.add_widget(Label(text='Gewünschte Haarfarbe:', font_size=18, 
                                          size_hint_y=None, height=40))
        grid2 = GridLayout(cols=2, size_hint_y=None, height=80, spacing=10)
        grid2.add_widget(Label(text='Tiefe (1-10):'))
        self.target_depth = TextInput(text='7', multiline=False, input_filter='int')
        grid2.add_widget(self.target_depth)
        grid2.add_widget(Label(text='Nuance:'))
        self.target_nuance = TextInput(text='0.1', multiline=False)
        grid2.add_widget(self.target_nuance)
        self.content_area.add_widget(grid2)

        self.content_area.add_widget(Label(text="Nuancen: 0.0=Neutral, 0.1=Asch, 0.3=Gold, 0.4=Kupfer, 0.6=Rot, 0.7=Violett, 0.8=Blau",
                                           size_hint_y=None, height=40, font_size=12, 
                                           color=(0.5,0.5,0.5,1)))

        calc_btn = Button(text='REZEPT BERECHNEN', size_hint_y=None, height=60, 
                         background_color=(0.8,0.2,0.4,1), font_size=18)
        calc_btn.bind(on_press=self.calculate_recipe_from_db)
        self.content_area.add_widget(calc_btn)

        self.result_label = Label(text='', size_hint_y=1, halign='left', valign='top')
        scroll = ScrollView(size_hint_y=1)
        scroll.add_widget(self.result_label)
        self.content_area.add_widget(scroll)

    # ------------------ Bildanalyse ------------------

    def show_image_upload(self, instance):
        if not getattr(self, 'agb_accepted', False):
            self.update_status("Bitte AGB akzeptieren!", (1,0,0,1))
            return

        self.clear_content()
        self.update_status("Bild hochladen")
        self.content_area.add_widget(Label(text='Bildanalyse:', font_size=18, 
                                          size_hint_y=None, height=40))

        self.image_button = Button(text='BILD AUSWÄHLEN', size_hint_y=None, height=120, 
                                  background_color=(0.4,0.6,0.9,1), font_size=20)
        self.image_button.bind(on_press=self.select_image_file)
        self.content_area.add_widget(self.image_button)

        self.file_info = Label(text='Kein Bild ausgewählt', size_hint_y=None, 
                              height=40, color=(0.5,0.5,0.5,1))
        self.content_area.add_widget(self.file_info)

        self.preview_label = Label(text='Vorschau erscheint hier', size_hint_y=None, 
                                  height=100)
        self.content_area.add_widget(self.preview_label)

        self.content_area.add_widget(Label(text='Ziel-Haarfarbe:', font_size=18, 
                                          size_hint_y=None, height=40))
        grid = GridLayout(cols=2, size_hint_y=None, height=80, spacing=10)
        grid.add_widget(Label(text='Tiefe (1-10):'))
        self.image_target_depth = TextInput(text='7', multiline=False, input_filter='int')
        grid.add_widget(self.image_target_depth)
        grid.add_widget(Label(text='Nuance:'))
        self.image_target_nuance = TextInput(text='0.1', multiline=False)
        grid.add_widget(self.image_target_nuance)
        self.content_area.add_widget(grid)

        analyze_btn = Button(text='ANALYSIEREN', size_hint_y=None, height=60, 
                            background_color=(0.4,0.2,0.8,1))
        analyze_btn.bind(on_press=self.start_image_analysis)
        self.content_area.add_widget(analyze_btn)

        self.image_result = Label(text='', size_hint_y=1, halign='left', valign='top')
        scroll = ScrollView(size_hint_y=1)
        scroll.add_widget(self.image_result)
        self.content_area.add_widget(scroll)

    def select_image_file(self, instance):
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        file_path = filedialog.askopenfilename(
            title="Bild auswählen",
            filetypes=[("Bilder","*.png *.jpg *.jpeg *.bmp"), ("Alle Dateien","*.*")]
        )
        if file_path:
            self.selected_image_path = file_path
            filename = os.path.basename(file_path)
            self.file_info.text = f"Ausgewählt: {filename}"
            self.image_button.text = f'{filename[:20]}...\n(Klicken zum Ändern)'
            self.update_status(f"Bild geladen: {filename}")
        root.destroy()

    def start_image_analysis(self, instance):
        if not getattr(self, 'agb_accepted', False):
            self.update_status("Bitte AGB akzeptieren!", (1,0,0,1))
            return
        if not hasattr(self, 'selected_image_path'):
            self.image_result.text = "Bitte erst ein Bild auswählen"
            return

        self.image_result.text = "Analysiere Bild...\nBitte warten..."
        def analyze_thread():
            if HAS_IMAGE_ANALYSIS:
                result = analyze_hair_image_simple(self.selected_image_path)
            else:
                result = {"source_depth":5, "source_nuance":0.3, "avg_color":[120,100,80], "info":"Demo-Modus"}
            Clock.schedule_once(lambda dt: self.show_analysis_result_with_db(result), 0)
        threading.Thread(target=analyze_thread, daemon=True).start()

    def show_analysis_result_with_db(self, result):
        if "error" in result:
            self.image_result.text = f"FEHLER:\n{result['error']}"
            return
        target_depth = int(self.image_target_depth.text)
        target_nuance = float(self.image_target_nuance.text)
        source_depth = result.get("source_depth",5)
        source_nuance = result.get("source_nuance",0.3)
        recipe_text, oxidant = self.database.get_recipe_from_db(source_depth, source_nuance, target_depth, target_nuance)
        avg_color = result.get("avg_color",[0,0,0])
        info = result.get("info","Bild analysiert")
        self.image_result.text = f"""BILDANALYSE ERFOLGREICH

{info}

ERKANNT:
• Haartiefe: {source_depth}
• Nuance: {source_nuance}
• Durchschnittsfarbe: RGB{avg_color}

REZEPT AUS DATENBANK:
Oxidant: {oxidant}

{recipe_text}"""

    # ------------------ Berechnung manuell ------------------

    def calculate_recipe_from_db(self, instance):
        try:
            current_depth = int(self.current_depth.text)
            current_nuance = float(self.current_nuance.text)
            target_depth = int(self.target_depth.text)
            target_nuance = float(self.target_nuance.text)
        except:
            self.result_label.text = "Ungültige Eingabe"
            return

        recipe_text, oxidant = self.database.get_recipe_from_db(current_depth, current_nuance, target_depth, target_nuance)
        self.result_label.text = f"""REZEPT

Aktuell: {current_depth}.{int(current_nuance*10)}
Ziel: {target_depth}.{int(target_nuance*10)}

Oxidant: {oxidant}

{recipe_text}"""

if __name__ == '__main__':
    print("=" * 50)
    print("HAARFARBEN ANALYSE APP")
    print("=" * 50)
    HairApp().run()
