# import sys
# from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
#                                QHBoxLayout, QLineEdit, QPushButton, QLabel, 
#                                QFrame)
# from PySide6.QtCore import Qt
# from PySide6.QtGui import QPainter, QColor, QLinearGradient
# # Import the main ChatBot application
# from App import ChatBotMainWindow

# class BackgroundWidget(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setMinimumSize(800, 600)
        
#     def paintEvent(self, event):
#         painter = QPainter(self)
#         painter.setRenderHint(QPainter.Antialiasing)
        
#         # Create gradient background
#         gradient = QLinearGradient(0, 0, self.width(), self.height())
#         gradient.setColorAt(0, QColor(45, 52, 78))  # Dark blue
#         gradient.setColorAt(0.5, QColor(62, 71, 107))  # Medium blue
#         gradient.setColorAt(1, QColor(88, 67, 134))  # Purple
        
#         painter.fillRect(self.rect(), gradient)
        
#         # Draw decorative geometric shapes
#         self.draw_decorative_shapes(painter)
        
#     def draw_decorative_shapes(self, painter):
#         # Set opacity for decorative elements
#         painter.setOpacity(0.3)
        
#         # Draw circles
#         painter.setBrush(QColor(255, 255, 255, 30))
#         painter.setPen(Qt.NoPen)
        
#         # Large circle
#         painter.drawEllipse(50, 300, 150, 150)
        
#         # Medium circles
#         painter.drawEllipse(600, 100, 100, 100)
#         painter.drawEllipse(650, 400, 80, 80)
        
#         # Small circles
#         painter.drawEllipse(200, 150, 60, 60)
#         painter.drawEllipse(500, 500, 40, 40)
        
#         # Draw rounded rectangles
#         painter.setBrush(QColor(255, 255, 255, 25))
#         painter.drawRoundedRect(700, 200, 80, 200, 40, 40)
#         painter.drawRoundedRect(100, 100, 60, 120, 30, 30)
        
#         # Draw stars
#         painter.setOpacity(0.6)
#         painter.setBrush(QColor(255, 255, 255))
#         self.draw_star(painter, 150, 100, 3)
#         self.draw_star(painter, 680, 150, 2)
#         self.draw_star(painter, 300, 50, 2.5)
#         self.draw_star(painter, 450, 450, 2)
        
#     def draw_star(self, painter, x, y, size):
#         # Simple star drawing
#         painter.drawEllipse(int(x-size), int(y-size), int(size*2), int(size*2))

# class LoginWidget(QFrame):
#     def __init__(self):
#         super().__init__()
#         self.setup_ui()
        
#     def setup_ui(self):
#         self.setFixedSize(400, 320)
#         self.setStyleSheet("""
#             QFrame {
#                 background-color: rgba(35, 42, 68, 0.9);
#                 border-radius: 15px;
#                 border: 1px solid rgba(255, 255, 255, 0.1);
#             }
#         """)
        
#         layout = QVBoxLayout(self)
#         layout.setSpacing(25)
#         layout.setContentsMargins(40, 40, 40, 40)
        
#         # Logo/Title - Changed to HealixQure
#         title = QLabel("HealixQure")
#         title.setStyleSheet("""
#             QLabel {
#                 color: white;
#                 font-size: 32px;
#                 font-weight: bold;
#                 font-family: Arial, sans-serif;
#                 background: transparent;
#                 border: none;
#             }
#         """)
#         title.setAlignment(Qt.AlignCenter)
#         layout.addWidget(title)
        
#         # Added extra spacing between title and input fields (increased from 20 to 40)
#         layout.addSpacing(40)
        
#         # Email input - Removed default value
#         self.email_input = QLineEdit()
#         self.email_input.setPlaceholderText("Email or Username")
#         self.email_input.setStyleSheet("""
#             QLineEdit {
#                 background-color: rgba(255, 255, 255, 0.1);
#                 border: 1px solid rgba(255, 255, 255, 0.2);
#                 border-radius: 8px;
#                 padding: 12px 15px;
#                 color: white;
#                 font-size: 14px;
#                 font-family: Arial, sans-serif;
#             }
#             QLineEdit:focus {
#                 border: 1px solid rgba(255, 255, 255, 0.4);
#                 background-color: rgba(255, 255, 255, 0.15);
#             }
#             QLineEdit::placeholder {
#                 color: rgba(255, 255, 255, 0.6);
#             }
#         """)
#         self.email_input.setMinimumHeight(45)
#         layout.addWidget(self.email_input)
        
