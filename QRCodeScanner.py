# #!/usr/bin/env python3
# """
# medicine_scanner_gui.py

# COMPLETE FIXED VERSION - Default fields always visible, updates on scan
# """

# import sys
# import cv2
# from pyzbar.pyzbar import decode as zbar_decode
# from datetime import datetime, date
# import re
# import xml.etree.ElementTree as ET

# from PySide6.QtWidgets import (
#     QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
#     QPushButton, QLabel, QFrame, QGridLayout, QSizePolicy
# )
# from PySide6.QtCore import Qt, QThread, Signal
# from PySide6.QtGui import QImage, QPixmap

# # === QR SCANNER FUNCTIONS ===

# # GS1 AI mapping
# AI_MAPPING = {
#     '01': ('gtin', 14, True),   # GTIN fixed 14
#     '17': ('expiry', 6, True),  # Expiry YYMMDD (or sometimes YYYYMMDD)
#     '10': ('batch', None, False),  # Batch/Lot - variable
#     '21': ('serial', None, False)  # Serial - variable
# }

# def format_expiry(expiry_raw):
#     if not expiry_raw:
#         return None
#     s = re.sub(r'\D', '', expiry_raw)
#     try:
#         if len(s) == 6:  # YYMMDD
#             return datetime.strptime(s, '%y%m%d').date().isoformat()
#         if len(s) == 8:  # YYYYMMDD
#             return datetime.strptime(s, '%Y%m%d').date().isoformat()
#     except Exception:
#         return None
#     return None

# def check_validity(expiry_iso):
#     if not expiry_iso:
#         return "UNKNOWN"
#     try:
#         d = datetime.strptime(expiry_iso, '%Y-%m-%d').date()
#         return "VALID" if d >= date.today() else "EXPIRED"
#     except Exception:
#         return "UNKNOWN"

# def normalize_gtin(g):
#     """Normalize 12/13/14-digit codes to GTIN-14 string (prefixed with zeros if needed)."""
#     if not g:
#         return None
#     digits = re.sub(r'\D', '', str(g))
#     if len(digits) == 14:
#         return digits
#     if len(digits) == 13:
#         return '0' + digits
#     if len(digits) == 12:
#         return '00' + digits
#     return digits if digits else None

# def parse_parenthesis_form(s):
#     """Parse (AI)value(AI)value forms like (01)....(17)...."""
#     res = {}
#     for ai, val in re.findall(r'\((\d{2,3})\)([^\(]+)', s):
#         if ai in AI_MAPPING:
#             name, _, _ = AI_MAPPING[ai]
#             res[name] = val
#     if 'expiry' in res:
#         res['expiry_formatted'] = format_expiry(res['expiry'])
#     if 'gtin' in res:
#         res['gtin'] = normalize_gtin(res.get('gtin'))
#     return res

# def parse_gs1_data(raw):
#     """Parse concatenated GS1 AIs in payloads."""
#     if not raw:
#         return {}

#     data = raw
#     data = data.replace('\\x1D', '\x1D').replace('\\u001d', '\x1D').replace('|GS|', '\x1D')
#     data = data.replace('\u001d', '\x1D')
#     data = re.sub(r'^\]d2?', '', data, flags=re.IGNORECASE)

#     if data.startswith('('):
#         return parse_parenthesis_form(data)

#     segments = re.split(r'\x1D', data)
#     result = {}
#     for seg in segments:
#         seg = seg.strip()
#         if not seg:
#             continue
#         i = 0
#         L = len(seg)
#         while i + 2 <= L:
#             ai = seg[i:i+2]
#             if ai in AI_MAPPING:
#                 name, length, fixed = AI_MAPPING[ai]
#                 i += 2
#                 if fixed and length:
#                     if i + length <= L:
#                         val = seg[i:i+length]
#                         i += length
#                     else:
#                         val = seg[i:]
#                         i = L
#                 else:
#                     next_match = re.search(r'(' + '|'.join(AI_MAPPING.keys()) + r')', seg[i:])
#                     if next_match:
#                         next_pos = i + next_match.start()
#                         val = seg[i:next_pos]
#                         i = next_pos
#                     else:
#                         val = seg[i:]
#                         i = L
#                 if val:
#                     result[name] = val
#             else:
#                 i += 1

#     if 'expiry' in result and 'expiry_formatted' not in result:
#         result['expiry_formatted'] = format_expiry(result['expiry'])
#     if 'gtin' in result:
#         result['gtin'] = normalize_gtin(result.get('gtin'))
#     return result

# def interpret_payload(payload):
#     """Return a normalized dict with scheme and parsed data."""
#     p = payload.strip()
    
#     # URL
#     low = p.lower()
#     if low.startswith('http://') or low.startswith('https://'):
#         return {'scheme': 'URL', 'gtin': None, 'expiry': None, 'batch': None, 'serial': None,
#                 'extra': {'url': p}}

#     # XML/HTML-like
#     if p.startswith('<') and p.endswith('>'):
#         extra = {}
#         try:
#             root = ET.fromstring(p)
#             for child in root:
#                 tag = child.tag.strip()
#                 text = child.text.strip() if child.text else ''
#                 extra[tag] = text
#         except Exception as e:
#             extra['xml_error'] = str(e)
#         return {'scheme': 'CUSTOM_XML', 'gtin': None, 'expiry': None, 'batch': None, 'serial': None,
#                 'extra': extra}

#     # Digits-only EAN/UPC
#     digits = re.sub(r'\D', '', p)
#     if digits and len(digits) in (12, 13, 14):
#         gt = normalize_gtin(digits)
#         return {'scheme': 'EAN/UPC', 'gtin': gt, 'expiry': None, 'batch': None, 'serial': None,
#                 'extra': {}}

