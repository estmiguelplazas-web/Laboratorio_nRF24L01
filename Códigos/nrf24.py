#nrf24.py
import time

class NRF24:
    def __init__(self, spi, csn, ce, payload=32, addr=b"UMNG1"):
        self.spi, self.csn, self.ce = spi, csn, ce
        self.payload = payload
        self.cfg = 0x0C                    # CRC activado, 2 bytes
        self.csn(1)
        self.ce(0)
        time.sleep_ms(100)
        self.write_reg(0x00, self.cfg)     # CONFIG
        self.write_reg(0x01, 0x01)         # auto-ACK en pipe 0
        self.write_reg(0x02, 0x01)         # habilitar pipe 0
        self.write_reg(0x03, 0x03)         # direcciones de 5 bytes
        self.write_reg(0x04, 0x2F)         # 15 reintentos, espera 750 us
        self.write_reg(0x05, 40)           # canal inicial
        self.write_reg(0x06, 0x06)         # 1 Mbps, 0 dBm
        self.write_reg(0x10, addr)         # TX_ADDR
        self.write_reg(0x0A, addr)         # RX_ADDR_P0
        self.write_reg(0x11, payload)      # tamano del payload
        self.cmd(0xE1)                     # flush TX
        self.cmd(0xE2)                     # flush RX
        self.write_reg(0x07, 0x70)         # limpiar banderas

    # ----- SPI basico -----
    def cmd(self, c):
        self.csn(0)
        self.spi.write(bytes([c]))
        self.csn(1)

    def write_reg(self, reg, val):
        if isinstance(val, int):
            val = bytes([val])
        self.csn(0)
        self.spi.write(bytes([0x20 | reg]) + val)
        self.csn(1)

    def read_reg(self, reg):
        rx = bytearray(2)
        self.csn(0)
        self.spi.write_readinto(bytes([reg, 0xFF]), rx)
        self.csn(1)
        return rx[1]

    def status(self):
        rx = bytearray(1)
        self.csn(0)
        self.spi.write_readinto(b'\xff', rx)
        self.csn(1)
        return rx[0]

    # ----- Configuracion -----
    def set_channel(self, ch):
        # RF_CH admite 0..125  ->  f = 2400 + ch (MHz)  ->  2400 a 2525 MHz
        ch = max(0, min(125, int(ch)))
        self.write_reg(0x05, ch)

    def get_channel(self):
        return self.read_reg(0x05)

    def set_power(self, level):            # 0=-18, 1=-12, 2=-6, 3=0 dBm
        rf = self.read_reg(0x06) & 0xF9
        self.write_reg(0x06, rf | (level << 1))

    def set_datarate(self, vel):           # "250K", "1M" o "2M"
        rf = self.read_reg(0x06) & 0xD7
        rf |= {"250K": 0x20, "1M": 0x00, "2M": 0x08}[vel]
        self.write_reg(0x06, rf)

    # ----- Transmisor -----
    def send(self, data, timeout_ms=300):
        data = bytes(data)[:self.payload]
        data = data + bytes(self.payload - len(data))
        self.ce(0)
        self.write_reg(0x00, self.cfg | 0x02)      # PWR_UP, modo TX
        time.sleep_ms(2)
        self.cmd(0xE1)
        self.write_reg(0x07, 0x70)
        self.csn(0)
        self.spi.write(b'\xA0' + data)             # W_TX_PAYLOAD
        self.csn(1)
        self.ce(1)
        time.sleep_us(20)
        self.ce(0)
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            st = self.status()
            if st & 0x20:                          # TX_DS: enviado con ACK
                self.write_reg(0x07, 0x20)
                return True
            if st & 0x10:                          # MAX_RT: sin ACK
                self.write_reg(0x07, 0x10)
                self.cmd(0xE1)
                return False
        self.cmd(0xE1)
        return False

    # ----- Receptor -----
    def start_rx(self):
        self.ce(0)
        self.write_reg(0x00, self.cfg | 0x03)      # PWR_UP, modo RX
        time.sleep_ms(5)
        self.write_reg(0x07, 0x70)
        self.cmd(0xE2)
        self.ce(1)
        time.sleep_us(150)

    def available(self):
        return not (self.read_reg(0x17) & 0x01)    # FIFO_STATUS: RX no vacio

    def recv(self):
        rx = bytearray(self.payload + 1)
        self.csn(0)
        self.spi.write_readinto(b'\x61' + bytes(self.payload), rx)   # R_RX_PAYLOAD
        self.csn(1)
        self.write_reg(0x07, 0x40)
        return bytes(rx[1:])
