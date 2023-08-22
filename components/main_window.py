import subprocess

from qtpy.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QInputDialog, QPushButton
from qtpy.QtGui import QDragEnterEvent


from components.menu_bar import MenuBar
from components.table_summary import TableSummary
from components.table_widget import TableWidget
from components.data import colors
from controller.color_settings_controller import ColorSettingsController
from controller.widget_controller import WidgetController


# Layout for the main window
# File, Settings
# message, AnimatedToggle (button)
# TableWidget (table)
# InputLayout (layout): core, inactive, active, secondary
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_UI()

    def init_UI(self):
        # Add drag and drop functionality
        self.setAcceptDrops(True)

        # Show the header bar
        self.menu_bar = MenuBar()
        self.menu_bar.open_action_dirac.triggered.connect(self.select_file_Dirac)
        self.menu_bar.open_action_dfcoef.triggered.connect(self.select_file_DFCOEF)

        # Body
        self.table_summary = TableSummary()
        self.table_widget = TableWidget()
        # Add Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_input)

        # Create an instance of WidgetController
        self.widget_controller = WidgetController(self.table_summary, self.table_widget)
        self.color_settings_controller = ColorSettingsController(self.table_widget, self.menu_bar.color_settings_action.color_settings)
        # layout
        layout = QVBoxLayout()
        layout.addWidget(self.menu_bar)
        layout.addWidget(self.table_widget)
        layout.addLayout(self.table_summary)
        layout.addWidget(self.save_button)

        # Create a widget to hold the layout
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def save_input(self):
        output = ""
        core = 0
        inact = 0
        act = 0
        sec = 0
        ras1_list = []
        ras2_list = []
        ras3_list = []
        for idx in range(self.table_widget.rowCount()):
            spinor_indices = [2 * idx + 1, 2 * idx + 2]
            color = self.table_widget.item(idx, 0).background().color()
            if color == colors.core.color:
                print(idx, "core")
                core += 2
            elif color == colors.inactive.color:
                print(idx, "inactive")
                inact += 2
            elif color == colors.ras1.color:
                print(idx, "ras1")
                act += 2
                ras1_list.extend(spinor_indices)
            elif color == colors.active.color:
                print(idx, "active")
                act += 2
                ras2_list.extend(spinor_indices)
            elif color == colors.ras3.color:
                print(idx, "ras3")
                sec += 2
                ras3_list.extend(spinor_indices)
            elif color == colors.secondary.color:
                print(idx, "secondary")
                sec += 2
        output += "ncore\n" + str(core) + "\n"
        output += "ninact\n" + str(inact) + "\n"
        output += "nact\n" + str(act) + "\n"
        output += "nsec\n" + str(sec) + "\n"
        output += "nbas\n" + str(core + inact + act + sec) + "\n"
        output += "nroot\n1\n"
        output += "selectroot\n1\n"
        output += "totsym\n33\n"
        output += "diracver\n21\n"
        output += "" if len(ras1_list) == 0 else "ras1\n" + " ".join(map(str, ras1_list)) + "\n" + self.table_summary.ras1_max_hole_number.text() + "\n"
        output += "" if len(ras2_list) == 0 else "ras2\n" + " ".join(map(str, ras2_list)) + "\n"
        output += "" if len(ras3_list) == 0 else "ras3\n" + " ".join(map(str, ras3_list)) + "\n" + self.table_summary.ras3_max_electron_number.text() + "\n"

        # open dialog to save the file
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt)")
        if file_path:
            # open the file with write mode
            with open(file_path, "w") as f:
                # get the text from the table widget
                f.write(output)

    def select_file_Dirac(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "SELECT A DIRAC OUTPUT FILE", "", "Output file (*.out)")
        if file_path:
            molecule_name = ""
            while molecule_name == "":
                molecule_name, _ = self.questionMolecule()
            # Run sum_dirac_defcoef subprocess
            self.run_sum_Dirac_DFCOEF(file_path, molecule_name)
            self.reload_table(molecule_name + ".out")

    def select_file_DFCOEF(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "SELECT A sum_dirac_dfcoef OUTPUT FILE", "", "Output file (*.out)")
        if file_path:
            self.reload_table(file_path)

    def questionMolecule(self):
        # Show a question message box that allow the user to write the molecule name
        molecule_name, ok = QInputDialog.getText(
            self,
            "Molecule formula",
            "Enter the molecule formula that you calculated using DIRAC:",
        )
        return molecule_name, ok

    def run_sum_Dirac_DFCOEF(self, file_path, molecule_name):
        command = f"sum_dirac_dfcoef -i {file_path} -m {molecule_name} -d 3 -c"
        process = subprocess.run(
            command,
            shell=True,
        )
        # Check the status of the subprocess named process
        if process.returncode != 0:
            QMessageBox.critical(
                self,
                "Error",
                f"An error has ocurred while running the sum_dirac_dfcoef program. Please, check the output file. path: {file_path}\nExecuted command: {command}",
            )

    def reload_table(self, output_path: str):
        try:
            if self.table_widget:
                self.table_widget.reload(output_path)
        except AttributeError:
            self.table_widget = TableWidget()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasText():
            event.accept()

    def dropEvent(self, event="") -> None:
        # Get the file path
        filepath = event.mimeData().text()[8:]
        self.reload_table(filepath)
