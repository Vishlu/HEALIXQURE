# """
# Install dependencies:
#     pip install google-generativeai textblob PySide6
#     python -m textblob.download_corpora
# """

# import sys
# import json
# import re
# from string import Template
# from datetime import datetime, timedelta, timezone
# from textblob import TextBlob  # For sentiment analysis

# import google.generativeai as genai
# from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
#                                QHBoxLayout, QTextEdit, QPushButton, QLabel,
#                                QFrame, QSpacerItem, QSizePolicy, QScrollArea)
# from PySide6.QtCore import Qt, QThread, Signal
# from PySide6.QtGui import QFont, QTextCursor

# # ----------------------------
# # CONFIGURE GEMINI
# # ----------------------------
# genai.configure(api_key="AIzaSyDWyYmlvq0xZImhrL43JAIkqKeiwOpv30Y")

# generation_config = {
#     "temperature": 0.3,  # Lower temperature for more factual medical responses
#     "top_p": 1,
#     "top_k": 1,
#     "max_output_tokens": 2048,
# }

# safety_settings = [
#     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
#     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
#     {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
#     {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
# ]

# model = genai.GenerativeModel(
#     model_name="gemini-2.0-flash",
#     generation_config=generation_config,
#     safety_settings=safety_settings,
# )

# # ----------------------------
# # MEDICINE AI ASSISTANT PROMPT TEMPLATE
# # ----------------------------
# MEDICINE_PROMPT_TMPL = Template(r"""
# You are a Medicine AI Assistant, a professional healthcare chatbot that provides accurate, reliable information about medications.
# Your role is to answer questions about medicines with factual, evidence-based information while emphasizing that users should always consult healthcare professionals.

# For each medicine query, provide a STRICT JSON object with:

# 1) medicine_name (the exact name of the medication)
# 2) generic_name (generic/chemical name if available)
# 3) uses (primary medical uses and indications)
# 4) dosage (typical dosage information - emphasize this may vary)
# 5) side_effects (common and serious side effects)
# 6) precautions (warnings, contraindications, special precautions)
# 7) interactions (drug-drug and drug-food interactions)
# 8) storage (storage conditions and requirements)
# 9) pregnancy_category (if applicable - FDA pregnancy categories)
# 10) availability (prescription status: OTC, Rx-only, etc.)
# 11) manufacturer (common manufacturers if known)
# 12) safety_warning (important safety alerts and disclaimers)

# IMPORTANT: Always include a clear disclaimer that this is informational only and not medical advice.

# Example Output:
# {
#   "medicine_name": "Ibuprofen",
#   "generic_name": "Ibuprofen",
#   "uses": ["Pain relief", "Fever reduction", "Anti-inflammatory"],
#   "dosage": "Adults: 200-400mg every 4-6 hours as needed (max 1200mg/day). Always follow doctor's instructions.",
#   "side_effects": ["Upset stomach", "Heartburn", "Nausea", "Dizziness", "Rare: Gastrointestinal bleeding"],
#   "precautions": ["Do not use if allergic to NSAIDs", "Avoid with kidney disease", "Use caution with heart conditions"],
#   "interactions": ["Blood thinners (warfarin)", "Other NSAIDs", "ACE inhibitors", "Diuretics"],
#   "storage": "Store at room temperature, away from moisture and heat",
#   "pregnancy_category": "Category C (consult doctor before use during pregnancy)",
#   "availability": "OTC and prescription strengths available",
#   "manufacturer": ["Advil", "Motrin", "Generic brands"],
#   "safety_warning": "WARNING: This information is for educational purposes only. Always consult a healthcare professional before taking any medication. Do not self-medicate."
# }

# Now answer this medicine question:

# Question: ${question}
# User Context: ${context}

# Rules:
# - RETURN VALID JSON ONLY (no markdown, no extra text)
# - Use double quotes for all strings
# - Include ALL fields (set to "Not specified" if unknown)
# - Be factual and evidence-based
# - Always include safety warnings and disclaimers
# - Do not provide dosage recommendations for specific individuals
# """)


# # ----------------------------
# # MEDICINE-SPECIFIC HELPER FUNCTIONS
# # ----------------------------
# def now_ist_str():
#     """Return current IST time formatted as 'YYYY-MM-DD HH:MM'."""
#     ist = timezone(timedelta(hours=5, minutes=30))
#     return datetime.now(ist).strftime("%Y-%m-%d %H:%M")

# def analyze_sentiment(text: str) -> str:
#     """Perform basic sentiment analysis using TextBlob"""
#     analysis = TextBlob(text)
#     if analysis.sentiment.polarity > 0.1:
#         return "positive"
#     elif analysis.sentiment.polarity < -0.1:
#         return "negative"
#     return "neutral"

# def extract_keywords(text: str) -> list:
#     """Extract important medical keywords"""
#     medical_terms = ['mg', 'dose', 'tablet', 'capsule', 'injection', 'syrup', 'cream', 'ointment']
#     blob = TextBlob(text)
#     nouns = [word.lower() for word, tag in blob.tags if tag.startswith('NN')]
#     # Prioritize medical terms
#     keywords = list(set([word for word in nouns if word in medical_terms] + nouns))[:8]
#     return keywords

# def build_medicine_prompt(question: str, context: str) -> str:
#     return MEDICINE_PROMPT_TMPL.substitute(
#         question=question.strip(),
#         context=context.strip(),
#         now_ist=now_ist_str(),
#     )

# def extract_json(text: str):
#     """Robust JSON extraction with improved error handling"""
#     try:
#         # First try direct parse
#         text = text.strip()
#         if text.startswith('{') and text.endswith('}'):
#             return json.loads(text)
        
