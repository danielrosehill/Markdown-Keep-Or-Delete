import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QFileDialog, QMessageBox, QTextBrowser
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
import markdown

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

        # Top toolbar with Open Folder button
        self.toolbar_layout = QHBoxLayout()
        self.open_folder_button = QPushButton("Open Folder")
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

        # Content display - using QTextBrowser for HTML rendering
        self.content_display = QTextBrowser()
        self.content_display.setOpenExternalLinks(True)
        self.layout.addWidget(self.content_display, 1)

        # Navigation buttons
        self.nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("← Previous")
        self.prev_button.setIcon(self.style().standardIcon(self.style().SP_ArrowLeft))
        self.prev_button.setIconSize(QSize(32, 32))
        self.prev_button.setMinimumHeight(50)
        self.prev_button.clicked.connect(self.navigate_prev)
        
        self.next_button = QPushButton("Next →")
        self.next_button.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
        self.next_button.setIconSize(QSize(32, 32))
        self.next_button.setMinimumHeight(50)
        self.next_button.clicked.connect(self.navigate_next)
        
        self.nav_layout.addWidget(self.prev_button)
        self.nav_layout.addWidget(self.next_button)
        self.layout.addLayout(self.nav_layout)

        # Action buttons at the bottom
        self.action_layout = QHBoxLayout()
        
        self.keep_button = QPushButton("KEEP")
        self.keep_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 16px;")
        self.keep_button.setMinimumHeight(60)
        self.keep_button.clicked.connect(self.keep_file)
        
        self.delete_button = QPushButton("DISCARD")
        self.delete_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; font-size: 16px;")
        self.delete_button.setMinimumHeight(60)
        self.delete_button.clicked.connect(self.show_delete_confirmation)
        
        self.action_layout.addWidget(self.keep_button)
        self.action_layout.addWidget(self.delete_button)
        self.layout.addLayout(self.action_layout)
        
        self.central_widget.setLayout(self.layout)
        
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

    def show_current_file(self):
        if self.files and 0 <= self.current_index < len(self.files):
            file_name = self.files[self.current_index]
            self.file_title.setText(file_name)
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
                                body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
                                h1, h2, h3, h4, h5, h6 {{ color: #333; margin-top: 24px; margin-bottom: 16px; }}
                                h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
                                h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
                                code {{ background-color: #f6f8fa; padding: 0.2em 0.4em; border-radius: 3px; }}
                                pre {{ background-color: #f6f8fa; padding: 16px; overflow: auto; border-radius: 3px; }}
                                blockquote {{ padding: 0 1em; color: #6a737d; border-left: 0.25em solid #dfe2e5; }}
                                table {{ border-collapse: collapse; width: 100%; }}
                                table, th, td {{ border: 1px solid #dfe2e5; padding: 6px 13px; }}
                                img {{ max-width: 100%; }}
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

    def navigate_next(self):
        if not self.files:
            return
        if self.current_index < len(self.files) - 1:
            self.current_index += 1
            self.show_current_file()

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
        except Exception as e:
            print("Error deleting " + file_name + ": " + str(e))
            QMessageBox.critical(self, "Error", "Could not delete file: " + str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FileBrowser()
    window.show()
    sys.exit(app.exec_())
