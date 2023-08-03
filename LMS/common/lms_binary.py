from enum import Enum
from LMS.module.reader import Reader
from LMS.module.writer import Writer


class LMS_MessageEncoding(Enum):
    UTF8 = 0
    UTF16 = 1
    UTF32 = 2


class LMS_Binary:
    def __init__(self):
        self.magic: str = None
        self.bom: str = None
        self.encoding: LMS_MessageEncoding = None
        self.revision: int = None
        self.block_count: int = None
        self.file_size: int = None

    def read_header(self, reader: Reader) -> None:
        self.magic = reader.read_string_len(8)
        self.bom = "little" if reader.read_bytes(2) == b"\xFF\xFE" else "big"
        reader.skip(2)
        self.encoding = LMS_MessageEncoding(reader.read_uint8())
        self.revision = reader.read_uint8()
        self.block_count = reader.read_uint16()
        reader.skip(2)
        self.file_size = reader.read_uint32()
        reader.skip(10)

    def write_header(self, writer: Writer) -> None:
        writer.write_string(self.magic)
        writer.write_bytes(b"\xFF\xFE" if self.bom == "little" else b"\xFE\xFF")
        writer.write_bytes(b"\x00\x00")

        writer.write_uint8(self.encoding.value)
        writer.write_uint8(self.revision)
        writer.write_uint16(self.block_count)
        writer.write_bytes(b"\x00\x00")
        writer.write_uint32(0)
        writer.write_bytes(b"\x00" * 10)

    def search_block_by_name(self, reader: Reader, name: str) -> int:
        blocks = self.search_all_blocks(reader)
        return blocks[name] if name in blocks else -1

    def search_all_blocks(self, reader: Reader) -> dict[str:int]:
        result = {}
        reader.seek(32)
        block_count = self.block_count

        for _ in range(block_count):
            offset = reader.tell()
            magic = reader.read_string_len(4)
            size = reader.read_uint32()
            reader.skip(8)
            reader.seek(size, 1)
            remainder = 16 - size % 16
            if remainder != 16:
                reader.skip(remainder)
            result[magic] = offset

        return result