#         # Handle code fences if present
#         fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
#         if fenced:
#             return json.loads(fenced.group(1))
        
#         # Fallback: find first complete JSON object
#         first = text.find('{')
#         last = text.rfind('}')
#         if first != -1 and last != -1:
#             return json.loads(text[first:last+1])
#     except json.JSONDecodeError as e:
#         print(f"JSON parsing error: {e}")
#     return None

# def normalize_medicine_result(d: dict) -> dict:
#     """Normalize medicine information with proper defaults"""
#     if not isinstance(d, dict):
#         return {}
    
#     # Ensure all required fields exist with appropriate defaults
#     out = {
#         "medicine_name": d.get("medicine_name", "Not specified").strip(),
#         "generic_name": d.get("generic_name", "Not specified").strip(),
#         "uses": list(set(d.get("uses", ["Not specified"]))),
#         "dosage": d.get("dosage", "Consult healthcare professional for proper dosage").strip(),
#         "side_effects": list(set(d.get("side_effects", ["Not specified"]))),
#         "precautions": list(set(d.get("precautions", ["Not specified"]))),
#         "interactions": list(set(d.get("interactions", ["Not specified"]))),
#         "storage": d.get("storage", "Store as per manufacturer instructions").strip(),
#         "pregnancy_category": d.get("pregnancy_category", "Consult doctor before use during pregnancy").strip(),
#         "availability": d.get("availability", "Not specified").strip(),
#         "manufacturer": list(set(d.get("manufacturer", ["Various manufacturers"]))),
#         "safety_warning": d.get("safety_warning", "WARNING: Always consult a healthcare professional before taking any medication. This information is for educational purposes only.").strip()
#     }
    
#     return out

# def get_medicine_info(question: str, context: str) -> dict | None:
#     """Get medicine information from AI model"""
#     prompt = build_medicine_prompt(question, context)
#     try:
#         convo = model.start_chat(history=[])
#         convo.send_message(prompt)
#         raw = convo.last.text
#         data = extract_json(raw)
        
#         if not data:
#             print("\n[WARN] Model returned invalid JSON. Providing basic information...")
#             # Fallback response
#             return {
#                 "medicine_name": question.split()[0] if question.split() else "Unknown",
#                 "generic_name": "Not specified",
#                 "uses": ["Please consult a pharmacist or doctor for accurate information"],
#                 "dosage": "Dosage must be determined by a healthcare professional based on individual needs",
#                 "side_effects": ["Consult medication leaflet or healthcare provider"],
#                 "precautions": ["Always read the package insert and follow doctor's instructions"],
#                 "interactions": ["Many drugs interact with other medications - consult your pharmacist"],
#                 "storage": "Follow storage instructions on packaging",
#                 "pregnancy_category": "Consult doctor before use during pregnancy or breastfeeding",
#                 "availability": "May require prescription - check with healthcare provider",
#                 "manufacturer": ["Various pharmaceutical companies"],
#                 "safety_warning": "IMPORTANT: This is general information. Always consult a healthcare professional for medical advice."
#             }
            
#         return normalize_medicine_result(data)
#     except Exception as e:
#         print(f"\n[ERROR] Medicine information retrieval failed: {str(e)}")
#         return None

# # ----------------------------
# # THREAD FOR AI PROCESSING
# # ----------------------------
# class AIWorker(QThread):
#     finished = Signal(dict)
#     error = Signal(str)
    
#     def __init__(self, question, context):
#         super().__init__()
#         self.question = question
#         self.context = context
        
#     def run(self):
#         try:
#             result = get_medicine_info(self.question, self.context)
#             if result:
#                 self.finished.emit(result)
#             else:
#                 self.error.emit("Could not retrieve medicine information.")
#         except Exception as e:
#             self.error.emit(f"Error: {str(e)}")

# # ----------------------------
# # UI COMPONENTS
# # ----------------------------
# class AutoResizeTextEdit(QTextEdit):
#     def __init__(self):
#         super().__init__()
#         # Set initial and maximum heights
#         self.setMinimumHeight(60)
#         self.setMaximumHeight(300)  # Max height to prevent excessive growth
        
#         # Connect content changes to height adjustment
#         self.document().contentsChanged.connect(self.adjustHeight)
        
#         # Disable scroll bars since we're auto-resizing
#         self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#         self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
#         # Initial height adjustment
#         self.adjustHeight()

#     def adjustHeight(self):
#         # Get the document height
#         doc_height = self.document().size().height()
        
#         # Add margins and padding
#         margins = self.contentsMargins()
#         total_margin = margins.top() + margins.bottom()
        
#         # Calculate new height (minimum 60px, maximum 300px)
#         new_height = max(60, min(300, int(doc_height + total_margin + 10)))
        
#         # Set the new height
#         self.setFixedHeight(new_height)
        
#         # Update the parent container if needed
#         if self.parent() and hasattr(self.parent().parent(), 'setMinimumHeight'):
#             container_height = new_height + 40  # Extra space for container padding
#             self.parent().parent().setMinimumHeight(container_height)

# class ResponseWidget(QFrame):
#     def __init__(self, result):
#         super().__init__()
#         self.setup_ui(result)
        
#     def setup_ui(self, result):
#         self.setStyleSheet("""
#             QFrame {
#                 background-color: white;
#                 border-radius: 12px;
#                 border: 1px solid #e0e0e0;
#                 margin: 15px 5px;
#                 padding: 20px;
#             }
#         """)
        
