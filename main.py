import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QFileDialog, QMessageBox, QTextBrowser
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer, QPoint
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient, QBrush, QPixmap, QFontDatabase
import markdown
import sys
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QUrl, QByteArray

class FileBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Browser")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        self.folder_path = ""
        self.files = []
        self.current_index = 0
        self.config_dir = os.path.expanduser("~/.config/markdown-keep-or-delete")
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # For the sloth popup
        self.files_viewed_since_popup = 0

        # Top toolbar with Open Folder button
        self.toolbar_layout = QHBoxLayout()
        self.open_folder_button = QPushButton("📁 Open Folder")
        self.open_folder_button.setStyleSheet("""
            QPushButton {
                background-color: #4a86e8; color: white; font-weight: bold; padding: 8px 16px;
                border-radius: 4px; font-size: 14px;
            }
            QPushButton:hover { background-color: #3a76d8; }
        """)
        self.open_folder_button.clicked.connect(self.browse_folder)
        self.toolbar_layout.addWidget(self.open_folder_button)
        self.toolbar_layout.addStretch(1)  # Push button to the left
        self.layout.addLayout(self.toolbar_layout)

        # File title
        self.file_title = QLabel("Select a folder to begin")
        self.file_title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.file_title.setFont(font)
        self.layout.addWidget(self.file_title)

        # Progress indicator
        self.progress_indicator = QLabel("No files loaded")
        self.progress_indicator.setAlignment(Qt.AlignCenter)
        progress_font = QFont()
        progress_font.setPointSize(12)
        self.progress_indicator.setFont(progress_font)
        self.layout.addWidget(self.progress_indicator)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #bdbdbd; border-radius: 5px; background-color: #f5f5f5; height: 20px; }
            QProgressBar::chunk { background-color: #4a86e8; border-radius: 5px; }
        """)
        self.layout.addWidget(self.progress_bar)
        # Content display - using QTextBrowser for HTML rendering
        self.content_display = QTextBrowser()
        self.content_display.setOpenExternalLinks(True)
        self.layout.addWidget(self.content_display, 1)

        # Navigation buttons
        self.nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("⬅️ Previous")
        self.prev_button.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
        self.prev_button.setIconSize(QSize(32, 32))
        self.prev_button.setMinimumHeight(50)
        self.prev_button.setStyleSheet("""
            QPushButton { background-color: #f0f0f0; border-radius: 4px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:disabled { color: #a0a0a0; }
        """)
        self.prev_button.clicked.connect(self.navigate_prev)
        
        self.next_button = QPushButton("Next ➡️")
        self.next_button.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
        self.next_button.setIconSize(QSize(32, 32))
        self.next_button.setMinimumHeight(50)
        self.next_button.setStyleSheet("""
            QPushButton { background-color: #f0f0f0; border-radius: 4px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:disabled { color: #a0a0a0; }
        """)
        self.next_button.clicked.connect(self.navigate_next)
        
        self.nav_layout.addWidget(self.prev_button)
        self.nav_layout.addWidget(self.next_button)
        self.layout.addLayout(self.nav_layout)

        # Action buttons at the bottom
        self.action_layout = QHBoxLayout()
        
        self.keep_button = QPushButton("✅ KEEP")
        self.keep_button.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; font-weight: bold; font-size: 16px; border-radius: 6px; }
            QPushButton:hover { background-color: #3d9c40; }
        """)
        self.keep_button.setMinimumHeight(60)
        self.keep_button.clicked.connect(self.keep_file)
        
        self.delete_button = QPushButton("🗑️ DISCARD")
        self.delete_button.setStyleSheet("""
            QPushButton { background-color: #f44336; color: white; font-weight: bold; font-size: 16px; border-radius: 6px; }
            QPushButton:hover { background-color: #e53935; }
        """)
        self.delete_button.setMinimumHeight(60)
        self.delete_button.clicked.connect(self.show_delete_confirmation)
        
        self.action_layout.addWidget(self.keep_button)
        self.action_layout.addWidget(self.delete_button)
        self.layout.addLayout(self.action_layout)
        
        self.central_widget.setLayout(self.layout)

        # Set a pleasant background color for the entire window
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f9f9f9;
            }
            QLabel {
                color: #333333;
            }
            QTextBrowser {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        # Initialize network manager for remote image loading
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_image_downloaded)
        
        self.setup_sloth_popup()
        # Load the last folder or prompt for a new one
        self.load_last_folder()

    def load_last_folder(self):
        """Load the last opened folder from config file if it exists"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    last_folder = config.get('last_folder', '')
                    if last_folder and os.path.exists(last_folder):
                        self.load_folder(last_folder)
                        return
        except Exception as e:
            print("Error loading config:", e)
        
        # If no last folder or error, prompt for a folder
        self.browse_folder()

    def save_config(self):
        """Save the current configuration to the config file"""
        try:
            # Create config directory if it doesn't exist
            os.makedirs(self.config_dir, exist_ok=True)
            
            config = {'last_folder': self.folder_path}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print("Error saving config:", e)

    def browse_folder(self):
        """Open a dialog to select a folder"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.load_folder(folder_path)

    def load_folder(self, folder_path):
        """Load files from the specified folder"""
        self.folder_path = folder_path
        # Filter for markdown files only
        self.files = sorted([f for f in os.listdir(folder_path) 
                            if os.path.isfile(os.path.join(folder_path, f)) 
                            and f.lower().endswith('.md')])
        
        # Save the folder path to config
        self.save_config()
        
        if self.files:
            self.current_index = 0
            self.show_current_file()
        else:
            self.file_title.setText("No markdown files found in the selected folder")
            self.content_display.setPlainText("")
            self.progress_indicator.setText("No files to display")
            self.progress_bar.setValue(0)
            self.files_viewed_since_popup = 0
            self.progress_bar.setMaximum(1)  # Avoid division by zero

    def show_current_file(self):
        if self.files and 0 <= self.current_index < len(self.files):
            file_name = self.files[self.current_index]
            self.file_title.setText(file_name)
            
            # Update progress indicator and progress bar
            self.progress_indicator.setText(f"Viewing file {self.current_index + 1} of {len(self.files)}")
            self.progress_bar.setMaximum(len(self.files))
            self.progress_bar.setValue(self.current_index + 1)
            self.progress_bar.setFormat(f"{int((self.current_index + 1) / len(self.files) * 100)}%")

            # Check if it's time to show the sloth popup (every 20 files)
            self.files_viewed_since_popup += 1
            if self.files_viewed_since_popup >= 20:
                self.show_sloth_popup()
            
            file_path = os.path.join(self.folder_path, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                    # Convert markdown to HTML for rendering
                    if file_name.lower().endswith('.md'):
                        html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])
                        # Add some basic CSS for better rendering
                        styled_html = f"""
                        <html>
                        <head>
                            <style>
                                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; padding: 20px; color: #333; }}
                                h1, h2, h3, h4, h5, h6 {{ color: #2c3e50; margin-top: 24px; margin-bottom: 16px; }}
                                h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
                                h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
                                code {{ background-color: #f8f8f8; padding: 0.2em 0.4em; border-radius: 3px; font-family: 'Consolas', monospace; }}
                                pre {{ background-color: #f8f8f8; padding: 16px; overflow: auto; border-radius: 5px; border: 1px solid #e0e0e0; }}
                                blockquote {{ padding: 0.5em 1em; color: #6a737d; border-left: 0.25em solid #4a86e8; background-color: #f8f9fa; }}
                                table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
                                table, th, td {{ border: 1px solid #e0e0e0; padding: 8px 16px; }}
                                img {{ max-width: 100%; border-radius: 5px; }}
                            </style>
                        </head>
                        <body>
                            {html_content}
                        </body>
                        </html>
                        """
                        self.content_display.setHtml(styled_html)
                    else:
                        # For non-markdown files, display as plain text
                        self.content_display.setPlainText(content)
            except Exception as e:
                self.content_display.setPlainText("Error opening file: " + str(e))
                print("Error opening " + file_name + ": " + str(e))

    def navigate_prev(self):
        if not self.files:
            return
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_file()
        
        # Update button states
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index < len(self.files) - 1)

    def navigate_next(self):
        if not self.files:
            return
        if self.current_index < len(self.files) - 1:
            self.current_index += 1
            self.show_current_file()
        
        # Update button states
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index < len(self.files) - 1)

    def keep_file(self):
        if not self.files or self.current_index >= len(self.files):
            return
        file_name = self.files[self.current_index]
        print("Keeping " + file_name)
        # Move to next file if available
        self.navigate_next()

    def show_delete_confirmation(self):
        if not self.files or self.current_index >= len(self.files):
            return
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                     'Are you sure you want to delete "' + self.files[self.current_index] + '"?', 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.delete_file()

    def delete_file(self):
        if not self.files or self.current_index >= len(self.files):
            return
        file_name = self.files[self.current_index]
        file_path = os.path.join(self.folder_path, file_name)
        try:
            os.remove(file_path)
            print("Deleted " + file_name)
            self.files.pop(self.current_index)
            if self.files:
                # If we deleted the last file, go to the previous one
                if self.current_index >= len(self.files):
                    self.current_index = len(self.files) - 1
                self.show_current_file()
            else:
                self.file_title.setText("No files left")
                self.content_display.setPlainText("")
                self.progress_indicator.setText("No files left")
                self.progress_bar.setValue(0)
                self.prev_button.setEnabled(False)
                self.next_button.setEnabled(False)
        except Exception as e:
            print("Error deleting " + file_name + ": " + str(e))
            QMessageBox.critical(self, "Error", "Could not delete file: " + str(e))

    def setup_sloth_popup(self):
        """Set up the sloth popup window"""
        self.sloth_popup = QWidget(self)
        self.sloth_popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.sloth_popup.setStyleSheet("""
            background-color: #90EE90;
            border: 4px solid #2E8B57;
            border-radius: 15px;
            padding: 10px;
        """)
        
        # Layout for the popup
        popup_layout = QVBoxLayout()
        
        # Image label
        self.sloth_image = QLabel()
        
        # Load the sloth image from remote URL
        self.sloth_image.setText("Loading sloth...")
        self.load_remote_image("https://res.cloudinary.com/drrvnflqy/image/upload/v1740514893/sloth-avatar_xs4djq.png")
        
        # Try to load a fun font, fall back to system fonts if not available
        font_id = QFontDatabase.addApplicationFont("Comic Sans MS")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            # Use a system font that's likely to be fun/playful
            font_family = "Comic Sans MS"  # Fallback to system Comic Sans if available
            
        zany_font = QFont(font_family, 14)
        zany_font.setBold(True)
        
        # Speech bubble
        self.speech_bubble = QLabel()
        self.speech_bubble.setStyleSheet("""
            background-color: #FFFFFF;
            border: 3px solid #2E8B57;
            border-radius: 15px;
            padding: 10px;
            font-size: 16px;
            font-weight: bold;
            color: #006400;
        """)
        self.speech_bubble.setFont(zany_font)
        
        # Add a fun title
        self.popup_title = QLabel("SLOTH SAYS:")
        self.popup_title.setAlignment(Qt.AlignCenter)
        self.popup_title.setFont(zany_font)
        self.popup_title.setStyleSheet("color: #006400; font-size: 18px;")
        
        popup_layout.addWidget(self.popup_title, alignment=Qt.AlignCenter)
        
        popup_layout.addWidget(self.sloth_image, alignment=Qt.AlignCenter)
        popup_layout.addWidget(self.speech_bubble, alignment=Qt.AlignCenter)
        self.sloth_popup.setLayout(popup_layout)

    def load_remote_image(self, url):
        """Load an image from a remote URL"""
        request = QNetworkRequest(QUrl(url))
        self.network_manager.get(request)
    
    def on_image_downloaded(self, reply):
        """Handle the downloaded image data"""
        if reply.error() == QNetworkReply.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            if not pixmap.isNull():
                self.sloth_image.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.sloth_image.setText("Failed to load image")
        else:
            self.sloth_image.setText("Error: " + reply.errorString())
        reply.deleteLater()

    def show_sloth_popup(self):
        """Show the sloth popup with a message about remaining files"""
        self.files_viewed_since_popup = 0
        
        # Calculate files left
        files_left = len(self.files) - (self.current_index + 1)
        
        # Set fun, encouraging message
        messages = [
            f"WOW! Only {files_left} files to go! You're AWESOME! 🎉",
            f"KEEP GOING! Just {files_left} more files! YOU GOT THIS! 🚀",
            f"ZOINKS! {files_left} files left! You're CRUSHING IT! 💪",
            f"HOLY MOLY! {files_left} to go! You're a SUPERSTAR! ⭐"
        ]
        import random
        self.speech_bubble.setText(random.choice(messages))
        
        # Position the popup in the center of the window
        self.sloth_popup.resize(350, 350)
        start_pos = self.geometry().center() - self.sloth_popup.rect().center()
        end_pos = QPoint(start_pos.x(), start_pos.y() - 200)  # Move up by 200 pixels
        self.sloth_popup.move(start_pos)
        self.sloth_popup.show()
        
        # Create animation to move the sloth up
        self.animation = QPropertyAnimation(self.sloth_popup, b"pos")
        self.animation.setDuration(2000)  # 2 seconds
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()
        
        # Hide after animation completes plus a little extra time
        QTimer.singleShot(4000, self.sloth_popup.hide)  # Hide after 4 seconds

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FileBrowser()
    window.setWindowTitle("Markdown Keep or Delete - File Browser")
    window.show()
    sys.exit(app.exec_())
