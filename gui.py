import sys
import yaml
import os
import traceback

from PyQt6 import QtGui, QtWidgets, uic

from LMS.module.reader import Reader
from LMS.module.writer import Writer
from LMS.msbf.msbf import MSBF
from LMS.msbt.msbt import MSBT
from LMS.msbf.nodes import (LMS_BaseNode, LMS_BranchNode, LMS_EntryNode,
                            LMS_EventNode, LMS_JumpNode, LMS_MessageNode,
                            LMS_NodeSubtypes)


class MSBF_Editor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.msbf: MSBF = None
        self.msbt: MSBT = None
        self.current_label: str = None
        self.current_nodes: list[LMS_BaseNode] = []
        self.previous_start_nodes: list[LMS_BaseNode] = []
        self.current_node_index = 0
        self.current_extension = None
        self.byte_order: str = None

        # -- Variables --
        # Parameter labels
        self.param_1_label: QtWidgets.QLabel = None
        self.param_2_label: QtWidgets.QLabel = None
        self.param_3_label: QtWidgets.QLabel = None
        self.param_4_label: QtWidgets.QLabel = None

        # List widgets
        self.flowchart_list: QtWidgets.QListView = None
        self.node_list: QtWidgets.QListView = None
        self.strings_list: QtWidgets.QListView = None
        self.branch_list: QtWidgets.QListView = None

        # Buttons
        self.delete_node_button: QtWidgets.QPushButton = None
        self.goto_root_button: QtWidgets.QPushButton = None
        self.add_next_node_button: QtWidgets.QPushButton = None
        self.add_string_button: QtWidgets.QPushButton = None
        self.edit_string_button: QtWidgets.QPushButton = None
        self.string_reference_button: QtWidgets.QPushButton = None
        self.add_branch_button: QtWidgets.QPushButton = None
        self.add_flowchart_button: QtWidgets.QPushButton = None
        self.back_button: QtWidgets.QPushButton = None

        # Edits
        self.type_edit: QtWidgets.QLineEdit = None
        self.subtype_edit: QtWidgets.QLineEdit = None
        self.subtype_value_edit: QtWidgets.QLineEdit = None
        self.id_edit: QtWidgets.QLineEdit = None
        self.next_id_edit: QtWidgets.QLineEdit = None
        self.string_index_edit: QtWidgets.QLineEdit = None
        self.index_edit: QtWidgets.QLineEdit = None
        self.param_1_edit: QtWidgets.QLineEdit = None
        self.param_2_edit: QtWidgets.QLineEdit = None
        self.param_3_edit: QtWidgets.QLineEdit = None
        self.param_4_edit: QtWidgets.QLineEdit = None
        self.message_edit: QtWidgets.QTextEdit = None
        self.label_edit: QtWidgets.QLineEdit = None

        # Menubar
        self.file_menu: QtWidgets.QMenuBar = None
        self.extensions_menu: QtWidgets.QMenuBar = None
        self.menu_load: QtWidgets.QMenuBar = None

        # Menu bar actions
        self.actionNewFile: QtGui.QAction = None
        self.actionOpen: QtGui.QAction = None
        self.actionSave: QtGui.QAction = None
        self.actionDisable: QtGui.QAction = None

        uic.load_ui.loadUi("Ui/Main.ui", self)
        self.setWindowTitle("FLW3 Editor: By AbdyyEee")
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.setFixedSize(783, 737)

        # -- Events --
        # Menubar
        self.actionOpen.triggered.connect(self.initialize_msbf)
        self.actionSave.triggered.connect(self.export_msbf)
        self.actionNewFile.triggered.connect(self.new_msbf)
        self.actionDisable.triggered.connect(self.extension_disable)

        # List views
        self.flowchart_list.itemClicked.connect(self.flowchart_clicked)
        self.node_list.itemClicked.connect(self.node_clicked)
        self.branch_list.itemDoubleClicked.connect(
            self.branch_node_double_clicked)
        self.strings_list.itemClicked.connect(self.string_clicked)
        self.node_list.itemDoubleClicked.connect(self.jump_node_double_clicked)

        # Buttons
        self.add_string_button.clicked.connect(self.add_string)
        self.edit_string_button.clicked.connect(self.edit_string)
        self.string_reference_button.clicked.connect(
            self.find_string_reference)
        self.add_next_node_button.clicked.connect(self.add_node)
        self.add_branch_button.clicked.connect(self.add_branch)
        self.add_flowchart_button.clicked.connect(self.new_flowchart)
        self.goto_root_button.clicked.connect(self.goto_root)
        self.back_button.clicked.connect(self.go_back)

        # Edits
        self.param_1_edit.editingFinished.connect(self.on_param_1_edit)
        self.param_2_edit.editingFinished.connect(self.on_param_2_edit)
        self.param_3_edit.editingFinished.connect(self.on_param_3_edit)
        self.param_4_edit.editingFinished.connect(self.on_param_4_edit)
        self.string_index_edit.editingFinished.connect(
            self.on_string_index_edit)

        # Disable till msbf is loaded
        self.actionSave.setEnabled(False)
        self.extensions_menu.setEnabled(False)
        self.goto_root_button.setEnabled(False)
        self.add_next_node_button.setEnabled(False)
        self.add_string_button.setEnabled(False)
        self.edit_string_button.setEnabled(False)
        self.string_reference_button.setEnabled(False)
        self.add_branch_button.setEnabled(False)
        self.add_flowchart_button.setEnabled(False)
        self.back_button.setEnabled(False)

        self.extension_add_games_to_list()

    # MSBF functions
    # --------------
    def initialize_msbf(self, is_new=False):
        self.msbf = MSBF()
        self.msbt = MSBT()

        if is_new:
            self.msbt = None

        self.flowchart_list.clear()
        self.branch_list.clear()
        self.node_list.clear()
        self.strings_list.clear()
        self.label_edit.clear()
        self.message_edit.clear()

        msbf_filter = "MSBF (*.msbf)"
        msbt_filter = "MSBT (*.msbt)"

        if not is_new:
            msbf_path = QtWidgets.QFileDialog.getOpenFileName(
                caption="Open a MSBF file.", filter=msbf_filter
            )[0]

            msbt_path = QtWidgets.QFileDialog.getOpenFileName(
                caption="Open a MSBT file.", filter=msbt_filter
            )[0]

            if len(msbf_path) == 0:
                return

            if len(msbt_path) > 0:
                with open(msbt_path, "rb+") as message:
                    reader = Reader(message.read())
                    try:
                        self.msbt.read(reader)
                    except Exception:
                        self.prompt_message(
                            f"An error occured while reading the MSBT file.\n\nError: {traceback.format_exc()}", type="Warning"
                        )

            else:
                self.msbt = None

            with open(msbf_path, "rb+") as flow:
                reader = Reader(flow.read())
                try:
                    if self.msbt is not None:
                        self.msbf.read(reader, self.msbt.txt2)
                    else:
                        self.msbf.read(reader, None)
                except Exception:
                    self.prompt_message(
                        f"An error occured while reading the MSBF file.\n\nError: {traceback.format_exc()}", type="Warning")

        if is_new:
            self.msbf.binary.bom = self.byte_order
        else:
            self.byte_order = self.msbf.binary.bom

        # Populate the flowchart list
        for label in self.msbf.flw3.flowcharts:
            self.flowchart_list.addItem(label)

        # Populate the strings list
        for string in self.msbf.flw3.string_table:
            self.strings_list.addItem(string)

        # Serialize all flowcharts
        for index in self.msbf.fen1.labels:
            label = self.msbf.fen1.labels[index]
            entry_node = self.msbf.flw3.get_entry_node_by_label(label)
            self.msbf.flw3.serialize_flowchart(entry_node)

        # Re-enable all the previously disabled items
        self.actionSave.setEnabled(True)
        self.extensions_menu.setEnabled(True)
        self.goto_root_button.setEnabled(True)
        self.add_next_node_button.setEnabled(True)
        self.add_string_button.setEnabled(True)
        self.edit_string_button.setEnabled(True)
        self.string_reference_button.setEnabled(True)
        self.add_branch_button.setEnabled(True)
        self.add_flowchart_button.setEnabled(True)
        self.back_button.setEnabled(True)

    def export_msbf(self):
        self.path = QtWidgets.QFileDialog.getSaveFileName(
            caption="Save", filter="MSBF (*.msbf)"
        )[0]

        # Create the file
        with open(self.path, "w+"):
            pass

        with open(self.path, "rb+") as flow:
            flow.truncate()
            writer = Writer(flow, self.byte_order)
            try:
                self.msbf.write(writer)
            except Exception:
                self.prompt_message(
                    f"An error occured while writing the MSBF file.\n\nError: {traceback.format_exc()}", type="Warning"
                )
                return

        self.prompt_message(
            "The MSBF has been written succesfully.", type="Message")

    def new_msbf(self):
        self.flowchart_list.clear()
        self.node_list.clear()
        self.branch_list.clear()

        byte_order = QtWidgets.QInputDialog.getText(
            self, "Select byte order", "Choose from 'little' (3DS) or 'big' (Wii or Wii U)")[0].lower()
        if byte_order not in ["little", "big"]:
            self.prompt_message("Select a proper byte order", type="Warning")
            return

        self.byte_order = byte_order
        self.initialize_msbf(is_new=True)

        self.prompt_message(
            "A new MSBF file has been created.", type="Message")

    # Flowchart related functions
    # ----------------------
    def new_flowchart(self):
        label = QtWidgets.QInputDialog.getText(
            self, "Add a flowchart", "Input the new label"
        )[0]

        if len(label) == 0:
            return

        for i in range(self.flowchart_list.count()):
            if self.flowchart_list.item(i).text() == label:
                self.prompt_message(
                    "This label already exists in the flowchart list.", type="Warning"
                )
                return

        entry_node = LMS_EntryNode()
        id = len(self.msbf.flw3.nodes)
        entry_node.label = label
        entry_node.id = id

        self.msbf.fen1.labels[id] = label
        self.msbf.flw3.nodes.append(entry_node)
        self.msbf.flw3.flowcharts[label] = [entry_node]
        self.msbf.flw3.flowcharts[label]
        self.flowchart_list.addItem(label)

    def goto_root(self):
        if len(self.flowchart_list.selectedIndexes()) == 0:
            return

        self.node_list.clear()
        self.branch_list.clear()

        for node in self.msbf.flw3.flowcharts[self.current_label]:
            self.node_list.addItem(str(node))

        self.current_nodes = self.msbf.flw3.flowcharts[self.current_label]

    def go_back(self):
        if self.current_node_index == 0:
            return

        self.node_list.clear()
        self.branch_list.clear()

        del self.previous_start_nodes[self.current_node_index]
        self.current_node_index -= 1

        previous_node: LMS_BaseNode = self.previous_start_nodes[self.current_node_index]
        # Select the flowchart from the flowchart list if the previous node is entry\
        if isinstance(previous_node, LMS_EntryNode):
            for i in range(self.flowchart_list.count()):
                if self.flowchart_list.item(i).text() == previous_node.label:
                    self.flowchart_list.item(i).setSelected(True)

        self.current_nodes = self.msbf.flw3.serialize_node(previous_node)
        self.add_nodes_to_list()

    # String table related functions
    # ------------------------------
    def add_string(self):
        new_string = QtWidgets.QInputDialog.getText(
            self, "Add string", "String")[0]
        self.strings_list.addItem(new_string)
        self.msbf.flw3.string_table.append(new_string)

    def edit_string(self):
        current_row = self.strings_list.currentRow()
        current_text = self.strings_list.item(current_row).text()
        edited_string = QtWidgets.QInputDialog.getText(
            self, "Edit string", "String", text=current_text
        )[0]
        self.strings_list.item(current_row).setText(edited_string)

        self.msbf.flw3.string_table[current_row] = edited_string

    def find_string_reference(self):
        self.node_list.clear()
        self.branch_list.clear()
        referenced_node = None

        for node in self.msbf.flw3.nodes:
            if isinstance(node, LMS_BranchNode) or isinstance(node, LMS_EventNode):
                if node.string_table_index == self.strings_list.currentRow():
                    referenced_node = node

        self.add_nodes_to_list(referenced_node)

    def string_clicked(self):
        self.index_edit.setText(str(self.strings_list.currentRow()))

    # Node related functions
    # ----------------------

    def refresh_node_list(self):
        if self.node_list.count() == 0:
            return
        self.node_list.clear()

        for i in range(0, len(self.current_nodes) - 1):
            node = self.current_nodes[i]
            self.extension_match_node(node)
            self.node_list.addItem(node.name)
            node.next_node_id = self.current_nodes[i + 1].id

        self.node_list.addItem(
            self.current_nodes[len(self.current_nodes) - 1].name)

    def refresh_branch_list(self):
        if self.branch_list.count() == 0:
            return

        self.branch_list.clear()
        node: LMS_BranchNode = self.get_current_node()
        for branch in node.branches:
            if branch is None:
                self.branch_list.addItem(str(branch))
                continue
            self.extension_match_node(branch)
            self.branch_list.addItem(branch.name)

    def add_nodes_to_list(self, node_to_add: LMS_BaseNode | None = None):
        if node_to_add is None:
            for node in self.current_nodes:
                self.extension_match_node(node)
                self.node_list.addItem(node.name)
                if isinstance(node, LMS_JumpNode):
                    break
        else:
            node_list = self.msbf.flw3.serialize_node(node_to_add)

            self.previous_start_nodes.append(node_list[0])
            self.current_node_index += 1
            self.current_nodes = node_list

            for node in self.current_nodes:
                self.node_list.addItem(node.name)
                if isinstance(node, LMS_JumpNode):
                    break

    def get_current_node(self) -> LMS_BaseNode:
        index = self.node_list.currentRow()
        return self.current_nodes[index]

    def get_current_branch_node(self) -> LMS_BaseNode:
        branch_node = self.get_current_node()
        index = self.branch_list.currentRow()
        return branch_node.branches[index]

    def get_branch_nodes(self) -> list[LMS_BaseNode]:
        branch_node = self.get_current_node()
        return branch_node.branches

    # Touch event functions
    # ---------------------
    def flowchart_clicked(self):
        self.previous_start_nodes = []
        self.current_node_index = 0
        self.node_list.clear()
        self.previous_start_nodes.clear()

        label = self.flowchart_list.item(
            self.flowchart_list.currentRow()).text()
        flowchart = self.msbf.flw3.flowcharts[label]
        self.current_nodes = flowchart

        self.add_nodes_to_list()
        self.current_label = label
        self.previous_start_nodes.append(flowchart[0])

    def node_clicked(self):
        self.branch_list.clear()
        node = self.get_current_node()
        self.extension_match_node(node)

        # Handling enabling of parameter edits
        if type(node) == LMS_EntryNode or type(node) == LMS_JumpNode:
            self.param_1_edit.setEnabled(False)
            self.param_2_edit.setEnabled(False)
            self.param_3_edit.setEnabled(False)
            self.param_4_edit.setEnabled(False)
        else:
            if not isinstance(node, LMS_BranchNode):
                self.add_branch_button.setEnabled(False)
                self.param_1_edit.setEnabled(True)
                self.param_2_edit.setEnabled(True)
                self.param_3_edit.setEnabled(True)
                self.param_4_edit.setEnabled(True)
            else:
                self.add_branch_button.setEnabled(True)
                self.param_1_edit.setEnabled(True)
                self.param_2_edit.setEnabled(True)
                self.param_3_edit.setEnabled(False)
                self.param_4_edit.setEnabled(False)

        # Changing labels for certain nodes
        if isinstance(node, LMS_MessageNode):
            self.param_3_label.setText("MSBT index")
            self.param_4_label.setText("File index")

        elif isinstance(node, LMS_BranchNode):
            self.param_3_label.setText("Branch count")
            self.param_4_label.setText("Branch index")
        else:
            self.param_3_label.setText("Parameter 3")
            self.param_4_label.setText("Parameter 4")

        if isinstance(node, LMS_MessageNode):
            if self.msbt is not None:
                self.label_edit.setText(self.msbt.lbl1.labels[node.param_3])
                self.message_edit.setText(
                    self.msbt.txt2.messages[node.param_3])
        else:
            self.label_edit.clear()
            self.message_edit.clear()

        if self.current_extension is not None:
            for node_data in self.current_extension:
                node_name = self.get_current_node().name
                node_name = node_name[:node_name.index(" ")]
                if node_data["name"] == node_name:
                    self.param_1_label.setText(
                        node_data["labels"]["param_1"])
                    self.param_2_label.setText(
                        node_data["labels"]["param_2"])
                    self.param_3_label.setText(
                        node_data["labels"]["param_3"])
                    self.param_4_label.setText(
                        node_data["labels"]["param_4"])

                    self.param_1_edit.setEnabled(
                        node_data["edits"]["param_1"])
                    self.param_2_edit.setEnabled(
                        node_data["edits"]["param_2"])
                    self.param_3_edit.setEnabled(
                        node_data["edits"]["param_3"])
                    self.param_4_edit.setEnabled(
                        node_data["edits"]["param_4"])

        # Set generic information
        self.type_edit.setText(node.get_node_type())
        self.subtype_edit.setText(str(node.subtype))
        self.subtype_value_edit.setText(str(node.subtype_value))
        self.id_edit.setText(str(node.id))
        self.next_id_edit.setText(str(node.next_node_id))

        if node.subtype == LMS_NodeSubtypes.string_table:
            # Disable subtype value editing so that its clear string offsets can't be messed with
            self.subtype_value_edit.setEnabled(False)
            self.string_index_edit.setEnabled(True)
            self.string_index_edit.setText(str(node.string_table_index))
        else:
            self.subtype_value_edit.setEnabled(True)
            self.string_index_edit.setEnabled(False)
            self.string_index_edit.clear()

        # Setting parameter information
        self.param_1_edit.setText(str(node.param_1))
        self.param_2_edit.setText(str(node.param_2))
        self.param_3_edit.setText(str(node.param_3))
        self.param_4_edit.setText(str(node.param_4))

        if isinstance(node, LMS_BranchNode):
            # Add branches to branch list
            for i, branch in enumerate(node.branches):
                self.branch_list.addItem(str(branch))

                if branch is not None:
                    self.extension_match_node(branch)
                    self.branch_list.item(i).setText(branch.name)

    def branch_node_double_clicked(self):
        node = self.get_current_branch_node()

        if node is None:
            return

        self.branch_list.clear()
        self.node_list.clear()
        self.add_nodes_to_list(node)

    def jump_node_double_clicked(self):
        node: LMS_JumpNode = self.get_current_node()
        label_index = None
        label = None
        if isinstance(node, LMS_JumpNode):
            for i in range(self.flowchart_list.count()):
                if self.flowchart_list.item(i).text() == node.jump_label:
                    label_index = i
                    label = self.flowchart_list.item(i).text()

            self.flowchart_list.item(label_index).setSelected(True)
            self.node_list.clear()
            self.branch_list.clear()
            entry_node = self.msbf.flw3.get_entry_node_by_label(label)
            self.add_nodes_to_list(entry_node)

    def add_node(self):
        self.popup = NextNode_Popup(self)

    def add_branch(self):
        self.popup = NextNode_Popup(self, branch=True)

    # Edit event functions
    # --------------------
    def on_param_1_edit(self):
        node = self.get_current_node()
        text: str = self.param_1_edit.text()

        if text.isnumeric():
            node.param_1 = int(text)

    def on_param_2_edit(self):
        node = self.get_current_node()
        text: str = self.param_2_edit.text()

        if text.isnumeric():
            node.param_2 = int(text)

    def on_param_3_edit(self):
        node = self.get_current_node()
        text: str = self.param_3_edit.text()

        if text.isnumeric():
            node.param_3 = int(text)

    def on_param_4_edit(self):
        node = self.get_current_node()
        text: str = self.param_4_edit.text()

        if text.isnumeric():
            node.param_4 = int(text)

    def on_string_index_edit(self):
        node: LMS_BaseNode = self.get_current_node()
        text: str = self.string_index_edit.text()

        if text.isnumeric():
            node.string_table_index = int(text)

    def on_subtype_value_edit(self):
        node = self.get_current_node()
        text: str = self.subtype_value_edit.text()

        if text.isnumeric():
            node.subtype_value = int(text)

    # Extension functions
    # -------------------
    def extension_add_games_to_list(self):
        for file in os.listdir(f"Extensions"):
            name = file[:file.index(".yaml")]
            game_action = self.menu_load.addAction(name)

            def extension_load():
                with open(f"Extensions/{file}", "r") as extension:
                    self.current_extension = yaml.safe_load(extension)
                    self.prompt_message(
                        f"This extension has been loaded.", type="Message")

                    self.refresh_node_list()
                    self.refresh_branch_list()

            game_action.triggered.connect(extension_load)

    def extension_match_node(self, node: LMS_BaseNode):
        if node is None:
            return

        if self.current_extension is None:
            node.name = str(node)
            return

        node_values = [node.param_1, node.param_2, node.param_3, node.param_4]
        for node_data in self.current_extension:
            result: list[bool, bool, bool, bool] = []
            matched_values = node_data["node_values"]

            if type(node) in [LMS_MessageNode, LMS_EntryNode, LMS_JumpNode]:
                return

            if node_data["type"] == node.get_node_type() and node_data["subtype"] == node.subtype.value:

                for i in range(len(matched_values)):
                    value = matched_values[i]
                    if value == node_values[i]:
                        result.append(True)
                        continue

                    if value == "any":
                        result.append(True)
                        continue

                    result.append(False)

                if result == [True, True, True, True]:
                    node.name = f"{node_data['name']} {node.id}"

    def extension_disable(self):
        if self.current_extension is None:
            return
        self.current_extension = None
        self.prompt_message(
            "The current extension has been disabled.", "Message")

        self.refresh_node_list()
        self.refresh_branch_list()

    # Miscellaneous
    def prompt_message(self, message: str, type: str):
        warning = QtWidgets.QMessageBox()
        warning.setWindowTitle("FLW3 Editor")
        warning.setText(message)

        if type == "Message":
            warning.setIcon(QtWidgets.QMessageBox.Icon.Information)

        if type == "Warning":
            warning.setIcon(QtWidgets.QMessageBox.Icon.Critical)

        warning.exec()