#         layout = QVBoxLayout(self)
#         layout.setSpacing(12)
        
#         # Medicine name and generic name
#         medicine_text = f"💊 {result.get('medicine_name', 'Unknown Medicine')}"
#         if result.get('generic_name') != "Not specified":
#             medicine_text += f"\nGeneric: {result.get('generic_name')}"
        
#         medicine_label = QLabel(medicine_text)
#         medicine_label.setStyleSheet("""
#             QLabel {
#                 color: #2c2c2c;
#                 font-size: 18px;
#                 font-weight: bold;
#                 font-family: 'Segoe UI', Arial, sans-serif;
#                 padding-bottom: 5px;
#                 border-bottom: 2px solid #f0f0f0;
#             }
#         """)
#         medicine_label.setWordWrap(True)
#         layout.addWidget(medicine_label)
        
#         # Uses section
#         if result.get('uses') and result.get('uses')[0] != "Not specified":
#             uses_widget = self.create_section_widget("🏥 Primary Uses:", result.get('uses', []))
#             layout.addWidget(uses_widget)
        
#         # Dosage section
#         if result.get('dosage') != "Consult healthcare professional for proper dosage":
#             dosage_widget = self.create_text_widget("📋 Dosage Information:", result.get('dosage', ''))
#             layout.addWidget(dosage_widget)
        
#         # Side Effects section
#         if result.get('side_effects') and result.get('side_effects')[0] != "Not specified":
#             side_effects_widget = self.create_section_widget("⚠️ Side Effects:", result.get('side_effects', []))
#             layout.addWidget(side_effects_widget)
        
#         # Precautions section
#         if result.get('precautions') and result.get('precautions')[0] != "Not specified":
#             precautions_widget = self.create_section_widget("🚫 Precautions:", result.get('precautions', []))
#             layout.addWidget(precautions_widget)
        
#         # Interactions section
#         if result.get('interactions') and result.get('interactions')[0] != "Not specified":
#             interactions_widget = self.create_section_widget("🔗 Interactions:", result.get('interactions', []))
#             layout.addWidget(interactions_widget)
        
#         # Storage section
#         if result.get('storage') != "Store as per manufacturer instructions":
#             storage_widget = self.create_text_widget("🌡️ Storage:", result.get('storage', ''))
#             layout.addWidget(storage_widget)
        
#         # Pregnancy category
#         if result.get('pregnancy_category') != "Consult doctor before use during pregnancy":
#             pregnancy_widget = self.create_text_widget("🤰 Pregnancy:", result.get('pregnancy_category', ''))
#             layout.addWidget(pregnancy_widget)
        
#         # Availability
#         if result.get('availability') != "Not specified":
#             availability_widget = self.create_text_widget("🛒 Availability:", result.get('availability', ''))
#             layout.addWidget(availability_widget)
        
#         # Manufacturer
#         if result.get('manufacturer') and result.get('manufacturer')[0] != "Various manufacturers":
#             manufacturer_widget = self.create_section_widget("🏭 Common Manufacturers:", result.get('manufacturer', []))
#             layout.addWidget(manufacturer_widget)
        
#         # Safety Warning
#         if result.get('safety_warning'):
#             warning_label = QLabel("🔴 " + result.get('safety_warning'))
#             warning_label.setStyleSheet("""
#                 QLabel {
#                     color: #d32f2f;
#                     font-size: 13px;
#                     font-family: 'Segoe UI', Arial, sans-serif;
#                     font-weight: bold;
#                     margin-top: 15px;
#                     padding: 12px;
#                     background-color: #ffebee;
#                     border-radius: 8px;
#                     border: 1px solid #ffcdd2;
#                 }
#             """)
#             warning_label.setWordWrap(True)
#             layout.addWidget(warning_label)
    
#     def create_section_widget(self, title, items):
#         widget = QWidget()
#         layout = QVBoxLayout(widget)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.setSpacing(5)
        
#         title_label = QLabel(title)
#         title_label.setStyleSheet("""
#             QLabel {
#                 color: #2c2c2c;
#                 font-size: 16px;
#                 font-weight: bold;
#                 font-family: 'Segoe UI', Arial, sans-serif;
#             }
#         """)
#         layout.addWidget(title_label)
        
#         for item in items:
#             item_label = QLabel(f"• {item}")
#             item_label.setStyleSheet("""
#                 QLabel {
#                     color: #444444;
#                     font-size: 14px;
#                     font-family: 'Segoe UI', Arial, sans-serif;
#                     margin-left: 10px;
#                 }
#             """)
#             item_label.setWordWrap(True)
#             layout.addWidget(item_label)
        
#         return widget
    
#     def create_text_widget(self, title, text):
#         widget = QWidget()
#         layout = QVBoxLayout(widget)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.setSpacing(5)
        
#         title_label = QLabel(title)
#         title_label.setStyleSheet("""
#             QLabel {
#                 color: #2c2c2c;
#                 font-size: 16px;
#                 font-weight: bold;
#                 font-family: 'Segoe UI', Arial, sans-serif;
#             }
#         """)
#         layout.addWidget(title_label)
        
#         text_label = QLabel(text)
#         text_label.setStyleSheet("""
#             QLabel {
#                 color: #444444;
#                 font-size: 14px;
#                 font-family: 'Segoe UI', Arial, sans-serif;
#                 margin-left: 10px;
#             }
#         """)
#         text_label.setWordWrap(True)
#         layout.addWidget(text_label)
        
#         return widget

# class ChatBotHomeWidget(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setup_ui()

#     def setup_ui(self):
#         self.setStyleSheet("""
#             QWidget {
#                 background-color: #f8f6f3;
#             }
#         """)

