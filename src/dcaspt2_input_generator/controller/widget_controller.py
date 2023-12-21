from dcaspt2_input_generator.components.data import colors, table_data
from dcaspt2_input_generator.components.table_summary import TableSummary
from dcaspt2_input_generator.components.table_widget import TableWidget


class WidgetController:
    def __init__(self, table_summary: TableSummary, table_widget: TableWidget):
        self.table_summary = table_summary
        self.table_widget = table_widget

        # Connect signals and slots
        # change_background_color is a slot
        self.table_widget.color_changed.connect(self.onTableWidgetColorChanged)

    def onTableWidgetColorChanged(self):
        color_count = {"core": 0, "inactive": 0, "ras1": 0, "active, ras2": 0, "ras3": 0, "secondary": 0}
        row_count = self.table_widget.rowCount()
        for row in range(row_count):
            color = self.table_widget.item(row, 0).background()
            sym_str = self.table_widget.item(row, 0).text()
            mo_num = int(self.table_widget.item(row, 1).text())
            table_data.header_info.moltra_info[sym_str][mo_num] = False if color == colors.not_used.color else True

            if color == colors.core.color:
                color_count["core"] += 2
            elif color == colors.inactive.color:
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
        self.table_summary.spinor_summary.core_label.setText(f"core: {color_count['core']}")
        self.table_summary.spinor_summary.inactive_label.setText(f"inactive: {color_count['inactive']}")
        self.table_summary.spinor_summary.ras1_label.setText(f"ras1: {color_count['ras1']}")
        self.table_summary.spinor_summary.active_label.setText(f"active, ras2: {color_count['active, ras2']}")
        self.table_summary.spinor_summary.ras3_label.setText(f"ras3: {color_count['ras3']}")
        self.table_summary.spinor_summary.secondary_label.setText(f"secondary: {color_count['secondary']}")

        # Update the maximum number of holes and electrons
        self.table_summary.user_input.ras1_max_hole_number.setTop(color_count["ras1"])
        self.table_summary.user_input.ras3_max_electron_number.setTop(color_count["ras3"])
        res = ""
        for k, d in table_data.header_info.moltra_info.items():
            res += f"\n {k}"
            range_str = ""
            left = True
            ser_end = False
            cur_mo_num = 0
            start_mo_num = cur_mo_num
            for mo_num, is_used in d.items():
                cur_mo_num = mo_num
                if is_used:
                    if left:
                        if range_str == "":
                            range_str += f" {mo_num}"
                        else:
                            range_str += f",{mo_num}"
                        start_mo_num = mo_num
                        left = False
                        ser_end = True
                elif ser_end:
                    if mo_num > start_mo_num + 1:
                        range_str += f"..{mo_num-1}"
                    left = True
                    ser_end = False
            if ser_end:
                range_str += f"..{cur_mo_num}"
            res += range_str

        self.table_summary.recommended_moltra.setText(f"Recommended MOLTRA setting: {res}")

        # Reload the input
        self.table_summary.update()
