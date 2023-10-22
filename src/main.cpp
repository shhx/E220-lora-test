#include <Arduino.h>
#include "E220.h"
#include "config_e220.h"
#include "command.h"

//Define the pins we need to use later to create the object
#define AUX 25
#define M0 15
#define M1 2
#define TX_PIN 17
#define RX_PIN 22
#define DESTINATION_ADDL 3

E220 radioModule(&Serial1, M0, M1, AUX);

typedef struct  __attribute__((packed)){
	float temperature;
	uint32_t seq_num;
} Message_t;

typedef struct __attribute__((packed)){
    Message_t msg;
    uint8_t rssi;
} MessageRSSI_t;

uint32_t seq_num = 0;
size_t t0 = 0;

bool e220_default_config(){
    bool success = true;
    success &= radioModule.setAirDataRate(E220_AIR_DATA_RATE, true);
    success &= radioModule.setBaud(E220_BAUD_RATE, true);
    success &= radioModule.setChannel(E220_CHANNEL, true);
    success &= radioModule.setPower(E220_POWER, true);
    success &= radioModule.setSubPacketSize(E220_SUB_PACKET_SIZE, true);
    success &= radioModule.setParity(E220_UART_PARITY, true);
    success &= radioModule.setRSSIByteToggle(E220_RSSI_ENABLE, true);
    success &= radioModule.setRadioMode(E220_MODE);
    success &= radioModule.setFixedTransmission(true, true);
    return success;
}

bool read_packet_rssi(MessageRSSI_t *packet) {
    size_t read = Serial2.readBytes((uint8_t*)packet, sizeof(MessageRSSI_t));
    if (read != sizeof(MessageRSSI_t)) {
        return false;
    }
    return true;
}

void setup(){
    //begin all of our UART connections
    Serial.begin(115200);
    Serial1.begin(E220_SERIAL_SPEED, SERIAL_8N1, RX_PIN, TX_PIN);

    //initialise the module and check it communicates with us, else loop and keep trying
    while(!radioModule.init()){
        delay(500);
    }
    bool ret = e220_default_config();
    if (!ret) {
        Serial.println("Failed to configure");
    } else {
        Serial.println("Configured");
    }
    radioModule.readBoardData();
    t0 = millis();
}


void loop(){
    MessageRSSI_t packet = {0};
    size_t t1 = millis();
    if (t1 - t0 > 1000) {
        packet.msg.seq_num = seq_num++;
        radioModule.sendFixedData(DESTINATION_ADDL, E220_CHANNEL, (uint8_t*)&packet.msg, sizeof(Message_t), true);
        t0 = t1;
    } 

    bool ret = parse_cmd(radioModule);
    if(Serial2.available()){
        if(read_packet_rssi(&packet)){
            send_packet((uint8_t*)&packet, sizeof(MessageRSSI_t), PACKET_TYPE_DATA);
            // Serial.print("Send time: ");
            // Serial.println(t1 - t0);
        } else {
            // Serial.println("Failed to read packet");
        }
    }
}