#         main_layout = QVBoxLayout(self)
#         main_layout.setContentsMargins(40, 30, 40, 30)
#         main_layout.setSpacing(20)

#         # Title - centered and positioned higher
#         title_label = QLabel("💊 HealixQure – What Can I Help With?")
#         title_label.setStyleSheet("""
#             QLabel {
#                 color: #2c2c2c;
#                 font-size: 28px;
#                 font-weight: bold;
#                 font-family: 'Segoe UI', Arial, sans-serif;
#                 margin-bottom: 10px;
#             }
#         """)
#         title_label.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(title_label)

#         # Input container that will resize with content
#         self.input_container = QFrame()
#         self.input_container.setFixedWidth(700)
#         self.input_container.setMinimumHeight(100)
#         self.input_container.setStyleSheet("""
#             QFrame {
#                 background-color: white;
#                 border-radius: 12px;
#                 border: 1px solid #e0e0e0;
#                 margin: 5px;
#             }
#             QFrame:hover {
#                 border: 1px solid #d0d0d0;
#             }
#         """)

#         input_layout = QHBoxLayout(self.input_container)
#         input_layout.setContentsMargins(15, 10, 15, 10)
#         input_layout.setSpacing(10)

#         # Auto-resizing text input with minimal internal padding
#         self.text_input = AutoResizeTextEdit()
#         self.text_input.setPlaceholderText("Ask about any medicine...")
#         self.text_input.setStyleSheet("""
#             QTextEdit {
#                 border: none;
#                 background: transparent;
#                 font-size: 16px;
#                 font-family: 'Segoe UI', Arial, sans-serif;
#                 color: #2c2c2c;
#                 padding-left: 8px;
#                 padding-right: 8px;
#                 padding-top: 6px;
#                 padding-bottom: 6px;
#             }
#             QTextEdit:focus {
#                 outline: none;
#             }
#         """)
#         input_layout.addWidget(self.text_input, 1)



#         # Send button
#         self.send_button = QPushButton("↗")
#         self.send_button.setFixedSize(45, 45)
#         self.send_button.setStyleSheet("""
#             QPushButton {
#                 background-color: #2c2c2c;
#                 color: white;
#                 border: none;
#                 border-radius: 22px;
#                 font-size: 18px;
#                 font-weight: bold;
#                 font-family: Arial;
#             }
#             QPushButton:hover {
#                 background-color: #404040;
#             }
#             QPushButton:pressed {
#                 background-color: #1a1a1a;
#             }
#             QPushButton:disabled {
#                 background-color: #cccccc;
#             }
#         """)
#         self.send_button.clicked.connect(self.send_message)
#         input_layout.addWidget(self.send_button)

#         main_layout.addWidget(self.input_container, alignment=Qt.AlignCenter)

#         # Response area
#         self.scroll_area = QScrollArea()
#         self.scroll_area.setWidgetResizable(True)
#         self.scroll_area.setFixedWidth(750)
#         self.scroll_area.setMinimumHeight(500)
#         self.scroll_area.setStyleSheet("""
#             QScrollArea {
#                 background-color: transparent;
#                 border: none;
#                 margin: 10px 0;
#             }
#             QScrollArea > QWidget > QWidget {
#                 background-color: transparent;
#             }
#         """)
        
#         self.response_container = QWidget()
#         self.response_layout = QVBoxLayout(self.response_container)
#         self.response_layout.setAlignment(Qt.AlignTop)
#         self.response_layout.setSpacing(15)
#         self.response_layout.setContentsMargins(5, 5, 5, 5)
        
#         self.scroll_area.setWidget(self.response_container)
#         main_layout.addWidget(self.scroll_area, alignment=Qt.AlignCenter)

#         # Loading indicator (initially hidden)
#         self.loading_label = QLabel("🔍 Searching for information...")
#         self.loading_label.setStyleSheet("""
#             QLabel {
#                 color: #666666;
#                 font-size: 14px;
#                 font-family: 'Segoe UI', Arial, sans-serif;
#                 font-style: italic;
#             }
#         """)
#         self.loading_label.setAlignment(Qt.AlignCenter)
#         self.loading_label.hide()
#         main_layout.addWidget(self.loading_label)

#         # Bottom spacer
#         bottom_spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
#         main_layout.addItem(bottom_spacer)

#     def send_message(self):
#         message = self.text_input.toPlainText().strip()
#         if message:
#             self.show_loading()
#             self.worker = AIWorker(message, message)
#             self.worker.finished.connect(self.handle_response)
#             self.worker.error.connect(self.handle_error)
#             self.worker.start()
#         else:
#             print("Please enter a message")

#     def show_loading(self):
#         self.loading_label.show()
#         self.send_button.setEnabled(False)

#     def hide_loading(self):
#         self.loading_label.hide()
#         self.send_button.setEnabled(True)

#     def handle_response(self, result):
#         self.hide_loading()
#         self.text_input.clear()
#         self.input_container.setMinimumHeight(100)
        
#         # Create and add response widget
#         response_widget = ResponseWidget(result)
#         self.response_layout.addWidget(response_widget)
        
#         # Scroll to bottom
#         QApplication.processEvents()  # Ensure UI updates
#         self.scroll_area.verticalScrollBar().setValue(
#             self.scroll_area.verticalScrollBar().maximum()
#         )