#     # GS1-like
#     if '\x1D' in p or '|GS|' in p or re.search(r'\(01\)', p) or re.search(r'01\d{14}', p):
#         parsed = parse_gs1_data(p)
#         return {'scheme': 'GS1',
#                 'gtin': parsed.get('gtin'),
#                 'expiry': parsed.get('expiry_formatted'),
#                 'batch': parsed.get('batch'),
#                 'serial': parsed.get('serial'),
#                 'extra': {}}

#     # Default: RAW
#     return {'scheme': 'RAW', 'gtin': None, 'expiry': None, 'batch': None, 'serial': None,
#             'extra': {'raw': p}}

# def try_decode(frame):
#     """Improved QR decoding with better preprocessing."""
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
#     clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
#     enhanced = clahe.apply(gray)
    
#     images_to_try = [
#         gray,
#         enhanced,
#         cv2.GaussianBlur(gray, (3, 3), 0),
#         cv2.medianBlur(gray, 3)
#     ]
    
#     for img in images_to_try:
#         r = zbar_decode(img)
#         if r:
#             try:
#                 return r[0].data.decode('utf-8', errors='ignore')
#             except:
#                 return str(r[0].data)
    
#     qrd = cv2.QRCodeDetector()
#     for img in [frame, cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)]:
#         data, pts, _ = qrd.detectAndDecode(img)
#         if data:
#             return data
    
#     return None

# # === GUI COMPONENTS ===

# class CameraWorker(QThread):
#     frame_ready = Signal(object)
#     qr_detected = Signal(object)  # Use object for thread safety
    
#     def __init__(self):
#         super().__init__()
#         self.camera_active = False
#         self.cap = None
#         self.camera_index = 0
#         self.last_qr_time = 0
        
#     def start_camera(self):
#         if not self.cap or not self.cap.isOpened():
#             self.init_camera()
#         self.camera_active = True
#         if not self.isRunning():
#             self.start()
    
#     def stop_camera(self):
#         self.camera_active = False
#         if self.cap:
#             self.cap.release()
#             self.cap = None
    
#     def init_camera(self):
#         for idx in [0, 1, 2]:
#             try:
#                 self.cap = cv2.VideoCapture(idx)
#                 if self.cap.isOpened():
#                     self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#                     self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
#                     self.cap.set(cv2.CAP_PROP_FPS, 30)
#                     try:
#                         self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
#                     except:
#                         pass
#                     self.camera_index = idx
#                     print(f"Camera initialized: index {idx}")
#                     return
#                 else:
#                     self.cap.release()
#             except Exception:
#                 pass
#         print("Failed to initialize camera")
    
#     def run(self):
#         import time
#         while self.camera_active and self.cap and self.cap.isOpened():
#             ret, frame = self.cap.read()
#             if ret:
#                 self.frame_ready.emit(frame)
                
#                 payload = try_decode(frame)
#                 if payload:
#                     current_time = time.time()
#                     if current_time - self.last_qr_time > 0.5:
#                         self.last_qr_time = current_time
                        
#                         print(f"Raw QR payload: {repr(payload)}")
                        
#                         info = interpret_payload(payload)
#                         print(f"Interpreted info: {info}")
                        
#                         parsed_output = {
#                             'scheme': info.get('scheme'),
#                             'gtin': info.get('gtin'),
#                             'expiry': info.get('expiry'),
#                             'batch': info.get('batch'),
#                             'serial': info.get('serial'),
#                             'status': check_validity(info.get('expiry')),
#                             'extra': info.get('extra', {})
#                         }
                        
#                         print(f"Final parsed output: {parsed_output}")
#                         self.qr_detected.emit(parsed_output)
            
#             self.msleep(16)

# class ResultDisplayWidget(QFrame):
#     def __init__(self):
#         super().__init__()
#         self.field_values = {}
#         self.setup_ui()
#         self.show_default_fields()  # Show default fields immediately
        
#     def setup_ui(self):
#         self.setStyleSheet("""
#             QFrame {
#                 background-color: white;
#                 border-radius: 15px;
#                 border: 2px solid #e0e0e0;
#                 padding: 20px;
#                 margin: 10px;
#             }
#         """)
        
#         # Ensure minimum size
#         self.setMinimumSize(450, 500)
#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
#         layout = QVBoxLayout(self)
#         layout.setSpacing(15)
#         layout.setContentsMargins(20, 20, 20, 20)
        
#         # Title - always visible
#         self.title_label = QLabel("📱 Scan Results")
#         self.title_label.setStyleSheet("""
#             QLabel {
#                 font-size: 24px;
#                 font-weight: bold;
#                 color: #2c5aa0;
#                 margin-bottom: 10px;
#             }
#         """)
#         layout.addWidget(self.title_label)
        
#         # Results grid with proper sizing
#         self.results_grid = QGridLayout()
#         self.results_grid.setSpacing(15)
#         self.results_grid.setContentsMargins(0, 0, 0, 0)
        
#         # CRITICAL: Set column stretch to ensure visibility
#         self.results_grid.setColumnStretch(0, 0)  # Labels column - fixed width
#         self.results_grid.setColumnStretch(1, 1)  # Values column - expandable
        
#         # Field definitions
#         fields = [
#             ('scheme', '🔍 Scheme'),
#             ('status', '✅ Status'),
#             ('gtin', '🏷️ GTIN'),
#             ('expiry', '📅 Expiry'),
#             ('batch', '📦 Batch'),
#             ('serial', '🔢 Serial'),
#         ]
        
