from LMS.module.reader import Reader
from LMS.module.writer import Writer
from enum import Enum


class LMS_NodeSubtypes(Enum):
    type_0 = 0
    type_1 = 1
    type_2 = 2
    type_3 = 3
    type_4 = 4
    string_table = 5
    type_6 = 6
    none = 255


class LMS_BaseNode:
    def __init__(self):
        self.id: int = None
        self.string_table_index: int = None
        self.subtype: LMS_NodeSubtypes = LMS_NodeSubtypes(255)
        self.param_1: int = 0
        self.subtype_value: int = 0
        self.param_2: int = 0
        self.next_node_id: int = None
        self.next_node: LMS_BaseNode = None
        self.param_3: int = 0
        self.param_4: int = 0

    def read(self, reader: Reader) -> None:
        self.subtype = LMS_NodeSubtypes(reader.read_uint8())
        reader.skip(2)
        self.subtype_value = reader.read_uint16()
        self.param_1 = reader.read_uint16()
        self.next_node_id = reader.read_uint16()
        self.param_2 = reader.read_uint16()
        self.param_3 = reader.read_uint16()
        self.param_4 = reader.read_uint16()

        if self.next_node_id == 65535:
            self.next_node_id = None

    def write(self, writer: Writer):
        writer.write_uint8(self.subtype.value)
        writer.write_bytes(b"\x00\x00")
        writer.write_uint16(self.subtype_value)
        writer.write_uint16(self.param_1)

        if self.next_node_id == None or self.next_node_id == "None":
            writer.write_uint16(65535)
        else:
            writer.write_uint16(self.next_node_id)

        writer.write_uint16(self.param_2)
        writer.write_uint16(self.param_3)
        writer.write_uint16(self.param_4)

    def get_node_type(self):
        return type(self).__name__

    def __str__(self):
        return f"{self.get_node_type()} {str(self.id)}"


class LMS_MessageNode(LMS_BaseNode):
    def __init__(self):
        super().__init__()

        # TODO: Implement parsing messages from a MSBT
        self.message: str = ""

    def read(self, reader: Reader):
        super().read(reader)


class LMS_BranchNode(LMS_BaseNode):
    def __init__(self):
        super().__init__()
        self.branches: list[LMS_BaseNode] = []


class LMS_EventNode(LMS_BaseNode):
    def __init__(self):
        super().__init__()
        # TODO: Implement custom event node attributes (if those exist)
        pass


class LMS_EntryNode(LMS_BaseNode):
    def __init__(self):
        super().__init__()
        self.label = ""


class LMS_JumpNode(LMS_BaseNode):
    def __init__(self):
        super().__init__()
        pass