class NextNode_Popup(QtWidgets.QMainWindow):
    def __init__(self, parent: MSBF_Editor, branch=False):
        super().__init__()
        self.parent = parent
        self.branch = branch

        # List views
        self.type_box: QtWidgets.QListView = None
        self.subtype_box: QtWidgets.QListView = None

        # Button
        self.add_button: QtWidgets.QPushButton = None

        uic.load_ui.loadUi("Ui/NextNode_Popup.ui", self)

        # -- Events --
        self.add_button.clicked.connect(self.get_new_node)
        self.type_box.currentIndexChanged.connect(self.disable_subtype_box)
        self.subtype_box.setDisabled(True)

        # Add the "none" type used in branches
        # if self.branch:
        # self.type_box.addItem("None")

        self.show()

    def disable_subtype_box(self):
        match self.type_box.currentIndex():
            case 0:
                self.subtype_box.setDisabled(True)
            case 1:
                self.subtype_box.setDisabled(False)
            case 2:
                self.subtype_box.setDisabled(False)
            case 3:
                self.subtype_box.setCurrentIndex(7)
                self.subtype_box.setDisabled(True)
            case 4:
                self.subtype_box.setCurrentIndex(7)
                self.subtype_box.setDisabled(True)
            case 5:
                self.subtype_box.setDisabled(True)
            case _:
                self.subtype_box.setDisabled(True)

    def get_new_node(self):
        match self.type_box.currentIndex():
            case 0:
                new_node = LMS_MessageNode()
            case 1:
                new_node = LMS_BranchNode()
            case 2:
                new_node = LMS_EventNode()
            case 3:
                new_node = LMS_JumpNode()

        if type(new_node) not in [LMS_EntryNode, LMS_JumpNode, LMS_MessageNode]:
            match self.subtype_box.currentIndex():
                case 0:
                    new_node.subtype = LMS_NodeSubtypes(0)
                case 1:
                    new_node.subtype = LMS_NodeSubtypes(1)
                case 2:
                    new_node.subtype = LMS_NodeSubtypes(2)
                case 3:
                    new_node.subtype = LMS_NodeSubtypes(3)
                case 4:
                    new_node.subtype = LMS_NodeSubtypes(4)
                case 5:
                    new_node.subtype = LMS_NodeSubtypes(5)
                case 6:
                    new_node.subtype = LMS_NodeSubtypes(6)
        else:
            new_node.subtype = LMS_NodeSubtypes(255)
            new_node.subtype_value = 0

        if isinstance(new_node, LMS_JumpNode):
            label = QtWidgets.QInputDialog.getText(
                self, "Label", "Input flowchart label you'd like to jump to"
            )[0]

            if len(label) == 0:
                return

            if label not in self.parent.msbf.flw3.flowcharts:
                self.parent.prompt_message(
                    "This label is not in the flowchart list", type="Warning"
                )
                return

            new_node.param_3 = 65535

            new_node.next_node_id = self.parent.msbf.flw3.flowcharts[label][0].id

        if new_node.subtype == LMS_NodeSubtypes.string_table:
            string_index = QtWidgets.QInputDialog.getInt(
                self, "String index", "Input the index from the string table"
            )[0]
            new_node.string_table_index = string_index

        new_node.id = len(self.parent.msbf.flw3.nodes)
        new_node.name = str(new_node)
        self.parent.msbf.flw3.nodes.append(new_node)

        if not self.branch:
            if isinstance(new_node, LMS_BranchNode):
                new_node.param_4 = len(self.parent.msbf.flw3.branch_list)

            self.parent.current_nodes.insert(
                self.parent.node_list.currentRow() + 1, new_node
            )
            self.parent.refresh_node_list()
            self.hide()
            return

        # Check if there are 2 or more branch nodes and prevent the new node from being added
        if isinstance(new_node, LMS_BranchNode):
            for node in self.parent.get_branch_nodes():
                if isinstance(new_node, LMS_BranchNode):
                    self.parent.prompt_message(
                        "Adding multiple branch nodes to an existing branch is not support as this may cause issues.",
                        type="Warning",
                    )
                    return

        # Branch node handling
        self.parent.branch_list.addItem(str(new_node))
        selected_branch_node: LMS_BranchNode = self.parent.get_current_node()
        selected_branch_node.branches.append(new_node)

        # Add the new node id into the branch id table
        id_index = selected_branch_node.param_4 + selected_branch_node.param_3
        # Increase the branch count short
        selected_branch_node.param_3 += 1
        self.parent.msbf.flw3.branch_list.insert(id_index, new_node.id)

        # Make sure any added branch nodes have their branch index parameter set correctly
        for node in self.parent.get_branch_nodes():
            if isinstance(new_node, LMS_BranchNode):
                node.param_4 = len(self.parent.msbf.flw3.branch_list)

        self.hide()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MSBF_Editor()
    window.show()
    sys.exit(app.exec())
