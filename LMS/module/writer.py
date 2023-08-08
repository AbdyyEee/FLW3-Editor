import struct
from io import BufferedWriter

le_types = {"uint8": "<B", "uint16": "<H", "uint32": "<I"}
be_types = {"uint8": ">B", "uint16": ">H", "uint32": ">I"}


class Writer:
    def __init__(self, file: BufferedWriter, byte_order: str = "little"):
        self.file = file
        self.byte_order = byte_order
        self.types = le_types if byte_order == "little" else be_types

    def change_byte_order(self, byte_order: str):
        self.byte_order = byte_order
        self.types = le_types if byte_order == "little" else be_types

    def skip(self, length: int) -> None:
        self.data.read(length)

    def write_bytes(self, data: bytes) -> None:
        self.file.write(data)

    def seek(self, offset: int, whence: int = 0) -> None:
        self.file.seek(offset, whence)

    def tell(self) -> int:
        return self.file.tell()

    def write_string_nt(self, string: str) -> None:
        self.file.write(string.encode("UTF-8") + b"\x00")

    def write_string(self, string: str) -> None:
        self.file.write(string.encode("UTF-8"))

    def write_utf16_string(self, string: str, use_double=False) -> None:
        self.file.write(string.encode("UTF-16-LE"))
        if use_double:
            self.file.write(b"\x00\x00")

    def write_uint8(self, num: int):
        self.file.write(struct.pack(self.types["uint8"], num))

    def write_uint16(self, num: int):
        self.file.write(struct.pack(self.types["uint16"], num))

    def write_uint32(self, num: int):
        self.file.write(struct.pack(self.types["uint32"], num))
