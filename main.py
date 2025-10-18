"""
Main Application Entry Point
Multi-Drive Cloud Manager - Desktop (PySide6)
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

# Ensure project root in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gui.main_window import MainWindow


def main():
    print("🚀 Starting Multi-Drive Cloud Manager (Desktop UI)...")
    app = QApplication(sys.argv)
    app.setApplicationName("Multi-Drive Cloud Manager")
    app.setOrganizationName("Jagyaa")
    app.setApplicationVersion("3.0.0")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
