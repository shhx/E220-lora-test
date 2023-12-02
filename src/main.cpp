#include <Arduino.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include "SPIFFS.h"
// #include <ArduinoJson.h>
#include "E220.h"
#include "config_e220.h"
#include "command.h"
#include "wifi_config.h"

//Define the pins we need to use later to create the object
// t-display PINS
// #define AUX 25
// #define M0 15
// #define M1 2
// #define TX_PIN 17
// #define RX_PIN 22

#define AUX 6
#define M0 8
#define M1 7
#define MAX_TEXT_LEN 20

// Create AsyncWebServer object on port 80
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");
E220 radioModule(&Serial0, M0, M1, AUX);
String rx_message = "";
size_t last_rx_msg = 0;


typedef struct  __attribute__((packed)){
	float temperature;
	uint32_t seq_num;
} Message_t;

typedef struct  __attribute__((packed)){
	char text[MAX_TEXT_LEN];
    bool end;
	uint32_t seq_num;
} TextMessage_t;

typedef struct __attribute__((packed)){
    TextMessage_t msg;
    uint8_t rssi;
} MessageRSSI_t;

uint32_t seq_num = 0;
size_t t0 = 0;
bool ws_connected = true;
String sensorReadings;

bool e220_default_config(){
    bool success = true;
    success &= radioModule.setAddress(E220_ADDRESS, true);
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
    size_t read = Serial0.readBytes((uint8_t*)packet, sizeof(MessageRSSI_t));
    if (read != sizeof(MessageRSSI_t)) {
        return false;
    }
    return true;
}

// Initialize SPIFFS
void initSPIFFS() {
    if (!SPIFFS.begin(true)) {
        Serial.println("An error has occurred while mounting SPIFFS");
    }
    Serial.println("SPIFFS mounted successfully");
}

// Initialize WiFi
void init_wifi_ap() {
    WiFi.mode(WIFI_MODE_AP);
    WiFi.setTxPower(WIFI_POWER_8_5dBm);
    // WiFi.setTxPower(WIFI_POWER_MINUS_1dBm);
    bool ret = WiFi.softAPConfig(IPAddress(192, 168, 1, 4), IPAddress(192, 168, 1, 1), IPAddress(255, 255, 255, 0));
    ret = WiFi.softAP("ESP32-wtf", "123456789");
    if (!ret) {
        Serial.println("Failed to create AP");
    }
    // WiFi.config(INADDR_NONE, INADDR_NONE, INADDR_NONE);
    IPAddress IP = WiFi.softAPIP();
    Serial.print("AP IP address: ");
    Serial.println(IP);
}

void init_wifi_sta() {
    WiFi.begin(SSID, PASS);
    WiFi.setTxPower(WIFI_POWER_8_5dBm);
    Serial.print("Connecting to WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println();
    Serial.print("Connected, IP address: ");
    Serial.println(WiFi.localIP());
}

void handleWebSocketMessage(void *arg, uint8_t *data, size_t len) {
    AwsFrameInfo *info = (AwsFrameInfo*)arg;
    if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
        String message = (char*)data;
        size_t message_len = message.length();
        Serial.print("Message: ");
        Serial.println(message);
        int i = 0;
        while (message_len > MAX_TEXT_LEN) {
            TextMessage_t msg = {.end = false, .seq_num = seq_num++};
            memcpy(msg.text, &message[i], MAX_TEXT_LEN);
            Serial.print("Sending: ");
            Serial.println(msg.text);
            radioModule.sendFixedData(DESTINATION_ADDL, E220_CHANNEL, (uint8_t*)&msg, sizeof(msg), true);
            message_len -= MAX_TEXT_LEN;
            i += MAX_TEXT_LEN;
        }
        TextMessage_t msg = {.end = true, .seq_num = seq_num++};
        memcpy(msg.text, &message[i], message_len);
        Serial.print("Sending: ");
        Serial.println(msg.text);
        radioModule.sendFixedData(DESTINATION_ADDL, E220_CHANNEL, (uint8_t*)&msg, sizeof(msg), true);
    }
}

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len) {
    switch (type) {
        case WS_EVT_CONNECT: 
            ws_connected = true;
            Serial.printf("WebSocket client #%u connected from %s\n", client->id(), client->remoteIP().toString().c_str());
            break;
        case WS_EVT_DISCONNECT:
            ws_connected = false;
            Serial.printf("WebSocket client #%u disconnected\n", client->id());
            break;
        case WS_EVT_DATA:
            handleWebSocketMessage(arg, data, len);
            break;
        case WS_EVT_PONG:
        case WS_EVT_ERROR:
            Serial.println("WebSocket error");
            break;
    }
}

void initWebSocketServer() {
    ws.onEvent(onEvent);
    server.addHandler(&ws);
}

void setup(){
    Serial.begin(115200);
    Serial0.begin(E220_SERIAL_SPEED);
    // Serial1.begin(E220_SERIAL_SPEED, SERIAL_8N1, RX_PIN, TX_PIN);
    // initialise the module and check it communicates with us, else loop and keep trying
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
    radioModule.printBoardParameters();

    initSPIFFS();
    init_wifi_sta();
    initWebSocketServer();
    // Web Server Root URL
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
        Serial.println("Request received");
        request->send(SPIFFS, "/index.html", "text/html");
    });

    server.serveStatic("/", SPIFFS, "/");
    server.begin();
    t0 = millis();
}


void loop(){
    MessageRSSI_t packet = {0};
    size_t t1 = millis();
    if (t1 - t0 > 1000) {
        // packet.msg.seq_num = seq_num++;
        // radioModule.sendFixedData(DESTINATION_ADDL, E220_CHANNEL, (uint8_t*)&packet.msg, sizeof(Message_t), true);
        t0 = t1;
    } 

    bool ret = parse_cmd(radioModule);
    if(Serial0.available()){
        Serial.println("Reading packet");
        last_rx_msg = millis();
        if (read_packet_rssi(&packet)) {
            Serial.print("New packet: ");
            Serial.println(packet.msg.text);
            if (ws_connected) {
                rx_message += packet.msg.text;
                if (packet.msg.end) {
                    ws.textAll(rx_message);
                    rx_message = "";
                }
            }
        } else {
            Serial.println("Failed to read packet");
        }
    }

    if (millis() - last_rx_msg > 1000 && rx_message.length() > 0) {
        ws.textAll(rx_message + "...");
        rx_message = "";
    }
}