#         # Password input - Removed default value
#         self.password_input = QLineEdit()
#         self.password_input.setPlaceholderText("Password")
#         self.password_input.setEchoMode(QLineEdit.Password)
#         self.password_input.setStyleSheet("""
#             QLineEdit {
#                 background-color: rgba(255, 255, 255, 0.1);
#                 border: 1px solid rgba(255, 255, 255, 0.2);
#                 border-radius: 8px;
#                 padding: 12px 15px;
#                 color: white;
#                 font-size: 14px;
#                 font-family: Arial, sans-serif;
#             }
#             QLineEdit:focus {
#                 border: 1px solid rgba(255, 255, 255, 0.4);
#                 background-color: rgba(255, 255, 255, 0.15);
#             }
#             QLineEdit::placeholder {
#                 color: rgba(255, 255, 255, 0.6);
#             }
#         """)
#         self.password_input.setMinimumHeight(45)
#         layout.addWidget(self.password_input)
        
#         layout.addSpacing(15)
        
#         # Login button
#         self.login_button = QPushButton("LOG IN")
#         self.login_button.setStyleSheet("""
#             QPushButton {
#                 background-color: white;
#                 color: #2d3a4e;
#                 border: none;
#                 border-radius: 25px;
#                 padding: 12px 0px;
#                 font-size: 14px;
#                 font-weight: bold;
#                 font-family: Arial, sans-serif;
#             }
#             QPushButton:hover {
#                 background-color: rgba(255, 255, 255, 0.9);
#             }
#             QPushButton:pressed {
#                 background-color: rgba(255, 255, 255, 0.8);
#             }
#         """)
#         self.login_button.setMinimumHeight(50)
#         self.login_button.clicked.connect(self.login_clicked)
#         layout.addWidget(self.login_button)
        
#         # Removed forgot password link completely
        
#     def login_clicked(self):
#         username = self.email_input.text()
#         password = self.password_input.text()
#         print(f"Login attempted with Username: {username}, Password: {password}")
        
#         # You can add your login logic here
#         if username == "Vishal" and password == "123":
#             print("Login successful!")
#         else:
#             print("Please enter both username and password")

# class HealixQureLoginApp(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setup_ui()
        
#     def setup_ui(self):
#         self.setWindowTitle("HealixQure Login")
#         # Changed from setFixedSize to resize to allow window resizing
#         self.resize(800, 600)
#         self.setMinimumSize(600, 450)  # Set minimum size for usability
        
#         # Central widget with background
#         central_widget = BackgroundWidget()
#         self.setCentralWidget(central_widget)
        
#         # Main layout
#         main_layout = QVBoxLayout(central_widget)
#         main_layout.setAlignment(Qt.AlignCenter)
        
#         # Login widget
#         login_widget = LoginWidget()
#         main_layout.addWidget(login_widget, alignment=Qt.AlignCenter)

# def main():
#     app = QApplication(sys.argv)
    
#     # Set application style
#     app.setStyle('Fusion')
    
#     window = HealixQureLoginApp()
#     window.show()
    
#     sys.exit(app.exec())

# if __name__ == "__main__":
#     main()













# import sys
# from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
#                                QHBoxLayout, QLineEdit, QPushButton, QLabel, 
#                                QFrame, QMessageBox)
# from PySide6.QtCore import Qt
# from PySide6.QtGui import QPainter, QColor, QLinearGradient



# class BackgroundWidget(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setMinimumSize(800, 600)
        
#     def paintEvent(self, event):
#         painter = QPainter(self)
#         painter.setRenderHint(QPainter.Antialiasing)
        
#         # Create gradient background
#         gradient = QLinearGradient(0, 0, self.width(), self.height())
#         gradient.setColorAt(0, QColor(45, 52, 78))  # Dark blue
#         gradient.setColorAt(0.5, QColor(62, 71, 107))  # Medium blue
#         gradient.setColorAt(1, QColor(88, 67, 134))  # Purple
        
#         painter.fillRect(self.rect(), gradient)
        
#         # Draw decorative geometric shapes
#         self.draw_decorative_shapes(painter)
        
#     def draw_decorative_shapes(self, painter):
#         # Set opacity for decorative elements
#         painter.setOpacity(0.3)
        
#         # Draw circles
#         painter.setBrush(QColor(255, 255, 255, 30))
#         painter.setPen(Qt.NoPen)
        
