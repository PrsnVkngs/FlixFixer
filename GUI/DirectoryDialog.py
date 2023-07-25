from PyQt6.QtWidgets import QCheckBox, QDialog, QFormLayout, QSpinBox, QDialogButtonBox


class RecursiveDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttonBox = None
        self.recursive_cb = None
        self.recursion_depth_sb = None
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.recursive_cb = QCheckBox("Enable Recursive Search", self)
        self.recursive_cb.stateChanged.connect(self.toggle_recursion_depth)

        self.recursion_depth_sb = QSpinBox(self)
        self.recursion_depth_sb.setEnabled(False)  # initially disabled

        layout.addRow(self.recursive_cb)
        layout.addRow("Recursion Depth:", self.recursion_depth_sb)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)

        self.setLayout(layout)

    def toggle_recursion_depth(self):
        self.recursion_depth_sb.setEnabled(self.recursive_cb.isChecked())

    def get_values(self):
        return self.recursive_cb.isChecked(), self.recursion_depth_sb.value()
