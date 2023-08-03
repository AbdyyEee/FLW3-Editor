from LMS.common.lms_binary import LMS_Binary
from LMS.common.lms_hashtable import LMS_HashTableBlock
from LMS.module.reader import Reader
from LMS.module.writer import Writer
from LMS.common.lms_binary import LMS_MessageEncoding
from LMS.msbf.flw3 import FLW3


class MSBF:
    def __init__(self):
        self.binary = LMS_Binary()
        self.flw3 = FLW3()
        self.fen1 = LMS_HashTableBlock()

    def read(self, reader: Reader) -> None:
        self.binary.read_header(reader)

        flw3_offset = self.binary.search_block_by_name(reader, "FLW3")
        fen1_offset = self.binary.search_block_by_name(reader, "FEN1")

        reader.seek(flw3_offset)
        self.flw3.read(reader)

        reader.seek(fen1_offset)
        self.fen1.read(reader)

        for index in self.fen1.labels:
            label = self.fen1.labels[index]
            entry_key = self.flw3.nodes[index]
            entry_key.label = label

            self.flw3.flowcharts[label] = self.flw3.flowcharts.pop(entry_key)

    def write(self, writer: Writer) -> None:
        self.binary.magic = "MsgFlwBn"
        self.binary.file_size = 0
        self.binary.bom = "little"
        self.binary.encoding = LMS_MessageEncoding(0)
        self.binary.revision = 3
        self.binary.block_count = 2

        self.flw3.block.magic = "FLW3"
        self.flw3.block.size = 0
        self.fen1.block.magic = "FEN1"
        self.fen1.block.size = 0
        self.binary.write_header(writer)

        self.flw3.write(writer)
        self.fen1.write(writer)

        writer.seek(0, 2)
        size = writer.tell()
        writer.seek(18)
        writer.write_uint32(size)
