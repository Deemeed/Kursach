from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход в файловый менеджер")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout(self)

        # Метка
        label = QLabel("Введите пароль:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Поле для пароля
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.check_password)
        layout.addWidget(self.password_input)

        # Кнопка
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.check_password)
        layout.addWidget(self.login_button)

    def check_password(self):
        from kursach.core.auth import check_password

        password = self.password_input.text()

        if check_password(password):
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный пароль")
            self.password_input.clear()
            self.password_input.setFocus()