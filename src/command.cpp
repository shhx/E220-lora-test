#include <Arduino.h>
#include "command.h"

void send_response(uint8_t cid, ResponseStatus status) {

    Response_t resp = {
        .cid = cid,
        .status = status,
    };
    send_packet((uint8_t*)&resp, sizeof(resp), PACKET_TYPE_RESP);
}

void send_packet(uint8_t *packet, size_t len, uint8_t type) {
    uint8_t checksum = 0;
    for (size_t i = 0; i < len; i++) {
        checksum ^= packet[i];
    }
    PacketHeader_t header = {0};
    header.header = PACKET_HEADER;
    header.type = type;
    header.length = len;
    header.checksum = checksum;
    Serial.write((uint8_t*)&header, sizeof(PacketHeader_t));
    Serial.write(packet, len);
}

bool parse_cmd(E220 &radioModule) {
    Command_t cmd;
    if(Serial.available()) {
        size_t bytes_read = Serial.readBytes((uint8_t*)&cmd, sizeof(cmd));
        if (bytes_read == sizeof(cmd)) {
            if (cmd.header != PACKET_HEADER) {
                // Serial.println("NOK, invalid header");
                return false;
            }
            bool ret = false;
            switch (cmd.cid) {
                case SET_TX_POWER:
                    ret = radioModule.setPower(cmd.value, true);
                    break;
                case SET_AIR_DATA_RATE:
                    ret = radioModule.setAirDataRate(cmd.value, true);
                    break;
                case SET_UART_BAUD_RATE:
                    ret = radioModule.setBaud(cmd.value, true);
                    break;
                case GET_CONFIG:
                    {
                        ret = radioModule.readBoardData();
                        if (!ret) {
                            return false;
                        }
                        Config_t cfg = {
                            .tx_power = radioModule.getPower(),
                            .air_data_rate = radioModule.getAirDataRate(),
                            .uart_baud_rate = radioModule.getBaud(),
                        };
                        send_packet((uint8_t*)&cfg, sizeof(cfg), PACKET_TYPE_CONFIG);
                        return true;
                    }
                default:
                    send_response(cmd.cid, CMD_NOK);
                    return false;
            }
            send_response(cmd.cid, ret ? CMD_OK : CMD_NOK);
            return ret;
        }
        return false;
    }
    return false;
}