#         # Large circle
#         painter.drawEllipse(50, 300, 150, 150)
        
#         # Medium circles
#         painter.drawEllipse(600, 100, 100, 100)
#         painter.drawEllipse(650, 400, 80, 80)
        
#         # Small circles
#         painter.drawEllipse(200, 150, 60, 60)
#         painter.drawEllipse(500, 500, 40, 40)
        
#         # Draw rounded rectangles
#         painter.setBrush(QColor(255, 255, 255, 25))
#         painter.drawRoundedRect(700, 200, 80, 200, 40, 40)
#         painter.drawRoundedRect(100, 100, 60, 120, 30, 30)
        
#         # Draw stars
#         painter.setOpacity(0.6)
#         painter.setBrush(QColor(255, 255, 255))
#         self.draw_star(painter, 150, 100, 3)
#         self.draw_star(painter, 680, 150, 2)
#         self.draw_star(painter, 300, 50, 2.5)
#         self.draw_star(painter, 450, 450, 2)
        
#     def draw_star(self, painter, x, y, size):
#         # Simple star drawing
#         painter.drawEllipse(int(x-size), int(y-size), int(size*2), int(size*2))

# class LoginWidget(QFrame):
#     def __init__(self):
#         super().__init__()
#         self.main_app = None  # Will hold reference to main app
#         self.setup_ui()
        
#     def setup_ui(self):
#         self.setFixedSize(400, 320)
#         self.setStyleSheet("""
#             QFrame {
#                 background-color: rgba(35, 42, 68, 0.9);
#                 border-radius: 15px;
#                 border: 1px solid rgba(255, 255, 255, 0.1);
#             }
#         """)
        
#         layout = QVBoxLayout(self)
#         layout.setSpacing(25)
#         layout.setContentsMargins(40, 40, 40, 40)
        
#         # Logo/Title - Changed to HealixQure
#         title = QLabel("HealixQure")
#         title.setStyleSheet("""
#             QLabel {
#                 color: white;
#                 font-size: 32px;
#                 font-weight: bold;
#                 font-family: Arial, sans-serif;
#                 background: transparent;
#                 border: none;
#             }
#         """)
#         title.setAlignment(Qt.AlignCenter)
#         layout.addWidget(title)
        
#         # Added extra spacing between title and input fields
#         layout.addSpacing(40)
        
#         # Email input - Removed default value
#         self.email_input = QLineEdit()
#         self.email_input.setPlaceholderText("Email or Username")
#         self.email_input.setStyleSheet("""
#             QLineEdit {
#                 background-color: rgba(255, 255, 255, 0.1);
#                 border: 1px solid rgba(255, 255, 255, 0.2);
#                 border-radius: 8px;
#                 padding: 12px 15px;
#                 color: white;
#                 font-size: 14px;
#                 font-family: Arial, sans-serif;
#             }
#             QLineEdit:focus {
#                 border: 1px solid rgba(255, 255, 255, 0.4);
#                 background-color: rgba(255, 255, 255, 0.15);
#             }
#             QLineEdit::placeholder {
#                 color: rgba(255, 255, 255, 0.6);
#             }
#         """)
#         self.email_input.setMinimumHeight(45)
#         layout.addWidget(self.email_input)
        
#         # Password input - Removed default value
#         self.password_input = QLineEdit()
#         self.password_input.setPlaceholderText("Password")
#         self.password_input.setEchoMode(QLineEdit.Password)
#         self.password_input.setStyleSheet("""
#             QLineEdit {
#                 background-color: rgba(255, 255, 255, 0.1);
#                 border: 1px solid rgba(255, 255, 255, 0.2);
#                 border-radius: 8px;
#                 padding: 12px 15px;
#                 color: white;
#                 font-size: 14px;
#                 font-family: Arial, sans-serif;
#             }
#             QLineEdit:focus {
#                 border: 1px solid rgba(255, 255, 255, 0.4);
#                 background-color: rgba(255, 255, 255, 0.15);
#             }
#             QLineEdit::placeholder {
#                 color: rgba(255, 255, 255, 0.6);
#             }
#         """)
#         self.password_input.setMinimumHeight(45)
#         layout.addWidget(self.password_input)
        
#         layout.addSpacing(15)
        
