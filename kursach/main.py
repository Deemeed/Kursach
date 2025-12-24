import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.login_dialog import LoginDialog


def main():
    app = QApplication(sys.argv)

    login = LoginDialog()

    if login.exec() == LoginDialog.DialogCode.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()