#     def handle_error(self, error_message):
#         self.hide_loading()
#         error_label = QLabel(f"❌ {error_message}")
#         error_label.setStyleSheet("""
#             QLabel {
#                 color: #d32f2f;
#                 font-size: 14px;
#                 font-family: 'Segoe UI', Arial, sans-serif;
#                 padding: 10px;
#                 background-color: #ffebee;
#                 border-radius: 8px;
#                 border: 1px solid #ffcdd2;
#                 margin: 10px;
#             }
#         """)
#         error_label.setWordWrap(True)
#         self.response_layout.addWidget(error_label)
        
#         # Scroll to bottom
#         self.scroll_area.verticalScrollBar().setValue(
#             self.scroll_area.verticalScrollBar().maximum()
#         )

# class ChatBotMainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setup_ui()

#     def setup_ui(self):
#         self.setWindowTitle("💊 HealixQure")
#         self.resize(1000, 700)
#         self.setMinimumSize(800, 600)

#         self.setStyleSheet("""
#             QMainWindow {
#                 background-color: #f8f6f3;
#             }
#         """)

#         self.setup_top_bar()
#         central_widget = ChatBotHomeWidget()
#         self.setCentralWidget(central_widget)

#     def setup_top_bar(self):
#         top_bar = QFrame()
#         top_bar.setFixedHeight(60)
#         top_bar.setStyleSheet("""
#             QFrame {
#                 background-color: #f8f6f3;
#                 border: none;
#             }
#         """)
#         top_layout = QHBoxLayout(top_bar)
#         top_layout.setContentsMargins(20, 10, 20, 10)

#         # Logout button
#         logout_top_button = QPushButton("⏻")
#         logout_top_button.setStyleSheet("""
#             QPushButton {
#                 background-color: #e74c3c;
#                 color: white;
#                 border: none;
#                 border-radius: 20px;
#                 padding: 10px 20px;
#                 font-size: 19px;
#                 font-weight: bold;
#                 font-family: 'Segoe UI', Arial, sans-serif;
#             }
#             QPushButton:hover {
#                 background-color: #c0392b;
#             }
#             QPushButton:pressed {
#                 background-color: #a93226;
#             }
#         """)
#         logout_top_button.clicked.connect(self.logout_clicked)
#         top_layout.addWidget(logout_top_button)

#         left_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
#         top_layout.addItem(left_spacer)

#         scan_button = QPushButton("Scan")
#         scan_button.setStyleSheet("""
#             QPushButton {
#                 background-color: #2c2c2c;
#                 color: white;
#                 border: 1px solid black;
#                 border-radius: 20px;
#                 padding: 10px 20px;
#                 font-size: 13px;
#                 font-weight: bold;
#                 font-family: 'Segoe UI', Arial, sans-serif;
#             }
#             QPushButton:hover {
#                 background-color: #404040;
#             }
#             QPushButton:pressed {
#                 background-color: #1a1a1a;
#             }
#         """)
#         scan_button.clicked.connect(self.scan_clicked)
#         top_layout.addWidget(scan_button)

#         self.setMenuWidget(top_bar)

#     def scan_clicked(self):
#         print("Scan button clicked")

#     def logout_clicked(self):
#         print("Logout button clicked from top bar")

# def main():
#     app = QApplication(sys.argv)
#     app.setStyle('Fusion')
#     window = ChatBotMainWindow()
#     window.show()
#     sys.exit(app.exec())

# if __name__ == "__main__":
#     main()



"""
Install dependencies:
    pip install google-generativeai textblob PySide6
    python -m textblob.download_corpora
"""

import sys
import json
import re
from string import Template
from datetime import datetime, timedelta, timezone
from textblob import TextBlob  # For sentiment analysis

import google.generativeai as genai
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QTextEdit, QPushButton, QLabel,
                               QFrame, QSpacerItem, QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor


# ----------------------------
# CONFIGURE GEMINI
# ----------------------------
genai.configure(api_key="AIzaSyDWyYmlvq0xZImhrL43JAIkqKeiwOpv30Y")

