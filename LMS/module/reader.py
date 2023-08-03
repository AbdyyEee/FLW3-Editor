import struct 
from io import  BytesIO

le_types = {
    "uint8": "<B",
    "uint16": "<H",
    "uint32": "<I"
}
be_types = {
    "uint8": ">B",
    "uint16": ">H",
    "uint32": ">I"
}

class Reader:
    def __init__(self, data: bytes, byte_order: str = "little"):
        self.data = BytesIO(data) 
        self.byte_order = byte_order
        self.types = le_types if byte_order == "little" else be_types

    def skip(self, length: int) -> None:
        self.data.read(length)

    def read_bytes(self, length: int) -> None:
        return self.data.read(length)
    
    def seek(self, offset: int, whence: int = 0) -> None:
        self.data.seek(offset, whence)

    def tell(self) -> int:
        return self.data.tell()
    
    def read_uint8(self) -> int:
        return struct.unpack(self.types["uint8"], self.data.read(1))[0]
    
    def read_uint16(self) -> int:
        return struct.unpack(self.types["uint16"], self.data.read(2))[0]

    def read_uint32(self) -> int:
        return struct.unpack(self.types["uint32"], self.data.read(4))[0]

    def read_string_len(self, length: int) -> str:
        return self.data.read(length).decode("UTF-8")

    def read_string_nt(self) -> str:
        result = b""
        char = self.data.read(1)
        while char != b"\x00":
            result += char
            char = self.data.read(1)
        return result.decode("UTF-8")
    
    def read_utf16_string(self):
        message = b""
        byte = self.data.read(2)
        while True:
            if byte == b"\x00\x00":
                break
            message += byte
            byte = self.data.read(2)

        return message.decode("UTF-16")

