import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QTextEdit, QPushButton, QLabel,
                               QFrame, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

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
        # Adjusted margins to center content higher up like Google's search page
        main_layout.setContentsMargins(80, 60, 80, 120)  
        main_layout.setSpacing(20)  
        main_layout.setAlignment(Qt.AlignCenter)

        # Add small top spacer to position content in upper-middle area
        top_spacer = QSpacerItem(20, 80, QSizePolicy.Minimum, QSizePolicy.Fixed)
        main_layout.addItem(top_spacer)

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
        self.input_container.setFixedWidth(650)
        self.input_container.setMinimumHeight(100)  # Initial height
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
        input_layout.setContentsMargins(10, 8, 8, 8)  # Minimized container margins
        input_layout.setSpacing(8)

        # Auto-resizing text input with minimal internal padding
        self.text_input = AutoResizeTextEdit()
        self.text_input.setPlaceholderText("Ask anything")
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

        # Logout button - added to the left of send button
        self.logout_button = QPushButton("🕸️")
        self.logout_button.setFixedSize(70, 38)
        self.logout_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: white;
                border: none;
                border-radius: 50px;
                font-size: 23px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: none;
            }
            QPushButton:pressed {
                background-color: #F2EBEB;
            }
        """)
        self.logout_button.clicked.connect(self.logout_clicked)
        input_layout.addWidget(self.logout_button)

        # Send button - made smaller
        self.send_button = QPushButton("↗")
        self.send_button.setFixedSize(38, 38)  # Reduced from 45x45 to 38x38
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2c;
                color: white;
                border: none;
                border-radius: 19px;
                font-size: 16px;
                font-weight: bold;
                font-family: Arial;
            }
            QPushButton:hover {
                background-color: #404040;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        main_layout.addWidget(self.input_container, alignment=Qt.AlignCenter)

        # Larger bottom spacer to push content up
        bottom_spacer = QSpacerItem(20, 200, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(bottom_spacer)

    def send_message(self):
        message = self.text_input.toPlainText().strip()
        if message:
            print(f"Sending message: {message}")
            self.text_input.clear()
            # Reset container height after clearing
            self.input_container.setMinimumHeight(100)
        else:
            print("Please enter a message")

    def logout_clicked(self):
        print("Logout button clicked")
        # Add your logout logic here

class ChatBotMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("💊 HealixQure")
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

        # Add logout button to the left side
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

    def scan_clicked(self):
        print("Scan button clicked")

    def logout_clicked(self):
        print("Logout button clicked from top bar")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ChatBotMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
