from LMS.common.lms_block import LMS_Block
from LMS.module.reader import Reader
from LMS.module.writer import Writer


class TXT2:
    def __init__(self):
        self.block = LMS_Block()
        self.messages: list[str] = []

    def read(self, reader: Reader, byte_order: str) -> None:
        self.block.read_header(reader)
        message_count = reader.read_uint32()

        offsets = []
        for _ in range(message_count):
            offset = reader.read_uint32() + self.block.data_start
            offsets.append(offset)

        for i, offset in enumerate(offsets):
            next_offset = (
                offsets[i + 1]
                if i < len(offsets) - 1
                else self.block.data_start + self.block.size
            )
            reader.seek(offset)

            message = b""
            tag_data = {
                "little": b"\x0E\x00",
                "big": b"\x00\x0E"
            }
            while reader.tell() < next_offset:
                bytes = reader.read_bytes(2)
                if bytes == tag_data[byte_order]:
                    tag = self.parse_control_tag(reader).encode(
                        "UTF-16-LE" if byte_order == "little" else "UTF-16-BE")
                    message += tag
                else:
                    message += bytes

            self.messages.append(message.decode(
                "UTF-16-LE") if byte_order == "little" else message.decode("UTF-16-BE"))

    def parse_control_tag(self, reader: Reader):
        group = reader.read_uint16()
        type = reader.read_uint16()
        size = reader.read_uint16()
        raw_parameters = reader.read_bytes(size)
        hex_parameters = raw_parameters.hex()
        parameters = '-'.join([hex_parameters[i] + hex_parameters[i + 1]
                              for i in range(0, len(hex_parameters), 2)])
        return f"[n{group}.{type}:{parameters}]"
