from LMS.module.reader import Reader
from LMS.module.writer import Writer
from LMS.common.lms_block import LMS_Block
from LMS.common.lms_binary import LMS_Binary


class LMS_HashTableBlock:
    def __init__(self):
        self.block = LMS_Block()
        self.labels: dict[str:int] = {}
        self.index = 0

    def get_index_by_label(self, label: str):
        for key in self.labels:
            if self.labels[key] == label:
                return key

    def read(self, reader: Reader) -> None:
        self.block.read_header(reader)
        slot_count = reader.read_uint32()

        for _ in range(slot_count):
            label_count = reader.read_uint32()
            offset = reader.read_uint32()
            end = reader.tell()
            reader.seek(self.block.data_start)
            reader.seek(offset, 1)

            for _ in range(label_count):
                length = reader.read_uint8()
                label = reader.read_string_len(length)
                item_index = reader.read_uint32()
                self.labels[item_index] = label

            reader.seek(end)

    def calc_hash(self, label, num_slots):
        hash = 0
        for char in label:
            hash = hash * 0x492 + ord(char)
        return (hash & 0xFFFFFFFF) % num_slots

    def write(self, writer: Writer, slot_count: int = 59):
        self.block.write_header(writer)
        self.block.data_start = writer.tell()
        writer.write_uint32(slot_count)

        hash_slots = {}
        for index in self.labels:
            label = self.labels[index]
            hash_slots[self.calc_hash(label, slot_count)] = []

        for index in self.labels:
            label = self.labels[index]
            hash = self.calc_hash(label, slot_count)
            if hash in hash_slots:
                hash_slots[hash].append(label)
            else:
                hash_slots[hash] = [label]

        size = 0
        offset_to_labels = slot_count * 8 + 4
        size += offset_to_labels

        hash_slots = ordered = dict(
            sorted(hash_slots.items(), key=lambda x: x[0]))

        for i in range(slot_count):
            if i in hash_slots:
                writer.write_uint32(len(hash_slots[i]))
                writer.write_uint32(offset_to_labels)

                for label in ordered[i]:
                    offset_to_labels += len(label) + 5
            else:
                writer.write_uint32(0)
                writer.write_uint32(offset_to_labels)

        for key in hash_slots:
            labels = hash_slots[key]
            for label in labels:
                label_index = self.get_index_by_label(label)
                writer.write_uint8(len(label))
                writer.write_string(label)
                writer.write_uint32(label_index)
                size += 5 + len(label)

        self.block.size = size
        self.block.write_ab_padding(writer)
        self.block.write_size(writer)
        self.block.seek_to_end(writer)
