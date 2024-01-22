from collections import OrderedDict

from dcaspt2_input_generator.components.data import colors, table_data
from dcaspt2_input_generator.components.table_summary import TableSummary
from dcaspt2_input_generator.components.table_widget import TableWidget
from dcaspt2_input_generator.utils.dir_info import dir_info


class WidgetController:
    def __init__(self, table_summary: TableSummary, table_widget: TableWidget):
        self.table_summary = table_summary
        self.table_widget = table_widget

        # Connect signals and slots
        self.table_summary.user_input.changed.connect(self.onUserInputChanged)
        # change_background_color is a slot
        self.table_widget.color_changed.connect(self.onTableWidgetColorChanged)

    def handleIVOInput(self):
        """Create standard input for IVO"""

        # Create info for standard IVO input
        # E1g,u or E1?
        is_gerade_ungerade = True if table_data.header_info.spinor_num_info.keys() == {"E1g", "E1u"} else False
        if is_gerade_ungerade:
            nocc = {"E1g": 0, "E1u": 0}
            nvcut = {"E1g": 0, "E1u": 0}
        else:
            nocc = {"E1": 0}
            nvcut = {"E1": 0}
        act = 0
        sec = 0
        rem_electrons = table_data.header_info.electron_number
        row_count = self.table_widget.rowCount()
        for row in range(row_count):
            item = self.table_widget.item(row, 0)
            color = item.background()
            sym_str = item.text()

            # nocc, nvcut
            if rem_electrons >= 0:
                nocc[sym_str] += 1
            elif color != colors.not_used.color:
                # Reset nvcut
                for k in nvcut.keys():
                    nvcut[k] = 0
            else:
                nvcut[sym_str] += 1

            # act, sec
            if color == colors.not_used.color:
                pass
            elif rem_electrons >= 0:
                act += 2
            else:
                sec += 2
            rem_electrons -= 2

        # Create standard IVO input
        output = ""
        output += "ninact\n0\n"
        output += f"nact\n{act}\n"
        output += f"nsec\n{sec}\n"
        output += f"nelec\n{act}\n"
        if is_gerade_ungerade:
            output += f"noccg\n{nocc['E1g']}\nnoccu\n{nocc['E1u']}\n"
            output += "" if sum(nvcut.values()) == 0 else f"nvcutg\n{nvcut['E1g']}\nnvcutu\n{nvcut['E1u']}\n"
        else:
            output += f"nocc\n{nocc['E1']}\n"
            output += "" if sum(nvcut.values()) == 0 else f"nvcut\n{nvcut['E1']}\n"
        output += f"totsym\n{self.table_summary.user_input.totsym_number.get_value()}\n"
        output += f"diracver\n{self.table_summary.user_input.dirac_ver_number.get_value()}\n"
        output += "end\n"

        # Save standard IVO input (replace active.ivo.inp)
        with open(dir_info.ivo_input_path, "w") as f:
            f.write(output)

    def onUserInputChanged(self):
        self.handleIVOInput()

    def onTableWidgetColorChanged(self):
        color_count = {"inactive": 0, "ras1": 0, "active, ras2": 0, "ras3": 0, "secondary": 0}
        row_count = self.table_widget.rowCount()
        for row in range(row_count):
            color = self.table_widget.item(row, 0).background()
            sym_str = self.table_widget.item(row, 0).text()
            mo_num = int(self.table_widget.item(row, 1).text())
            table_data.header_info.moltra_info[sym_str][mo_num] = False if color == colors.not_used.color else True

            if color == colors.inactive.color:
                color_count["inactive"] += 2
            elif color == colors.ras1.color:
                color_count["ras1"] += 2
            elif color == colors.active.color:
                color_count["active, ras2"] += 2
            elif color == colors.ras3.color:
                color_count["ras3"] += 2
            elif color == colors.secondary.color:
                color_count["secondary"] += 2

        # Update summary information
        self.table_summary.spinor_summary.inactive_label.setText(f"inactive: {color_count['inactive']}")
        self.table_summary.spinor_summary.ras1_label.setText(f"ras1: {color_count['ras1']}")
        self.table_summary.spinor_summary.active_label.setText(f"active, ras2: {color_count['active, ras2']}")
        self.table_summary.spinor_summary.ras3_label.setText(f"ras3: {color_count['ras3']}")
        self.table_summary.spinor_summary.secondary_label.setText(f"secondary: {color_count['secondary']}")

        # Update the maximum number of holes and electrons
        self.table_summary.user_input.ras1_max_hole_number.validator.setTop(color_count["ras1"])
        self.table_summary.user_input.ras3_max_electron_number.validator.setTop(color_count["ras3"])
        res = ""
        for k, d in table_data.header_info.moltra_info.items():
            res += f"\n {k}"
            range_str = ""
            start = True
            prev_mo_num = 0
            range_start_num = 0
            search_end = False
            sorted_d = OrderedDict(sorted(d.items()))
            for mo_num, is_used in sorted_d.items():
                search_end = True
                if not is_used:
                    continue
                if start:
                    # First used MO
                    range_str += f" {mo_num}"
                    range_start_num = mo_num
                    start = False
                elif mo_num != prev_mo_num + 1:
                    if range_start_num == prev_mo_num:
                        # Prev MO is alone, already added to range_str
                        range_str += f" {mo_num}"
                        range_start_num = mo_num
                    else:
                        # Prev MO is not alone, not added to range_str yet
                        range_str += f"..{prev_mo_num} {mo_num}"
                        range_start_num = mo_num
                prev_mo_num = mo_num
            if search_end and range_start_num != prev_mo_num:
                # prev_mo_num is not added to range_str
                range_str += f"..{prev_mo_num}"
            res += range_str

        self.table_summary.recommended_moltra.setText(f"Recommended MOLTRA setting: {res}")

        # Reload the input
        self.table_summary.update()

        self.handleIVOInput()
