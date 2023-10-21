from ctypes import (Array, LittleEndianStructure, c_float, c_uint8, c_uint16,
                    c_uint32)
from enum import IntEnum


class PackedStructure(LittleEndianStructure):
    """The standard ctypes Structure, but tightly packed (no field padding), and with a proper repr() function.
    This is the base type for all structures in packets data.
    """

    _pack_ = 1

    def __repr__(self):
        """Return a string representation of the structure."""
        fstr_list = []
        for (fname, _) in self._fields_:
            value = getattr(self, fname)
            if isinstance(value, (PackedStructure, int, float, bytes)):
                vstr = repr(value)
            elif isinstance(value, Array):
                vstr = "[{}]".format(", ".join(repr(e) for e in value))
            else:
                raise RuntimeError("Bad value {!r} of type {!r}".format(value, type(value)))
            fstr = "{}={}".format(fname, vstr)
            fstr_list.append(fstr)

        return "{}({})".format(self.__class__.__name__, ", ".join(fstr_list))

class AirSpeed(IntEnum):
    AIR_DATA_RATE_000_24 = 0b000
    AIR_DATA_RATE_001_24 = 0b001
    AIR_DATA_RATE_010_24 = 0b010
    AIR_DATA_RATE_011_48 = 0b011
    AIR_DATA_RATE_100_96 = 0b100
    AIR_DATA_RATE_101_192 = 0b101
    AIR_DATA_RATE_110_384 = 0b110
    AIR_DATA_RATE_111_625 = 0b111

class UARTSpeed(IntEnum):
    UART_DATA_RATE_1200 = 0b000
    UART_DATA_RATE_2400 = 0b001
    UART_DATA_RATE_4800 = 0b010
    UART_DATA_RATE_9600 = 0b011
    UART_DATA_RATE_19200 = 0b100
    UART_DATA_RATE_38400 = 0b101
    UART_DATA_RATE_57600 = 0b110
    UART_DATA_RATE_115200 = 0b111

class TxPower(IntEnum):
    POWER_30 = 0b00
    POWER_27 = 0b01
    POWER_24 = 0b10
    POWER_21 = 0b11

class CmdID(IntEnum):
    TX_POWER = 0
    AIR_SPEED = 1
    UART_DATA_RATE = 2
    GET_CONFIG = 3

class ResponseStatus(IntEnum):
    OK = 0
    NOK = 1

class Command(PackedStructure):
    _pack_ = 1
    _fields_ = [
        ("header", c_uint16),
        ("cid",  c_uint8),  # Command ID
        ("value", c_uint8), # Command Value
    ]

class Config(PackedStructure):
    _pack_ = 1
    _fields_ = [
        ("tx_power", c_uint8),
        ("air_speed", c_uint8),
        ("uart_speed", c_uint8),
    ]

class Response(PackedStructure):
    _pack_ = 1
    _fields_ = [
        ("cid",  c_uint8),
        ("status", c_uint8),
    ]

    def __repr__(self) -> str:
        return f"Response(cid={CmdID(self.cid).name}, status={ResponseStatus(self.status).name})"

class PacketType(IntEnum):
    DATA = 0
    RESPONSE = 1
    CONFIG = 2

class PacketHeader(PackedStructure):
    _pack_ = 1
    _fields_ = [
        ("header", c_uint16),
        ("length", c_uint16),
        ("type", c_uint8),
        ("checksum", c_uint8),
    ]

class Message(PackedStructure):
    _pack_ = 1
    _fields_ = [
        ("temperature", c_float),
        ("seq_num", c_uint32),
    ]

class MessageRSSI(PackedStructure):
    _pack_ = 1
    _fields_ = [
        ("msg", Message),
        ("rssi", c_uint8),
    ]