#         # Create and add all field widgets
#         for i, (field, display_name) in enumerate(fields):
#             # Label
#             label = QLabel(display_name)
#             label.setStyleSheet("""
#                 QLabel {
#                     font-size: 16px;
#                     font-weight: bold;
#                     color: #555;
#                     min-width: 120px;
#                     max-width: 120px;
#                 }
#             """)
#             label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            
#             # Value
#             value = QLabel("Waiting for scan...")
#             value.setStyleSheet("""
#                 QLabel {
#                     font-size: 16px;
#                     color: #666;
#                     background-color: #f8f9fa;
#                     padding: 8px 12px;
#                     border-radius: 8px;
#                     border: 1px solid #e9ecef;
#                     min-height: 20px;
#                     min-width: 200px;
#                 }
#             """)
#             value.setWordWrap(True)
#             value.setAlignment(Qt.AlignLeft | Qt.AlignTop)
#             value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            
#             # Store references
#             self.field_values[field] = value
            
#             # Add to grid
#             self.results_grid.addWidget(label, i, 0)
#             self.results_grid.addWidget(value, i, 1)
        
#         layout.addLayout(self.results_grid)
        
#         # Extra info section
#         self.extra_label = QLabel("📋 Additional Information")
#         self.extra_label.setStyleSheet("""
#             QLabel {
#                 font-size: 18px;
#                 font-weight: bold;
#                 color: #2c5aa0;
#                 margin-top: 20px;
#                 margin-bottom: 10px;
#             }
#         """)
        
#         self.extra_value = QLabel("Ready to scan QR codes...")
#         self.extra_value.setStyleSheet("""
#             QLabel {
#                 font-size: 14px;
#                 color: #666;
#                 background-color: #f8f9fa;
#                 padding: 15px;
#                 border-radius: 10px;
#                 border: 1px solid #e9ecef;
#                 min-height: 60px;
#             }
#         """)
#         self.extra_value.setWordWrap(True)
        
#         layout.addWidget(self.extra_label)
#         layout.addWidget(self.extra_value)
        
#         # Add stretch to push everything to top
#         layout.addStretch()
    
#     def show_default_fields(self):
#         """Show default field names and values - called on startup"""
#         default_values = {
#             'scheme': 'Not detected',
#             'status': 'Not checked',
#             'gtin': 'Not provided',
#             'expiry': 'Not provided',
#             'batch': 'Not provided',
#             'serial': 'Not provided',
#         }
        
#         for field, default_text in default_values.items():
#             if field in self.field_values:
#                 self.field_values[field].setText(default_text)
#                 self.field_values[field].setStyleSheet("""
#                     QLabel {
#                         font-size: 16px;
#                         color: #666;
#                         background-color: #f8f9fa;
#                         padding: 8px 12px;
#                         border-radius: 8px;
#                         border: 1px solid #e9ecef;
#                         min-height: 20px;
#                         min-width: 200px;
#                     }
#                 """)
        
#         self.extra_value.setText("Ready to scan QR codes...")
    
#     def update_results(self, data):
#         """Update fields with scanned data"""
#         print("GUI updating results with data:", data)
        
#         # Update main fields
#         for field, value_widget in self.field_values.items():
#             value = data.get(field)
            
#             if value is not None and str(value).strip() and str(value).strip().lower() != 'none':
#                 display_value = str(value)
                
#                 # Color coding for status
#                 if field == 'status':
#                     if value == 'VALID':
#                         color = "#28a745"
#                         bg_color = "#d4edda"
#                     elif value == 'EXPIRED':
#                         color = "#dc3545"
#                         bg_color = "#f8d7da"
#                     else:
#                         color = "#ffc107"
#                         bg_color = "#fff3cd"
#                 else:
#                     color = "#333"
#                     bg_color = "#e8f5e8"
                
#                 value_widget.setText(display_value)
#                 value_widget.setStyleSheet(f"""
#                     QLabel {{
#                         font-size: 16px;
#                         color: {color};
#                         background-color: {bg_color};
#                         padding: 8px 12px;
#                         border-radius: 8px;
#                         border: 1px solid rgba(0,0,0,0.1);
#                         min-height: 20px;
#                         min-width: 200px;
#                         font-weight: bold;
#                     }}
#                 """)
#             else:
#                 # Show "Not provided" for empty fields
#                 value_widget.setText("Not provided")
#                 value_widget.setStyleSheet("""
#                     QLabel {
#                         font-size: 16px;
#                         color: #999;
#                         background-color: #f8f9fa;
#                         padding: 8px 12px;
#                         border-radius: 8px;
#                         border: 1px solid #e9ecef;
#                         min-height: 20px;
#                         min-width: 200px;
#                     }
#                 """)
        
#         # Update extra information
#         extra = data.get('extra', {})
#         if extra and any(str(v).strip() for v in extra.values() if v is not None):
#             extra_text = ""
#             if 'url' in extra:
#                 extra_text = f"🌐 URL: {extra['url']}"
#             elif 'raw' in extra:
#                 extra_text = f"📄 Raw Data: {extra['raw']}"
#             else:
#                 extra_items = []
#                 for k, v in extra.items():
#                     if v and str(v).strip():
#                         extra_items.append(f"{k}: {v}")
#                 extra_text = "\n".join(extra_items)
            
#             self.extra_value.setText(extra_text if extra_text else "Additional data available but empty")
#         else:
#             self.extra_value.setText("No additional information available")

# class MedicineScannerGUI(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.camera_worker = CameraWorker()
#         self.setup_ui()
#         self.setup_connections()
        
#     def setup_ui(self):
#         # Main window setup
#         self.setWindowTitle("💊 HealixQure - Medicine Scanner")
#         self.resize(1200, 800)
#         self.setMinimumSize(1000, 700)
        
#         # Main widget and layout
#         main_widget = QWidget()
#         self.setCentralWidget(main_widget)
#         main_layout = QHBoxLayout(main_widget)
#         main_layout.setSpacing(20)
#         main_layout.setContentsMargins(20, 20, 20, 20)
        
