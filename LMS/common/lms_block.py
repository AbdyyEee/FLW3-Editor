from LMS.module.reader import Reader
from LMS.module.writer import Writer


class LMS_Block:
    def __init__(self):
        self.magic: str = None
        self.size: int = 0
        self.data_start: int = None

    def read_header(self, reader: Reader):
        self.magic = reader.read_string_len(4)
        self.size = reader.read_uint32()
        reader.skip(8)
        self.data_start = reader.tell()

    def seek_to_end(self, object: Reader | Writer):
        object.seek(self.data_start)
        object.seek(self.size, 1)
        remainder = 16 - self.size % 16
        object.seek(remainder, 1)

    def write_header(self, writer: Writer):
        writer.write_string(self.magic)
        writer.write_uint32(0)
        writer.write_bytes(b"\x00" * 8)

    def write_ab_padding(self, writer: Writer):
        remainder = 16 - self.size % 16
        if remainder == 16:
            return 0
        writer.write_bytes(b"\xAB" * remainder)
        return remainder

    def write_size(self, writer: Writer):
        writer.seek(self.data_start - 12)
        writer.write_uint32(self.size)

    def write_end_data(self, writer: Writer):
        remainder = self.write_ab_padding(writer)
        if remainder == 0:
            return
        self.write_size(writer)
        self.seek_to_end(writer)
