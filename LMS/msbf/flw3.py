from LMS.common.lms_block import LMS_Block

from LMS.module.reader import Reader
from LMS.module.writer import Writer
from LMS.msbf.nodes import (
    LMS_BaseNode,
    LMS_EntryNode,
    LMS_BranchNode,
    LMS_EventNode,
    LMS_JumpNode,
    LMS_MessageNode,
    LMS_NodeSubtypes,
)
from LMS.common.lms_hashtable import LMS_HashTableBlock
from LMS.msbt.txt2 import TXT2


class FLW3:
    def __init__(self):
        self.block = LMS_Block()
        self.flowcharts: dict = {}
        self.nodes: list[LMS_BaseNode] = []
        self.branch_list: list[int | None] = []
        self.string_table: list[str] = []

    def try_get_node(self, id: int):
        if id == 65535 or id == None:
            return None
        return self.nodes[id]

    def serialize_node(self, node: LMS_BaseNode):
        result = []
        result.append(node)
        while True:
            next_node = self.try_get_node(node.next_node_id)
            if next_node == None:
                return result
            result.append(next_node)
            node = next_node

    def serialize_flowchart(self, node: LMS_EntryNode):
        key = node.label
        while True:
            next_node = self.try_get_node(node.next_node_id)
            if next_node == None:
                break
            self.flowcharts[key].append(next_node)
            node = next_node

    def get_entry_node_by_label(self, label: str):
        for node in self.nodes:
            if isinstance(node, LMS_EntryNode) and node.label == label:
                return node

    def read(self, reader: Reader, fen1: LMS_HashTableBlock, txt2: TXT2):
        string_table_index = 0
        self.block.read_header(reader)
        data_start = reader.tell()

        node_count = reader.read_uint16()
        branch_id_count = reader.read_uint16()

        reader.skip(12)
        # Read the nodes
        for i in range(node_count):
            type = reader.read_uint8()
            match type:
                case 1:
                    node = LMS_MessageNode()
                    if txt2 is not None:
                        node.message = txt2.messages[node.param_3]
                    node.read(reader)
                case 2:
                    node = LMS_BranchNode()
                    node.read(reader)
                case 3:
                    node = LMS_EventNode()
                    node.read(reader)
                case 4:
                    node = LMS_EntryNode()
                    node.read(reader)
                    label = fen1.labels[i]
                    node.label = label
                    self.flowcharts[label] = []
                case 5:
                    node = LMS_JumpNode()
                    node.read(reader)
                    node.jump_label = fen1.labels[node.next_node_id]

            self.nodes.append(node)

            if node.subtype == LMS_NodeSubtypes.string_table:
                end = reader.tell()
                string_offset = data_start + node.subtype_value
                reader.seek(string_offset)

                string = reader.read_string_nt()
                node.string_table_index = string_table_index
                self.string_table.append(string)
                reader.seek(end)
                string_table_index += 1

        # Read all the branch ids
        for _ in range(branch_id_count):
            id = reader.read_uint16()
            if id == 65535:
                self.branch_list.append(None)
                continue
            self.branch_list.append(id)

        # Serialize every node
        for node in self.nodes:
            if isinstance(node, LMS_BranchNode):
                branch_end = node.param_3 + node.param_4
                branch_part = self.branch_list[node.param_4: branch_end]
                for id in branch_part:
                    branched_node = self.try_get_node(id)
                    node.branches.append(branched_node)
            else:
                node.next_node = self.try_get_node(node.next_node_id)

        # Add ID attribute to every node
        for i, node in enumerate(self.nodes):
            node.id = i
            node.name = str(node)

    def write(self, writer: Writer):
        self.block.magic = "FLW3"
        self.block.write_header(writer)
        self.block.data_start = writer.tell()

        node_count = len(self.nodes)
        branch_id_count = len(self.branch_list)
        size = node_count * 16 + 16 + branch_id_count * 2
        string_offset = size

        writer.write_uint16(node_count)
        writer.write_uint16(branch_id_count)
        writer.write_bytes(b"\x00" * 12)

        # Write all the nodes
        for node in self.nodes:
            if isinstance(node, LMS_MessageNode):
                writer.write_uint8(1)
            elif isinstance(node, LMS_BranchNode):
                writer.write_uint8(2)
            elif isinstance(node, LMS_EventNode):
                writer.write_uint8(3)
            elif isinstance(node, LMS_EntryNode):
                writer.write_uint8(4)
            elif isinstance(node, LMS_JumpNode):
                writer.write_uint8(5)

            if node.subtype == LMS_NodeSubtypes.string_table:
                node.subtype_value = string_offset
                string_offset += len(
                    self.string_table[node.string_table_index]) + 1

            node.write(writer)

        for id in self.branch_list:
            if id is None:
                id = 65535
            writer.write_uint16(id)

        for string in self.string_table:
            writer.write_string_nt(string)
            size += len(string) + 1

        self.block.size = size
        self.block.write_end_data(writer)