#         # Left panel - Camera view
#         left_panel = QFrame()
#         left_panel.setMaximumWidth(600)
#         left_panel.setStyleSheet("""
#             QFrame {
#                 background-color: white;
#                 border-radius: 15px;
#                 border: 2px solid #e0e0e0;
#                 padding: 20px;
#             }
#         """)
        
#         left_layout = QVBoxLayout(left_panel)
#         left_layout.setSpacing(20)
        
#         # Camera view title
#         camera_title = QLabel("📷 Camera View")
#         camera_title.setStyleSheet("""
#             QLabel {
#                 font-size: 24px;
#                 font-weight: bold;
#                 color: #2c5aa0;
#                 margin-bottom: 10px;
#             }
#         """)
#         left_layout.addWidget(camera_title)
        
#         # Camera display
#         self.camera_label = QLabel("📷 Camera Off")
#         self.camera_label.setFixedSize(540, 400)
#         self.camera_label.setAlignment(Qt.AlignCenter)
#         self.camera_label.setStyleSheet("""
#             QLabel {
#                 background-color: #f8f9fa;
#                 border: 2px dashed #dee2e6;
#                 border-radius: 10px;
#                 font-size: 18px;
#                 color: #6c757d;
#             }
#         """)
#         left_layout.addWidget(self.camera_label)
        
#         # Camera controls
#         controls_layout = QHBoxLayout()
        
#         self.start_button = QPushButton("🎥 Start Camera")
#         self.start_button.setStyleSheet("""
#             QPushButton {
#                 background-color: #28a745;
#                 color: white;
#                 border: none;
#                 border-radius: 8px;
#                 padding: 12px 20px;
#                 font-size: 16px;
#                 font-weight: bold;
#             }
#             QPushButton:hover { background-color: #218838; }
#             QPushButton:pressed { background-color: #1e7e34; }
#         """)
        
#         self.stop_button = QPushButton("⏹️ Stop Camera")
#         self.stop_button.setStyleSheet("""
#             QPushButton {
#                 background-color: #dc3545;
#                 color: white;
#                 border: none;
#                 border-radius: 8px;
#                 padding: 12px 20px;
#                 font-size: 16px;
#                 font-weight: bold;
#             }
#             QPushButton:hover { background-color: #c82333; }
#             QPushButton:pressed { background-color: #bd2130; }
#         """)
#         self.stop_button.setEnabled(False)
        
#         controls_layout.addWidget(self.start_button)
#         controls_layout.addWidget(self.stop_button)
#         left_layout.addLayout(controls_layout)
        
#         # Status indicator
#         self.status_label = QLabel("🔴 Camera: OFF")
#         self.status_label.setStyleSheet("""
#             QLabel {
#                 font-size: 16px;
#                 font-weight: bold;
#                 color: #dc3545;
#                 background-color: #f8f9fa;
#                 padding: 8px 15px;
#                 border-radius: 20px;
#                 border: 1px solid #e9ecef;
#             }
#         """)
#         self.status_label.setAlignment(Qt.AlignCenter)
#         left_layout.addWidget(self.status_label)
        
#         # Right panel - Results
#         self.results_widget = ResultDisplayWidget()
        
#         # Add panels to main layout
#         main_layout.addWidget(left_panel)
#         main_layout.addWidget(self.results_widget)
        
#         # CRITICAL: Set stretch factors to ensure right panel gets space
#         main_layout.setStretch(0, 1)  # Camera panel - normal space
#         main_layout.setStretch(1, 2)  # Results panel - more space
        
#         # Apply global styles
#         self.setStyleSheet("""
#             QMainWindow {
#                 background-color: #f5f6fa;
#             }
#         """)
    
#     def setup_connections(self):
#         self.start_button.clicked.connect(self.start_camera)
#         self.stop_button.clicked.connect(self.stop_camera)
        
#         self.camera_worker.frame_ready.connect(self.update_camera_display)
#         self.camera_worker.qr_detected.connect(self.update_results)
    
#     def start_camera(self):
#         self.camera_worker.start_camera()
#         self.start_button.setEnabled(False)
#         self.stop_button.setEnabled(True)
        
#         self.status_label.setText("🟢 Camera: ON - Ready to Scan")
#         self.status_label.setStyleSheet("""
#             QLabel {
#                 font-size: 16px;
#                 font-weight: bold;
#                 color: #28a745;
#                 background-color: #d4edda;
#                 padding: 8px 15px;
#                 border-radius: 20px;
#                 border: 1px solid #c3e6cb;
#             }
#         """)
        
#         self.camera_label.setText("📷 Starting camera...")
    
#     def stop_camera(self):
#         self.camera_worker.stop_camera()
#         self.start_button.setEnabled(True)
#         self.stop_button.setEnabled(False)
        
#         self.status_label.setText("🔴 Camera: OFF")
#         self.status_label.setStyleSheet("""
#             QLabel {
#                 font-size: 16px;
#                 font-weight: bold;
#                 color: #dc3545;
#                 background-color: #f8f9fa;
#                 padding: 8px 15px;
#                 border-radius: 20px;
#                 border: 1px solid #e9ecef;
#             }
#         """)
        
#         self.camera_label.setText("📷 Camera Off")
#         self.camera_label.setPixmap(QPixmap())
        
#         # Reset to default fields (don't hide them)
#         self.results_widget.show_default_fields()
    
#     def update_camera_display(self, frame):
#         # Convert frame to Qt format and display
#         rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         h, w, ch = rgb_image.shape
#         bytes_per_line = ch * w
        
