import struct # Упаковка данных в байты и распаковка

class SizeProtocol:
    MSG_SIZE = 4096  # Размер буфера по умолчанию
    
    @staticmethod
    def recv(connected_socket):
        """Приём данных: сначала размер, затем само содержимое."""
        data = connected_socket.recv(struct.calcsize('I')) # Чтение размера данных
        if not data: # Если соединение закрыто
            return None
        size, = struct.unpack('I', data) # Преобразование байтов размера в число
        
        # Чтение самих данных
        res_data = b''
        while len(res_data) < size: # Чтение данных порциями
            chank_size = min(SizeProtocol.MSG_SIZE, size - len(res_data)) # Чтобы не запросить лишние байты
            packet = connected_socket.recv(chank_size)
            if not packet:
                break
            res_data += packet
        return res_data.decode('utf-8') # Преобразование байтов в строку
    
    @staticmethod
    def send(connected_socket, text):
        """Отправка данных: размер + содержимое."""
        text_data = text.encode('utf-8') # Преобразование строки в байты
        connected_socket.send(struct.pack('I', len(text_data))) # Упаковка и отправка размера 
        connected_socket.sendall(text_data) # Отправка самих данных
