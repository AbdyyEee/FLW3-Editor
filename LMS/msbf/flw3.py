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

    def serialize_flowchart(self, node: LMS_ENtryNode):
        key = node.label
        while True:
            next_node = self.try_get_node(node.next_node_id)
            if next_node == None:
                break
            self.flowcharts[key].append(next_node)
            node = next_node

    def get_entry_node_by_label(self, label: str):
        for node in self.nodes:
            if type(node) == LMS_EntryNode:
                if node.label == label:
                    return node

    def read(self, reader: Reader):
        string_table_index = 0
        self.block.read_header(reader)
        data_start = reader.tell()

        node_count = reader.read_uint16()
        branch_id_count = reader.read_uint16()

        reader.skip(12)
        # Read the nodes
        for _ in range(node_count):
            type = reader.read_uint8()

            match type:
                case 1:
                    node = LMS_MessageNode()
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
                    self.flowcharts[node] = []
                case 5:
                    node = LMS_JumpNode()
                    node.read(reader)
            self.nodes.append(node)

            if node.subtype == LMS_NodeSubtypes.string_table:
                end = reader.tell()
                reader.seek(data_start)
                reader.seek(node.subtype_value, 1)
                string = reader.read_string_nt()
                node.string = string
                node.string_table_index = string_table_index
                self.string_table.append(string)
                reader.seek(end)

                string_table_index += 1

        # Read all the branch ids
        for _ in range(branch_id_count):
            id = reader.read_uint16()
            self.branch_list.append(id)

        # Serialize every node
        for node in self.nodes:
            if isinstance(node, LMS_BranchNode):
                for id in self.branch_list[node.param_4 : node.param_3 + node.param_4]:
                    next_branch_node = self.try_get_node(id)
                    node.branches.append(next_branch_node)
            else:
                node.next_node = self.try_get_node(node.next_node_id)

        # Add ID attribute to every node
        for i, node in enumerate(self.nodes):
            node.id = i
            if node.next_node is not None:
                node.next_node.id = node.next_node_id

    def write(self, writer: Writer):
        self.block.magic = "FLW3"
        self.block.write_header(writer)
        self.block.data_start = writer.tell()

        node_count = len(self.nodes)
        branch_id_count = len(self.branch_list)
        size = (node_count * 16 + 16) + branch_id_count * 2
        string_offset = size

        writer.write_uint16(node_count)
        writer.write_uint16(branch_id_count)
        writer.write_bytes(b"\x00" * 12)

        # Write all the nodes
        for node in self.nodes:
            if type(node) == LMS_MessageNode:
                writer.write_uint8(1)
            elif type(node) == LMS_BranchNode:
                writer.write_uint8(2)
            elif type(node) == LMS_EventNode:
                writer.write_uint8(3)
            elif type(node) == LMS_EntryNode:
                writer.write_uint8(4)
            elif type(node) == LMS_JumpNode:
                writer.write_uint8(5)

            if node.subtype == LMS_NodeSubtypes.string_table:
                node.subtype_value = string_offset
                string_offset += len(self.string_table[node.string_table_index]) + 1

            node.write(writer)

        for id in self.branch_list:
            if id == None:
                id == 65535
                continue
            writer.write_uint16(id)

        for string in self.string_table:
            writer.write_string_nt(string)
            size += len(string) + 1

        self.block.size = size
        self.block.write_ab_padding(writer)
        self.block.write_size(writer)
        self.block.seek_to_end(writer)