#         # Login button
#         self.login_button = QPushButton("LOG IN")
#         self.login_button.setStyleSheet("""
#             QPushButton {
#                 background-color: white;
#                 color: #2d3a4e;
#                 border: none;
#                 border-radius: 25px;
#                 padding: 12px 0px;
#                 font-size: 14px;
#                 font-weight: bold;
#                 font-family: Arial, sans-serif;
#             }
#             QPushButton:hover {
#                 background-color: rgba(255, 255, 255, 0.9);
#             }
#             QPushButton:pressed {
#                 background-color: rgba(255, 255, 255, 0.8);
#             }
#         """)
#         self.login_button.setMinimumHeight(50)
#         self.login_button.clicked.connect(self.login_clicked)
#         layout.addWidget(self.login_button)
        
#         # Connect Enter key to login
#         self.email_input.returnPressed.connect(self.login_clicked)
#         self.password_input.returnPressed.connect(self.login_clicked)
        
#     def login_clicked(self):
#         username = self.email_input.text().strip()
#         password = self.password_input.text().strip()
#         print(f"Login attempted with Username: {username}, Password: {password}")
        
#         # Check credentials
#         if username == "Vishal" and password == "123":
#             print("Login successful!")
#             self.open_main_application()
#         else:
#             # Show error message
#             self.show_error_message("Username and password are incorrect")
#             print("Username and password are incorrect")
    
#     def open_main_application(self):
#         """Open the main ChatBot application and close login window"""
#         try:
#             # Dynamic import to avoid circular import
#             from App import ChatBotMainWindow
            
#             # Create main application window
#             self.main_app = ChatBotMainWindow()
#             self.main_app.show()
            
#             # Close the login window
#             self.parent().parent().close()  # Close the main login window
            
#             print("Main application opened successfully")
#         except Exception as e:
#             print(f"Error opening main application: {e}")
#             self.show_error_message("Error opening application. Please try again.")

    
#     def show_error_message(self, message):
#         """Display error message to user"""
#         msg_box = QMessageBox()
#         msg_box.setIcon(QMessageBox.Warning)
#         msg_box.setWindowTitle("Login Error")
#         msg_box.setText(message)
#         msg_box.setStyleSheet("""
#             QMessageBox {
#                 background-color: white;
#                 color: black;
#             }
#             QMessageBox QPushButton {
#                 background-color: #2c2c2c;
#                 color: white;
#                 border: none;
#                 border-radius: 5px;
#                 padding: 8px 16px;
#                 min-width: 60px;
#             }
#             QMessageBox QPushButton:hover {
#                 background-color: #404040;
#             }
#         """)
#         msg_box.exec()

# class HealixQureLoginApp(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setup_ui()
        
#     def setup_ui(self):
#         self.setWindowTitle("HealixQure Login")
#         # Changed from setFixedSize to resize to allow window resizing
#         self.resize(800, 600)
#         self.setMinimumSize(600, 450)  # Set minimum size for usability
        
#         # Central widget with background
#         central_widget = BackgroundWidget()
#         self.setCentralWidget(central_widget)
        
#         # Main layout
#         main_layout = QVBoxLayout(central_widget)
#         main_layout.setAlignment(Qt.AlignCenter)
        
#         # Login widget
#         login_widget = LoginWidget()
#         main_layout.addWidget(login_widget, alignment=Qt.AlignCenter)

# def main():
#     app = QApplication(sys.argv)
    
#     # Set application style
#     app.setStyle('Fusion')
    
#     window = HealixQureLoginApp()
#     window.show()
    
#     sys.exit(app.exec())

# if __name__ == "__main__":
#     main()





import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                               QFrame, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QLinearGradient


class BackgroundWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create gradient background with #e74c3c (red) theme
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(231, 76, 60))  # Primary red #e74c3c
        gradient.setColorAt(0.3, QColor(192, 57, 43))  # Darker red #c0392b
        gradient.setColorAt(0.7, QColor(169, 50, 38))  # Even darker red
        gradient.setColorAt(1, QColor(44, 62, 80))  # Dark blue-grey accent #2c3e50

        painter.fillRect(self.rect(), gradient)

        # Draw decorative geometric shapes
        self.draw_decorative_shapes(painter)

    def draw_decorative_shapes(self, painter):
        # Set opacity for decorative elements
        painter.setOpacity(0.2)

        # Draw circles with white/black accents
        painter.setBrush(QColor(255, 255, 255, 40))  # White transparent
        painter.setPen(Qt.NoPen)

        # Large circle
        painter.drawEllipse(50, 300, 150, 150)

        # Medium circles
        painter.drawEllipse(600, 100, 100, 100)
        painter.drawEllipse(650, 400, 80, 80)

        # Small circles
        painter.drawEllipse(200, 150, 60, 60)
        painter.drawEllipse(500, 500, 40, 40)

        # Draw rounded rectangles with black accents
        painter.setBrush(QColor(0, 0, 0, 30))  # Black transparent
        painter.drawRoundedRect(700, 200, 80, 200, 40, 40)
        painter.drawRoundedRect(100, 100, 60, 120, 30, 30)

        # Draw additional white accents
        painter.setBrush(QColor(255, 255, 255, 35))
        painter.drawRoundedRect(400, 80, 60, 100, 30, 30)
        painter.drawRoundedRect(50, 50, 80, 60, 25, 25)

        # Draw stars with higher opacity
        painter.setOpacity(0.4)
        painter.setBrush(QColor(255, 255, 255))
        self.draw_star(painter, 150, 100, 3)
        self.draw_star(painter, 680, 150, 2)
        self.draw_star(painter, 300, 50, 2.5)
        self.draw_star(painter, 450, 450, 2)

    def draw_star(self, painter, x, y, size):
        # Simple star drawing
        painter.drawEllipse(int(x-size), int(y-size), int(size*2), int(size*2))


class LoginWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.main_app = None  # Will hold reference to main app
        self.setup_ui()

    def setup_ui(self):
        self.setFixedSize(400, 320)
        # FIXED: Removed unsupported box-shadow property
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                border: 2px solid rgba(231, 76, 60, 0.4);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(40, 40, 40, 40)

        # Logo/Title - HealixQure with red color
        title = QLabel("HealixQure")
        title.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 32px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                background: transparent;
                border: none;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Added extra spacing between title and input fields
        layout.addSpacing(40)

        # Email input - Updated for light theme
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email or Username")
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 12px 15px;
                color: #212529;
                font-size: 14px;
                font-family: Arial, sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #e74c3c;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #6c757d;
            }
        """)
        self.email_input.setMinimumHeight(45)
        layout.addWidget(self.email_input)

        # Password input - Updated for light theme
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 12px 15px;
                color: #212529;
                font-size: 14px;
                font-family: Arial, sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #e74c3c;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #6c757d;
            }
        """)
        self.password_input.setMinimumHeight(45)
        layout.addWidget(self.password_input)

        layout.addSpacing(15)

        # Login button - Red theme with white text
        self.login_button = QPushButton("LOG IN")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 12px 0px;
                font-size: 14px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.login_button.setMinimumHeight(50)
        self.login_button.clicked.connect(self.login_clicked)
        layout.addWidget(self.login_button)

        # Connect Enter key to login
        self.email_input.returnPressed.connect(self.login_clicked)
        self.password_input.returnPressed.connect(self.login_clicked)

    def login_clicked(self):
        username = self.email_input.text().strip()
        password = self.password_input.text().strip()
        print(f"Login attempted with Username: {username}, Password: {password}")

        # Check credentials Priyanshu,@Pranshu0512
        if username == "admin" and password == "admin":
            print("Login successful!")
            self.open_main_application()
        else:
            # Show error message
            self.show_error_message("Username and password are incorrect")
            print("Username and password are incorrect")

    def open_main_application(self):
        """Open the main ChatBot application and close login window"""
        try:
            # Dynamic import to avoid circular import
            from App import ChatBotMainWindow

            # Create main application window
            self.main_app = ChatBotMainWindow()
            self.main_app.show()

            # Close the login window
            self.parent().parent().close()  # Close the main login window

            print("Main application opened successfully")
        except Exception as e:
            print(f"Error opening main application: {e}")
            self.show_error_message("Error opening application. Please try again.")

    def show_error_message(self, message):
        """Display error message to user with red theme"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Login Error")
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
                color: #212529;
            }
            QMessageBox QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                min-width: 60px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        msg_box.exec()


class HealixQureLoginApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("HealixQure Login")
        # Changed from setFixedSize to resize to allow window resizing
        self.resize(800, 600)
        self.setMinimumSize(600, 450)  # Set minimum size for usability

        # Central widget with background
        central_widget = BackgroundWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignCenter)

        # Login widget
        login_widget = LoginWidget()
        main_layout.addWidget(login_widget, alignment=Qt.AlignCenter)


def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = HealixQureLoginApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