generation_config = {
    "temperature": 0.3,  # Lower temperature for more factual medical responses
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

# ----------------------------
# MEDICINE AI ASSISTANT PROMPT TEMPLATE
# ----------------------------
MEDICINE_PROMPT_TMPL = Template(r"""
You are a Medicine AI Assistant, a professional healthcare chatbot that provides accurate, reliable information about medications.
Your role is to answer questions about medicines with factual, evidence-based information while emphasizing that users should always consult healthcare professionals.

For each medicine query, provide a STRICT JSON object with:

1) medicine_name (the exact name of the medication)
2) generic_name (generic/chemical name if available)
3) uses (primary medical uses and indications)
4) dosage (typical dosage information - emphasize this may vary)
5) side_effects (common and serious side effects)
6) precautions (warnings, contraindications, special precautions)
7) interactions (drug-drug and drug-food interactions)
8) storage (storage conditions and requirements)
9) pregnancy_category (if applicable - FDA pregnancy categories)
10) availability (prescription status: OTC, Rx-only, etc.)
11) manufacturer (common manufacturers if known)
12) safety_warning (important safety alerts and disclaimers)

IMPORTANT: Always include a clear disclaimer that this is informational only and not medical advice.

Example Output:
{
  "medicine_name": "Ibuprofen",
  "generic_name": "Ibuprofen",
  "uses": ["Pain relief", "Fever reduction", "Anti-inflammatory"],
  "dosage": "Adults: 200-400mg every 4-6 hours as needed (max 1200mg/day). Always follow doctor's instructions.",
  "side_effects": ["Upset stomach", "Heartburn", "Nausea", "Dizziness", "Rare: Gastrointestinal bleeding"],
  "precautions": ["Do not use if allergic to NSAIDs", "Avoid with kidney disease", "Use caution with heart conditions"],
  "interactions": ["Blood thinners (warfarin)", "Other NSAIDs", "ACE inhibitors", "Diuretics"],
  "storage": "Store at room temperature, away from moisture and heat",
  "pregnancy_category": "Category C (consult doctor before use during pregnancy)",
  "availability": "OTC and prescription strengths available",
  "manufacturer": ["Advil", "Motrin", "Generic brands"],
  "safety_warning": "WARNING: This information is for educational purposes only. Always consult a healthcare professional before taking any medication. Do not self-medicate."
}

Now answer this medicine question:

Question: ${question}
User Context: ${context}

Rules:
- RETURN VALID JSON ONLY (no markdown, no extra text)
- Use double quotes for all strings
- Include ALL fields (set to "Not specified" if unknown)
- Be factual and evidence-based
- Always include safety warnings and disclaimers
- Do not provide dosage recommendations for specific individuals
""")


# ----------------------------
# MEDICINE-SPECIFIC HELPER FUNCTIONS
# ----------------------------
def now_ist_str():
    """Return current IST time formatted as 'YYYY-MM-DD HH:MM'."""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M")

def analyze_sentiment(text: str) -> str:
    """Perform basic sentiment analysis using TextBlob"""
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0.1:
        return "positive"
    elif analysis.sentiment.polarity < -0.1:
        return "negative"
    return "neutral"

def extract_keywords(text: str) -> list:
    """Extract important medical keywords"""
    medical_terms = ['mg', 'dose', 'tablet', 'capsule', 'injection', 'syrup', 'cream', 'ointment']
    blob = TextBlob(text)
    nouns = [word.lower() for word, tag in blob.tags if tag.startswith('NN')]
    # Prioritize medical terms
    keywords = list(set([word for word in nouns if word in medical_terms] + nouns))[:8]
    return keywords

def build_medicine_prompt(question: str, context: str) -> str:
    return MEDICINE_PROMPT_TMPL.substitute(
        question=question.strip(),
        context=context.strip(),
        now_ist=now_ist_str(),
    )

def extract_json(text: str):
    """Robust JSON extraction with improved error handling"""
    try:
        # First try direct parse
        text = text.strip()
        if text.startswith('{') and text.endswith('}'):
            return json.loads(text)
        
        # Handle code fences if present
        fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        if fenced:
            return json.loads(fenced.group(1))
        
        # Fallback: find first complete JSON object
        first = text.find('{')
        last = text.rfind('}')
        if first != -1 and last != -1:
            return json.loads(text[first:last+1])
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
    return None

def normalize_medicine_result(d: dict) -> dict:
    """Normalize medicine information with proper defaults"""
    if not isinstance(d, dict):
        return {}
    
    # Ensure all required fields exist with appropriate defaults
    out = {
        "medicine_name": d.get("medicine_name", "Not specified").strip(),
        "generic_name": d.get("generic_name", "Not specified").strip(),
        "uses": list(set(d.get("uses", ["Not specified"]))),
        "dosage": d.get("dosage", "Consult healthcare professional for proper dosage").strip(),
        "side_effects": list(set(d.get("side_effects", ["Not specified"]))),
        "precautions": list(set(d.get("precautions", ["Not specified"]))),
        "interactions": list(set(d.get("interactions", ["Not specified"]))),
        "storage": d.get("storage", "Store as per manufacturer instructions").strip(),
        "pregnancy_category": d.get("pregnancy_category", "Consult doctor before use during pregnancy").strip(),
        "availability": d.get("availability", "Not specified").strip(),
        "manufacturer": list(set(d.get("manufacturer", ["Various manufacturers"]))),
        "safety_warning": d.get("safety_warning", "WARNING: Always consult a healthcare professional before taking any medication. This information is for educational purposes only.").strip()
    }
    
    return out

def get_medicine_info(question: str, context: str) -> dict | None:
    """Get medicine information from AI model"""
    prompt = build_medicine_prompt(question, context)
    try:
        convo = model.start_chat(history=[])
        convo.send_message(prompt)
        raw = convo.last.text
        data = extract_json(raw)
        
        if not data:
            print("\n[WARN] Model returned invalid JSON. Providing basic information...")
            # Fallback response
            return {
                "medicine_name": question.split()[0] if question.split() else "Unknown",
                "generic_name": "Not specified",
                "uses": ["Please consult a pharmacist or doctor for accurate information"],
                "dosage": "Dosage must be determined by a healthcare professional based on individual needs",
                "side_effects": ["Consult medication leaflet or healthcare provider"],
                "precautions": ["Always read the package insert and follow doctor's instructions"],
                "interactions": ["Many drugs interact with other medications - consult your pharmacist"],
                "storage": "Follow storage instructions on packaging",
                "pregnancy_category": "Consult doctor before use during pregnancy or breastfeeding",
                "availability": "May require prescription - check with healthcare provider",
                "manufacturer": ["Various pharmaceutical companies"],
                "safety_warning": "IMPORTANT: This is general information. Always consult a healthcare professional for medical advice."
            }
            
        return normalize_medicine_result(data)
    except Exception as e:
        print(f"\n[ERROR] Medicine information retrieval failed: {str(e)}")
        return None

# ----------------------------
# THREAD FOR AI PROCESSING
# ----------------------------
class AIWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, question, context):
        super().__init__()
        self.question = question
        self.context = context
        
    def run(self):
        try:
            result = get_medicine_info(self.question, self.context)
            if result:
                self.finished.emit(result)
            else:
                self.error.emit("Could not retrieve medicine information.")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")

