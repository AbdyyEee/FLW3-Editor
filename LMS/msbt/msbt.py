from LMS.common.lms_binary import LMS_Binary
from LMS.common.lms_hashtable import LMS_HashTableBlock
from LMS.module.reader import Reader
from LMS.module.writer import Writer
from LMS.common.lms_binary import LMS_MessageEncoding
from LMS.msbt.txt2 import TXT2

class MSBT:
    def __init__(self):
        self.binary = LMS_Binary()
        self.lbl1 = LMS_HashTableBlock()
        self.txt2 = TXT2()

    def read(self, reader: Reader) -> None:
        self.binary.read_header(reader) 
       
        lbl1_offset = self.binary.search_block_by_name(reader, "LBL1")
        txt2_offset = self.binary.search_block_by_name(reader, "TXT2")

        reader.seek(lbl1_offset)
        self.lbl1.read(reader)

        reader.seek(txt2_offset)
        self.txt2.read(reader, self.binary.bom)
