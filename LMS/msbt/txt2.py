from LMS.common.lms_block import LMS_Block
from LMS.module.reader import Reader
from LMS.module.writer import Writer

class TXT2:
    def __init__(self):
        self.block = LMS_Block()
        self.messages: list[str] = []

    def read(self, reader: Reader) -> None:
        self.block.read_header(reader)
        message_count = reader.read_uint32()

        offsets = []
        for _ in range(message_count):
            offset = reader.read_uint32() + self.block.data_start
            offsets.append(offset)

        for i, offset in enumerate(offsets):
            # Instead of reading the UTF-16 string as a regular string with read_utf16_string
            # the next offset is obtained so a unicode decode error does not occur when the function encounters
            # a control tag
            next_offset = (
                offsets[i + 1]
                if i < len(offsets) - 1
                else self.block.data_start + self.block.size
            )
            reader.seek(offset)

            # Parse messages including control tags
            message = b""
            while reader.tell() < next_offset:
                char = reader.read_bytes(1)
                if char == b"\x0E":
                    reader.skip(1)
                    group = reader.read_uint16()
                    type = reader.read_uint16()
                    size = reader.read_uint16()
                    parameters = reader.read_bytes(size)
                    hex_parameters = parameters.hex()
                    parameters = '-'.join([hex_parameters[i] + hex_parameters[i + 1] for i in range(0, len(hex_parameters), 2)]).split("-")
                    tag = f"[n{group}.{type}:{hex_parameters}]".encode("UTF-16-LE")
                    message += tag
                else:
                    message += char
                    i += 1
            self.messages.append(message.decode("UTF-16-LE"))
                    
            

            
               

                
                   
           
                                  

                


                
            

                
            
                        



                        
                        
                       
                        

                    

                    
                    
                    
                 

                        

                        
                            

                                
                   

                     
            
        