#         qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
#         # Scale to fit the label
#         pixmap = QPixmap.fromImage(qt_image)
#         scaled_pixmap = pixmap.scaled(
#             self.camera_label.size(), 
#             Qt.KeepAspectRatio, 
#             Qt.SmoothTransformation
#         )
        
#         self.camera_label.setPixmap(scaled_pixmap)
    
#     def update_results(self, data):
#         print("Main window QR Detected:", data)
#         self.results_widget.update_results(data)

# def main():
#     app = QApplication(sys.argv)
#     app.setStyle('Fusion')
    
#     window = MedicineScannerGUI()
#     window.show()
    
#     sys.exit(app.exec())

# if __name__ == '__main__':
#     main()














#!/usr/bin/env python3
"""
Modern Medicine QR Code Scanner GUI with PySide6
Updated with custom color scheme: #e74c3c, black, white, light grey, red/green buttons
Maintains 100% original QR code scanning functionality
"""

import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import cv2
from pyzbar.pyzbar import decode as zbar_decode
from datetime import datetime, date
import re
import xml.etree.ElementTree as ET

# --- Original QR Code Scanning Logic (Complete & Unchanged) ---

AI_MAPPING = {
    '01': ('gtin', 14, True),      # GTIN-14 (fixed length)
    '17': ('expiry', 6, True),     # Expiry date YYMMDD (fixed length)
    '10': ('batch', None, False),  # Batch/lot number (variable length)
    '21': ('serial', None, False)  # Serial number (variable length)
}

def format_expiry(expiry_raw):
    """Format expiry date from YYMMDD to ISO format"""
    if not expiry_raw:
        return None

    # Remove non-digits
    s = re.sub(r'\D', '', expiry_raw)

    try:
        if len(s) == 6:  # YYMMDD
            return datetime.strptime(s, '%y%m%d').date().isoformat()
        elif len(s) == 8:  # YYYYMMDD
            return datetime.strptime(s, '%Y%m%d').date().isoformat()
    except Exception:
        return None

    return None

def check_validity(expiry_iso):
    """Check if medicine is valid based on expiry date"""
    if not expiry_iso:
        return "UNKNOWN"

    try:
        expiry_date = datetime.strptime(expiry_iso, '%Y-%m-%d').date()
        return "VALID" if expiry_date >= date.today() else "EXPIRED"
    except Exception:
        return "UNKNOWN"

def normalize_gtin(g):
    """Normalize GTIN to 14 digits"""
    if not g:
        return None

    digits = re.sub(r'\D', '', str(g))

    if len(digits) == 14:
        return digits
    elif len(digits) == 13:  # EAN-13
        return '0' + digits
    elif len(digits) == 12:  # UPC-A
        return '00' + digits

    return digits if digits else None

def parse_parenthesis_form(s):
    """Parse GS1 data in parenthesis format like (01)12345678901234(17)251231"""
    result = {}

    # Find all (AI)Value pairs
    for ai, val in re.findall(r'\((\d{2,3})\)([^\(]+)', s):
        if ai in AI_MAPPING:
            name, _, _ = AI_MAPPING[ai]
            result[name] = val

    # Format expiry if present
    if 'expiry' in result:
        result['expiry_formatted'] = format_expiry(result['expiry'])

    # Normalize GTIN if present
    if 'gtin' in result:
        result['gtin'] = normalize_gtin(result.get('gtin'))

    return result

def parse_gs1_data(raw):
    """Parse GS1 barcode data"""
    if not raw:
        return {}

    # Normalize separators
    data = raw
    data = data.replace('\\x1D', '\x1D').replace('\\u001d', '\x1D').replace('|GS|', '\x1D')
    data = data.replace('\u001d', '\x1D')

    # Remove GS1 prefix if present
    data = re.sub(r'^\]d2?', '', data, flags=re.IGNORECASE)

    # Handle parenthesis format
    if data.startswith('('):
        return parse_parenthesis_form(data)

    # Parse standard GS1 format
    segments = re.split(r'\x1D', data)
    result = {}

    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue

        i = 0
        L = len(seg)

        while i + 2 <= L:
            ai = seg[i:i+2]

            if ai in AI_MAPPING:
                name, length, fixed = AI_MAPPING[ai]
                i += 2

                # Extract value based on AI definition
                if fixed and length:
                    # Fixed length AI
                    if i + length <= L:
                        val = seg[i:i+length]
                        i += length
                    else:
                        val = seg[i:]
                        i = L
                else:
                    # Variable length AI - read until next AI or end
                    next_match = re.search(r'(' + '|'.join(AI_MAPPING.keys()) + r')', seg[i:])
                    if next_match:
                        next_pos = i + next_match.start()
                        val = seg[i:next_pos]
                        i = next_pos
                    else:
                        val = seg[i:]
                        i = L

                if val:
                    result[name] = val
            else:
                i += 1

    # Post-process results
    if 'expiry' in result and 'expiry_formatted' not in result:
        result['expiry_formatted'] = format_expiry(result['expiry'])

    if 'gtin' in result:
        result['gtin'] = normalize_gtin(result.get('gtin'))

    return result

