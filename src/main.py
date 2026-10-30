"""PySide6 catalogue application, completed through practical work 39."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QDialog, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from database import PROJECT_DIR, authenticate, fetch_catalog, initialise_database


RESOURCES = PROJECT_DIR / "resources"
IMAGES = RESOURCES / "images"
PLACEHOLDER = RESOURCES / "picture.png"
LOGO = RESOURCES / "Мир велосипедов.png"
ICON = RESOURCES / "Мир велосипедов.ico"


class LoginDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.user = None
        self.setWindowTitle("Вход — Мир велосипедов")
        self.setMinimumWidth(360)
        layout = QVBoxLayout(self)
        title = QLabel("Вход в систему")
        title.setObjectName("title")
        layout.addWidget(title)
        form = QFormLayout()
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Например: admin или client01")
        form.addRow("Логин:", self.login_edit)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.log_in)
        guest_button = QPushButton("Продолжить как гость")
        guest_button.clicked.connect(self.accept)
        buttons.addWidget(login_button)
        buttons.addWidget(guest_button)
        layout.addLayout(buttons)
        self.login_edit.returnPressed.connect(self.log_in)

    def log_in(self) -> None:
        self.user = authenticate(self.login_edit.text())
        if self.user is None:
            QMessageBox.warning(self, "Вход", "Пользователь с таким логином не найден.")
            return
        self.accept()


class ProductCard(QFrame):
    def __init__(self, product) -> None:
        super().__init__()
        self.setObjectName("productCard")
        self.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(self)
        image = QLabel()
        image.setFixedSize(150, 110)
        image.setAlignment(Qt.AlignCenter)
        image_path = IMAGES / (product["image_name"] or "")
        pixmap = QPixmap(str(image_path if image_path.exists() else PLACEHOLDER))
        image.setPixmap(pixmap.scaled(145, 105, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(image)
        info = QVBoxLayout()
        name = QLabel(product["name"])
        name.setObjectName("productName")
        info.addWidget(name)
        info.addWidget(QLabel(f"{product['category']} · {product['subcategory']}"))
        info.addWidget(QLabel(f"Производитель: {product['manufacturer']}"))
        info.addWidget(QLabel(product["composition"]))
        stock = "Нет на складе" if product["quantity"] == 0 else f"В наличии: {product['quantity']} шт."
        info.addWidget(QLabel(stock))
        layout.addLayout(info, 1)
        price = QLabel(f"от {float(product['minimum_price'] or product['base_price']):,.2f} ₽".replace(",", " "))
        price.setObjectName("price")
        layout.addWidget(price, alignment=Qt.AlignRight | Qt.AlignVCenter)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.current_user = None
        self.setWindowTitle("Мир велосипедов")
        self.setWindowIcon(QIcon(str(ICON)))
        self.resize(980, 720)
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        header = QHBoxLayout()
        logo = QLabel()
        logo_pixmap = QPixmap(str(LOGO))
        logo.setPixmap(logo_pixmap.scaledToHeight(55, Qt.SmoothTransformation))
        header.addWidget(logo)
        header.addStretch()
        self.user_label = QLabel("Гость")
        header.addWidget(self.user_label)
        self.auth_button = QPushButton("Войти")
        self.auth_button.clicked.connect(self.open_login)
        header.addWidget(self.auth_button)
        root.addLayout(header)
        self.catalog_layout = QVBoxLayout()
        self.catalog_layout.setAlignment(Qt.AlignTop)
        container = QWidget()
        container.setLayout(self.catalog_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        root.addWidget(scroll, 1)
        self.statusBar().showMessage("Каталог загружен")
        self.load_catalog()

    def load_catalog(self) -> None:
        while self.catalog_layout.count():
            item = self.catalog_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        products = fetch_catalog()
        for product in products:
            self.catalog_layout.addWidget(ProductCard(product))
        self.statusBar().showMessage(f"Найдено моделей: {len(products)}")

    def open_login(self) -> None:
        dialog = LoginDialog(self)
        if dialog.exec():
            self.current_user = dialog.user
            if self.current_user is None:
                self.user_label.setText("Гость")
                self.auth_button.setText("Войти")
            else:
                fio = f"{self.current_user['last_name']} {self.current_user['first_name']} {self.current_user['patronymic']}"
                self.user_label.setText(f"{fio} ({self.current_user['role']})")
                self.auth_button.setText("Сменить пользователя")


def main() -> int:
    initialise_database()
    app = QApplication(sys.argv)
    app.setStyleSheet(
        """
        QWidget { font-family: Calibri; font-size: 14px; color: #000000; background: #FFFFFF; }
        QPushButton { background: #70B2AF; padding: 7px 12px; border: 0; border-radius: 4px; }
        QPushButton:hover { background: #D2F6E7; }
        #title, #productName { font-weight: bold; font-size: 18px; }
        #productCard { border: 1px solid #70B2AF; border-radius: 6px; margin: 4px; padding: 4px; }
        #price { font-weight: bold; font-size: 16px; }
        QLineEdit, QComboBox { padding: 6px; border: 1px solid #70B2AF; border-radius: 3px; }
        """
    )
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