# ----------------------------
# UI COMPONENTS
# ----------------------------
class AutoResizeTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()
        # Set initial and maximum heights
        self.setMinimumHeight(60)
        self.setMaximumHeight(300)  # Max height to prevent excessive growth
        
        # Connect content changes to height adjustment
        self.document().contentsChanged.connect(self.adjustHeight)
        
        # Disable scroll bars since we're auto-resizing
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Initial height adjustment
        self.adjustHeight()

    def adjustHeight(self):
        # Get the document height
        doc_height = self.document().size().height()
        
        # Add margins and padding
        margins = self.contentsMargins()
        total_margin = margins.top() + margins.bottom()
        
        # Calculate new height (minimum 60px, maximum 300px)
        new_height = max(60, min(300, int(doc_height + total_margin + 10)))
        
        # Set the new height
        self.setFixedHeight(new_height)
        
        # Update the parent container if needed
        if self.parent() and hasattr(self.parent().parent(), 'setMinimumHeight'):
            container_height = new_height + 40  # Extra space for container padding
            self.parent().parent().setMinimumHeight(container_height)

class ResponseWidget(QFrame):
    def __init__(self, result):
        super().__init__()
        self.setup_ui(result)
        
    def setup_ui(self, result):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                margin: 15px 5px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Medicine name and generic name
        medicine_text = f"Search: 💊 {result.get('medicine_name', 'Unknown Medicine')}"
        if result.get('generic_name') != "Not specified":
            medicine_text += f"\nGeneric: {result.get('generic_name')}"
         
        medicine_label = QLabel(medicine_text)
        medicine_label.setStyleSheet("""
            QLabel {
                color: #2c2c2c;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding-bottom: 5px;
                border-bottom: 2px solid #f0f0f0;
            }
        """)
        medicine_label.setWordWrap(True)
        layout.addWidget(medicine_label)
        
        # Uses section
        if result.get('uses') and result.get('uses')[0] != "Not specified":
            uses_widget = self.create_section_widget("🏥 Primary Uses:", result.get('uses', []))
            layout.addWidget(uses_widget)
        
        # Dosage section
        if result.get('dosage') != "Consult healthcare professional for proper dosage":
            dosage_widget = self.create_text_widget("📋 Dosage Information:", result.get('dosage', ''))
            layout.addWidget(dosage_widget)
        
        # Side Effects section
        if result.get('side_effects') and result.get('side_effects')[0] != "Not specified":
            side_effects_widget = self.create_section_widget("⚠️ Side Effects:", result.get('side_effects', []))
            layout.addWidget(side_effects_widget)
        
        # Precautions section
        if result.get('precautions') and result.get('precautions')[0] != "Not specified":
            precautions_widget = self.create_section_widget("🚫 Precautions:", result.get('precautions', []))
            layout.addWidget(precautions_widget)
        
        # Interactions section
        if result.get('interactions') and result.get('interactions')[0] != "Not specified":
            interactions_widget = self.create_section_widget("🔗 Interactions:", result.get('interactions', []))
            layout.addWidget(interactions_widget)
        
        # Storage section
        if result.get('storage') != "Store as per manufacturer instructions":
            storage_widget = self.create_text_widget("🌡️ Storage:", result.get('storage', ''))
            layout.addWidget(storage_widget)
        
        # Pregnancy category
        if result.get('pregnancy_category') != "Consult doctor before use during pregnancy":
            pregnancy_widget = self.create_text_widget("🤰 Pregnancy:", result.get('pregnancy_category', ''))
            layout.addWidget(pregnancy_widget)
        
        # Availability
        if result.get('availability') != "Not specified":
            availability_widget = self.create_text_widget("🛒 Availability:", result.get('availability', ''))
            layout.addWidget(availability_widget)
        
        # Manufacturer
        if result.get('manufacturer') and result.get('manufacturer')[0] != "Various manufacturers":
            manufacturer_widget = self.create_section_widget("🏭 Common Manufacturers:", result.get('manufacturer', []))
            layout.addWidget(manufacturer_widget)
        
        # Safety Warning
        if result.get('safety_warning'):
            warning_label = QLabel("🔴 " + result.get('safety_warning'))
            warning_label.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-size: 13px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-weight: bold;
                    margin-top: 15px;
                    padding: 12px;
                    background-color: #ffebee;
                    border-radius: 8px;
                    border: 1px solid #ffcdd2;
                }
            """)
            warning_label.setWordWrap(True)
            layout.addWidget(warning_label)
    
    def create_section_widget(self, title, items):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c2c2c;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        layout.addWidget(title_label)
        
        for item in items:
            item_label = QLabel(f"• {item}")
            item_label.setStyleSheet("""
                QLabel {
                    color: #444444;
                    font-size: 14px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin-left: 10px;
                }
            """)
            item_label.setWordWrap(True)
            layout.addWidget(item_label)
        
        return widget
    
    def create_text_widget(self, title, text):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c2c2c;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        layout.addWidget(title_label)
        
        text_label = QLabel(text)
        text_label.setStyleSheet("""
            QLabel {
                color: #444444;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-left: 10px;
            }
        """)
        text_label.setWordWrap(True)
        layout.addWidget(text_label)
        
        return widget

class ChatBotHomeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f6f3;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        # Title - centered and positioned higher
        title_label = QLabel("💊 HealixQure – What Can I Help With?")
        title_label.setStyleSheet("""
            QLabel {
                color: #2c2c2c;
                font-size: 28px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-bottom: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Input container that will resize with content
        self.input_container = QFrame()
        self.input_container.setFixedWidth(700)
        self.input_container.setMinimumHeight(100)
        self.input_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                margin: 5px;
            }
            QFrame:hover {
                border: 1px solid #d0d0d0;
            }
        """)

        input_layout = QHBoxLayout(self.input_container)
        input_layout.setContentsMargins(15, 10, 15, 10)
        input_layout.setSpacing(10)

        # Auto-resizing text input with minimal internal padding
        self.text_input = AutoResizeTextEdit()
        self.text_input.setPlaceholderText("Ask about any medicine...")
        self.text_input.setStyleSheet("""
            QTextEdit {
                border: none;
                background: transparent;
                font-size: 16px;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #2c2c2c;
                padding-left: 8px;
                padding-right: 8px;
                padding-top: 6px;
                padding-bottom: 6px;
            }
            QTextEdit:focus {
                outline: none;
            }
        """)
        input_layout.addWidget(self.text_input, 1)

        # Send button
        self.send_button = QPushButton("↗")
        self.send_button.setFixedSize(45, 45)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2c;
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 18px;
                font-weight: bold;
                font-family: Arial;
            }
            QPushButton:hover {
                background-color: #404040;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        main_layout.addWidget(self.input_container, alignment=Qt.AlignCenter)

        # Response area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedWidth(950)
        self.scroll_area.setMinimumHeight(480)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
                margin: 10px 0;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)
        
        self.response_container = QWidget()
        self.response_layout = QVBoxLayout(self.response_container)
        self.response_layout.setAlignment(Qt.AlignTop)
        self.response_layout.setSpacing(15)
        self.response_layout.setContentsMargins(5, 5, 5, 5)
        
        self.scroll_area.setWidget(self.response_container)
        main_layout.addWidget(self.scroll_area, alignment=Qt.AlignCenter)

        # Loading indicator (initially hidden)
        self.loading_label = QLabel("🔍 Searching for information...")
        self.loading_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-style: italic;
            }
        """)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.hide()
        main_layout.addWidget(self.loading_label)

        # Bottom spacer
        bottom_spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(bottom_spacer)

    def send_message(self):
        message = self.text_input.toPlainText().strip()
        if message:
            # Clear previous responses before showing loading
            self.clear_responses()
            self.show_loading()
            self.worker = AIWorker(message, message)
            self.worker.finished.connect(self.handle_response)
            self.worker.error.connect(self.handle_error)
            self.worker.start()
        else:
            print("Please enter a message")

    def clear_responses(self):
        """Clear all previous responses from the response area"""
        # Remove all widgets from the response layout
        while self.response_layout.count():
            child = self.response_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_loading(self):
        self.loading_label.show()
        self.send_button.setEnabled(False)

    def hide_loading(self):
        self.loading_label.hide()
        self.send_button.setEnabled(True)

    def handle_response(self, result):
        self.hide_loading()
        self.text_input.clear()
        self.input_container.setMinimumHeight(100)
        
        # Create and add response widget
        response_widget = ResponseWidget(result)
        self.response_layout.addWidget(response_widget)
        
        # Scroll to bottom
        QApplication.processEvents()  # Ensure UI updates
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def handle_error(self, error_message):
        self.hide_loading()
        error_label = QLabel(f"❌ {error_message}")
        error_label.setStyleSheet("""
            QLabel {
                color: #d32f2f;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 10px;
                background-color: #ffebee;
                border-radius: 8px;
                border: 1px solid #ffcdd2;
                margin: 10px;
            }
        """)
        error_label.setWordWrap(True)
        self.response_layout.addWidget(error_label)
        
        # Scroll to bottom
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

class ChatBotMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        

    def setup_ui(self):
        self.setWindowTitle("HealixQure")
        self.resize(1000, 700)
        self.setMinimumSize(800, 600)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f6f3;
            }
        """)

        self.setup_top_bar()
        central_widget = ChatBotHomeWidget()
        self.setCentralWidget(central_widget)

    def setup_top_bar(self):
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #f8f6f3;
                border: none;
            }
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 10, 20, 10)

        # Logout button
        logout_top_button = QPushButton("⏻")
        logout_top_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 19px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        logout_top_button.clicked.connect(self.logout_clicked)
        top_layout.addWidget(logout_top_button)

        left_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        top_layout.addItem(left_spacer)

        scan_button = QPushButton("Scan")
        scan_button.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2c;
                color: white;
                border: 1px solid black;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #404040;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        scan_button.clicked.connect(self.scan_clicked)
        top_layout.addWidget(scan_button)

        self.setMenuWidget(top_bar)

    def logout_clicked(self):
        print("Logout button clicked from top bar")
        self.open_login_page()
    
    def open_login_page(self):
        """Close current app and open login page"""
        try:
            # Dynamic import to avoid circular import
            from LoginPage import HealixQureLoginApp
            
            # Create new instance of login application
            self.login_app = HealixQureLoginApp()
            self.login_app.show()
            
            # Close the current application window
            self.close()
            
            print("Logged out successfully. Login page opened.")
            
        except Exception as e:
            print(f"Error opening login page: {e}")

    def scan_clicked(self):
        print("Scan button clicked")
        
        try:
            # Import the QR Scanner class from your attached file
            from QRCodeScanner import MedicineScanner
            
            # Create and show the QR Scanner window
            self.qr_scanner = MedicineScanner()
            self.qr_scanner.show()
            
            print("QR Code Scanner opened successfully")
            
        except Exception as e:
            print(f"Error opening QR Code Scanner: {e}")
            # Show error message to user
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Failed to open QR Scanner: {str(e)}")


    

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ChatBotMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()