def interpret_payload(payload):
    """Main function to interpret QR code payload"""
    p = payload.strip()

    # Check for URL scheme
    low = p.lower()
    if low.startswith('http://') or low.startswith('https://'):
        return {
            'scheme': 'URL',
            'gtin': None,
            'expiry_formatted': None,
            'batch': None,
            'serial': None,
            'extra': {'url': p}
        }

    # Check for XML format
    if p.startswith('<') and p.endswith('>'):
        extra = {}
        try:
            root = ET.fromstring(p)
            for child in root:
                tag = child.tag.strip()
                text = child.text.strip() if child.text else ''
                extra[tag] = text
        except Exception as e:
            extra['xml_error'] = str(e)

        return {
            'scheme': 'CUSTOM_XML',
            'gtin': None,
            'expiry_formatted': None,
            'batch': None,
            'serial': None,
            'extra': extra
        }

    # Check for pure digits (EAN/UPC)
    digits = re.sub(r'\D', '', p)
    if digits and len(digits) in (12, 13, 14):
        gt = normalize_gtin(digits)
        return {
            'scheme': 'EAN/UPC',
            'gtin': gt,
            'expiry_formatted': None,
            'batch': None,
            'serial': None,
            'extra': {}
        }

    # Check for GS1 format
    if ('\x1D' in p or '|GS|' in p or 
        re.search(r'\(01\)', p) or 
        re.search(r'01\d{14}', p)):

        parsed = parse_gs1_data(p)
        return {
            'scheme': 'GS1',
            'gtin': parsed.get('gtin'),
            'expiry_formatted': parsed.get('expiry_formatted'),
            'batch': parsed.get('batch'),
            'serial': parsed.get('serial'),
            'extra': {}
        }

    # Default: RAW data
    return {
        'scheme': 'RAW',
        'gtin': None,
        'expiry_formatted': None,
        'batch': None,
        'serial': None,
        'extra': {'raw': p}
    }

def try_decode(frame):
    """Try to decode QR code from camera frame"""
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Try pyzbar first (more reliable)
    r = zbar_decode(gray)
    if r:
        try:
            return r[0].data.decode('utf-8', errors='ignore')
        except:
            return str(r[0].data)

    # Fallback to OpenCV QR detector
    qrd = cv2.QRCodeDetector()
    data, pts, _ = qrd.detectAndDecode(frame)
    if data:
        return data

    return None

# --- Camera Thread for Real-time Processing ---

class CameraThread(QThread):
    frameReady = Signal(object)
    qrDetected = Signal(dict)

    def __init__(self):
        super().__init__()
        self.cap = None
        self.running = False

    def start_camera(self):
        """Initialize and start camera"""
        if self.cap is not None:
            return True

        # Try multiple camera indices and backends
        for idx in [0, 1, 2]:
            for backend in [cv2.CAP_DSHOW, None]:
                try:
                    if backend:
                        self.cap = cv2.VideoCapture(idx, backend)
                    else:
                        self.cap = cv2.VideoCapture(idx)

                    if self.cap.isOpened():
                        # Set camera properties
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.cap.set(cv2.CAP_PROP_FPS, 30)

                        self.running = True
                        self.start()
                        return True
                    else:
                        self.cap.release()
                        self.cap = None
                except Exception:
                    if self.cap:
                        self.cap.release()
                        self.cap = None

        return False

    def stop_camera(self):
        """Stop camera and thread"""
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.quit()
        self.wait()

    def run(self):
        """Main camera loop"""
        last_decode_time = 0

        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Emit frame for display
                self.frameReady.emit(frame)

                # Try to decode QR code (limit frequency to avoid spam)
                current_time = datetime.now().timestamp()
                if current_time - last_decode_time > 1.0:  # 1 second cooldown
                    payload = try_decode(frame)
                    if payload:
                        info = interpret_payload(payload)
                        parsed_output = {
                            'scheme': info.get('scheme'),
                            'gtin': info.get('gtin'),
                            'expiry': info.get('expiry_formatted'),
                            'batch': info.get('batch'),
                            'serial': info.get('serial'),
                            'status': check_validity(info.get('expiry_formatted')),
                            'extra': info.get('extra', {})
                        }
                        self.qrDetected.emit(parsed_output)
                        last_decode_time = current_time

            self.msleep(33)  # ~30 FPS

# --- Main GUI Application ---

class MedicineScanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.camera_thread = CameraThread()
        self.camera_active = False
        self.last_scan_data = None
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("HealixQure Scanner")

        # Enable resizing with minimize/maximize buttons
        self.setMinimumSize(800, 600)
        self.resize(1200, 650)  # Default tablet size but resizable
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | 
                           Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)

        # NEW COLOR SCHEME: #e74c3c (red), black, white, light grey, red/green buttons
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #2c3e50, stop:1 #34495e);
                color: white;
            }
            QWidget {
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border: 2px solid #34495e;
                border-radius: 12px;
                padding: 15px 25px;
                font-size: 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
                border: 2px solid #e74c3c;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #1f618d);
            }
            QLabel {
                border-radius: 8px;
                padding: 10px;
                color: white;
            }
            QFrame {
                border-radius: 15px;
                background: rgba(52, 73, 94, 0.8);
                border: 2px solid #e74c3c;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(44, 62, 80, 0.8);
                width: 12px;
                border-radius: 6px;
                border: 1px solid #e74c3c;
            }
            QScrollBar::handle:vertical {
                background: #e74c3c;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #c0392b;
            }
        """)

        # Central widget setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Setup camera section
        self.setup_camera_section(main_layout)

        # Setup data display section
        self.setup_data_section(main_layout)

    def setup_camera_section(self, main_layout):
        """Setup camera view section"""
        # Camera container frame
        camera_frame = QFrame()
        camera_frame.setMinimumSize(500, 600)  # Responsive sizing
        camera_layout = QVBoxLayout(camera_frame)
        camera_layout.setSpacing(15)

        # Camera section title
        camera_title = QLabel("📱 Camera View")
        camera_title.setAlignment(Qt.AlignCenter)
        camera_title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #e74c3c;
            background: none;
            border: none;
            padding: 10px;
        """)
        camera_layout.addWidget(camera_title)

        # Camera display area
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(400, 300)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("""
            background: rgba(0, 0, 0, 0.7);
            border: 2px dashed #e74c3c;
            border-radius: 10px;
            color: #bdc3c7;
            font-size: 18px;
        """)
        self.camera_label.setText("📹\n\nCamera Off\n\nClick 'Start Camera' to begin scanning")
        camera_layout.addWidget(self.camera_label, alignment=Qt.AlignCenter)

        # Camera control buttons
        controls_layout = QHBoxLayout()

        # Start Camera Button (GREEN)
        self.start_camera_btn = QPushButton("🎥 Start Camera")
        self.start_camera_btn.setFixedSize(180, 50)
        self.start_camera_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                border: 2px solid #2ecc71;
                border-radius: 12px;
                padding: 15px 25px;
                font-size: 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
                border: 2px solid #e74c3c;
            }
        """)
        self.start_camera_btn.clicked.connect(self.toggle_camera)

        # Clear Data Button (RED)
        self.clear_data_btn = QPushButton("🗑️ Clear Data")
        self.clear_data_btn.setFixedSize(180, 50)
        self.clear_data_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                border: 2px solid #e74c3c;
                border-radius: 12px;
                padding: 15px 25px;
                font-size: 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:1 #e74c3c);
                border: 2px solid #2ecc71;
            }
        """)
        self.clear_data_btn.clicked.connect(self.clear_scan_data)

        controls_layout.addWidget(self.start_camera_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.clear_data_btn)

        camera_layout.addLayout(controls_layout)
        camera_layout.addStretch()

        main_layout.addWidget(camera_frame)

    def setup_data_section(self, main_layout):
        """Setup data display section"""
        # Data display container frame
        data_frame = QFrame()
        data_frame.setMinimumSize(450, 600)  # Responsive sizing
        data_layout = QVBoxLayout(data_frame)
        data_layout.setSpacing(15)

        # Data section title
        data_title = QLabel("📊 HealixQure Scan Report")
        data_title.setAlignment(Qt.AlignCenter)
        data_title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #e74c3c;
            background: none;
            border: none;
            padding: 10px;
        """)
        data_layout.addWidget(data_title)

        # Scrollable area for data display
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.data_widget = QWidget()
        self.data_layout = QVBoxLayout(self.data_widget)
        self.data_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.data_widget)

        # Initial message
        self.show_no_data_message()

        data_layout.addWidget(scroll)
        main_layout.addWidget(data_frame)

    def setup_connections(self):
        """Connect signals and slots"""
        self.camera_thread.frameReady.connect(self.update_camera_frame)
        self.camera_thread.qrDetected.connect(self.display_scan_result)

    def toggle_camera(self):
        """Toggle camera on/off"""
        if not self.camera_active:
            if self.camera_thread.start_camera():
                self.camera_active = True
                self.start_camera_btn.setText("⏹️ Stop Camera")
                self.start_camera_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #e74c3c, stop:1 #c0392b);
                        border: 2px solid #e74c3c;
                        border-radius: 12px;
                        padding: 15px 25px;
                        font-size: 16px;
                        font-weight: bold;
                        color: white;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #ec7063, stop:1 #e74c3c);
                        border: 2px solid #2ecc71;
                    }
                """)
            else:
                QMessageBox.warning(self, "Camera Error", 
                    "Failed to start camera. Please check if camera is available and not in use by another application.")
        else:
            self.camera_thread.stop_camera()
            self.camera_active = False
            self.start_camera_btn.setText("🎥 Start Camera")
            # Reset to green start camera button
            self.start_camera_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #27ae60, stop:1 #229954);
                    border: 2px solid #2ecc71;
                    border-radius: 12px;
                    padding: 15px 25px;
                    font-size: 16px;
                    font-weight: bold;
                    color: white;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2ecc71, stop:1 #27ae60);
                    border: 2px solid #e74c3c;
                }
            """)
            self.camera_label.setText("📹\n\nCamera Off\n\nClick 'Start Camera' to begin scanning")

    def update_camera_frame(self, frame):
        """Update camera display with new frame"""
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

        # Scale to fit display area while maintaining aspect ratio
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.camera_label.setPixmap(scaled_pixmap)

    def display_scan_result(self, data):
        """Display QR code scan results"""
        if data == self.last_scan_data:
            return  # Avoid duplicate displays

        self.last_scan_data = data
        self.clear_data_layout()

        # Display scheme information
        self.create_data_field("Scheme", data.get('scheme'), "🏷️")

        # Display medicine status
        self.create_status_field(data.get('status'))

        # Display GTIN if available
        if data.get('gtin'):
            self.create_data_field("GTIN Number", data.get('gtin'), "🔢")
        else:
            self.create_no_data_field("GTIN Number")

        # Display expiry date if available
        if data.get('expiry'):
            self.create_data_field("Expiry Date", data.get('expiry'), "📅")
        else:
            self.create_no_data_field("Expiry Date")

        # Display batch number if available
        if data.get('batch'):
            self.create_data_field("Batch Number", data.get('batch'), "📦")
        else:
            self.create_no_data_field("Batch Number")

        # Display serial number if available
        if data.get('serial'):
            self.create_data_field("Serial Number", data.get('serial'), "🔐")
        else:
            self.create_no_data_field("Serial Number")

        # Show extra data if available
        extra = data.get('extra', {})
        if extra:
            self.create_extra_data_section(extra)

        self.data_layout.addStretch()

    def create_data_field(self, field_name, value, icon):
        """Create a data field widget"""
        field_frame = QFrame()
        field_frame.setStyleSheet("""
            QFrame {
                background: rgba(44, 62, 80, 0.9);
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                padding: 10px;
                margin: 5px 0;
            }
        """)

        layout = QVBoxLayout(field_frame)
        layout.setSpacing(5)

        # Field name with icon
        name_label = QLabel(f"{icon} {field_name}")
        name_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #e74c3c;
            background: none;
            border: none;
            padding: 0;
        """)

        # Field value
        value_label = QLabel(str(value))
        value_label.setStyleSheet("""
            font-size: 16px;
            color: white;
            background: none;
            border: none;
            padding: 5px;
        """)
        value_label.setWordWrap(True)

        layout.addWidget(name_label)
        layout.addWidget(value_label)

        self.data_layout.addWidget(field_frame)

    def create_status_field(self, status):
        """Create status field with color coding"""
        field_frame = QFrame()

        # Color coding based on status
        if status == "VALID":
            color = "#27ae60"
            bg_color = "rgba(39, 174, 96, 0.2)"
            border_color = "#2ecc71"
            icon = "✅"
        elif status == "EXPIRED":
            color = "#e74c3c"
            bg_color = "rgba(231, 76, 60, 0.2)"
            border_color = "#e74c3c"
            icon = "❌"
        else:  # UNKNOWN
            color = "#f39c12"
            bg_color = "rgba(243, 156, 18, 0.2)"
            border_color = "#f39c12"
            icon = "❓"

        field_frame.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 10px;
                padding: 10px;
                margin: 5px 0;
            }}
        """)

        layout = QVBoxLayout(field_frame)
        layout.setSpacing(5)

        name_label = QLabel("🏥 Medicine Status")
        name_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {color};
            background: none;
            border: none;
            padding: 0;
        """)

        value_label = QLabel(f"{icon} {status}")
        value_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {color};
            background: none;
            border: none;
            padding: 5px;
        """)

        layout.addWidget(name_label)
        layout.addWidget(value_label)

        self.data_layout.addWidget(field_frame)

    def create_no_data_field(self, field_name):
        """Create field widget for missing data"""
        field_frame = QFrame()
        field_frame.setStyleSheet("""
            QFrame {
                background: rgba(127, 140, 141, 0.3);
                border: 2px solid #95a5a6;
                border-radius: 10px;
                padding: 10px;
                margin: 5px 0;
            }
        """)

        layout = QVBoxLayout(field_frame)
        layout.setSpacing(5)

        name_label = QLabel(f"⚪ {field_name}")
        name_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #95a5a6;
            background: none;
            border: none;
            padding: 0;
        """)

        value_label = QLabel("Data not available in QR code")
        value_label.setStyleSheet("""
            font-size: 14px;
            color: #bdc3c7;
            background: none;
            border: none;
            padding: 5px;
            font-style: italic;
        """)

        layout.addWidget(name_label)
        layout.addWidget(value_label)

        self.data_layout.addWidget(field_frame)

    def create_extra_data_section(self, extra):
        """Create section for additional data"""
        extra_frame = QFrame()
        extra_frame.setStyleSheet("""
            QFrame {
                background: rgba(155, 89, 182, 0.2);
                border: 2px solid #9b59b6;
                border-radius: 10px;
                padding: 10px;
                margin: 10px 0;
            }
        """)

        layout = QVBoxLayout(extra_frame)
        layout.setSpacing(5)

        title_label = QLabel("🔍 Additional Data")
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #9b59b6;
            background: none;
            border: none;
            padding: 0;
        """)
        layout.addWidget(title_label)

        # Format extra data
        if 'url' in extra:
            content = f"URL: {extra['url']}"
        elif 'raw' in extra:
            content = f"Raw Data: {str(extra['raw'])[:100]}{'...' if len(str(extra['raw'])) > 100 else ''}"
        else:
            extra_items = [f"{k}: {v}" for k, v in extra.items()]
            content = " | ".join(extra_items)
            if len(content) > 200:
                content = content[:200] + "..."

        content_label = QLabel(content)
        content_label.setStyleSheet("""
            font-size: 12px;
            color: #ecf0f1;
            background: none;
            border: none;
            padding: 5px;
        """)
        content_label.setWordWrap(True)
        layout.addWidget(content_label)

        self.data_layout.addWidget(extra_frame)

    def show_no_data_message(self):
        """Show initial message when no data is scanned"""
        no_data_label = QLabel("""
            <div style="text-align: center; color: #bdc3c7; padding: 50px;">
                <h2 style="color: #e74c3c;">📱 Ready to Scan</h2>
                <p style="font-size: 16px; margin: 20px 0; color: white;">
                    Start the camera and point it at a medicine QR code <br>to see detailed information here.
                </p>
                <p style="font-size: 14px; color: #95a5a6;">
                    The scanner will automatically detect and parse:<br/>
                    • GS1 barcodes with medicine data<br/>
                    • EAN/UPC product codes<br/>
                    • Custom XML data<br/>
                    • URLs and other QR code formats
                </p>
            </div>
        """)
        no_data_label.setAlignment(Qt.AlignCenter)
        no_data_label.setStyleSheet("background: none; border: none;")
        self.data_layout.addWidget(no_data_label)

    def clear_data_layout(self):
        """Clear all widgets from data layout"""
        while self.data_layout.count():
            child = self.data_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def clear_scan_data(self):
        """Clear scan data and show initial message"""
        self.last_scan_data = None
        self.clear_data_layout()
        self.show_no_data_message()

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        # Camera display adapts automatically with the resize

    def closeEvent(self, event):
        """Handle application close"""
        if self.camera_active:
            self.camera_thread.stop_camera()
        event.accept()

# --- Main Application Entry Point ---

def main():
    """Main application function"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Medicine QR Code Scanner")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Medical Scanner Solutions")

    # Create and show main window
    window = MedicineScanner()
    window.show()

    # Center window on screen
    screen = app.primaryScreen().geometry()
    window.move(
        (screen.width() - window.width()) // 2,
        (screen.height() - window.height()) // 2
    )

    # Run application
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
