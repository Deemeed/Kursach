import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QTreeView, QListView
)
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import QModelIndex


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Файловый менеджер")
        self.resize(900, 600)

        central_widget = QWidget()
        layout = QHBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.model = QFileSystemModel()
        self.model.setRootPath(os.path.expanduser("C:/"))

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index("C:/"))
        self.tree_view.setColumnWidth(0, 250)

        self.list_view = QListView()
        self.list_view.setModel(self.model)

        self.tree_view.selectionModel().selectionChanged.connect(self.on_tree_selection_changed)

        layout.addWidget(self.tree_view, 1)
        layout.addWidget(self.list_view, 2)

    def on_tree_selection_changed(self, selected, deselected):

        """Обработка выбора каталога в дереве"""

        for index in selected.indexes():
            if self.model.isDir(index):
                self.list_view.setRootIndex(index)
