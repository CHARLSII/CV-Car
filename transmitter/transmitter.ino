#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEClient.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

#define BUTTON_PIN 23
String incomingData = "";

// BLE
BLEClient* pClient;
BLERemoteCharacteristic* pRemoteCharacteristic;
bool connected = false;

const char* serverName = "ESP32_RC_Car";

// ----------------------------------------------------
// Scan and connect to BLE server
// ----------------------------------------------------
void connectToServer() {
    Serial.println("Scanning for BLE server...");

    BLEScan* scanner = BLEDevice::getScan();
    scanner->setActiveScan(true);

    BLEScanResults* results = scanner->start(5);  // <-- FIXED (pointer)

    if (!results) {
        Serial.println("Scan failed (null results).");
        return;
    }

    int count = results->getCount();
    Serial.printf("Found %d devices\n", count);

    for (int i = 0; i < count; i++) {
        BLEAdvertisedDevice device = results->getDevice(i);

        if (device.getName() == serverName) {
            Serial.println("Found BLE server! Connecting...");

            if (pClient->connect(&device)) {
                Serial.println("Connected!");

                BLERemoteService* service =
                    pClient->getService(BLEUUID((uint16_t)0x181C));

                if (service) {
                    pRemoteCharacteristic =
                        service->getCharacteristic(BLEUUID((uint16_t)0x2A56));

                    if (pRemoteCharacteristic) {
                        connected = true;
                        Serial.println("Characteristic ready!");
                    }
                }
            }
            break;
        }
    }

    // free memory
    scanner->clearResults();
    results->~BLEScanResults();

    if (!connected) {
        Serial.println("Failed to connect.");
    }
}

// ----------------------------------------------------
void setup() {
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

    Serial.begin(115200);
    pinMode(BUTTON_PIN, INPUT_PULLUP);

    BLEDevice::init("");
    pClient = BLEDevice::createClient();

    connectToServer();
}

// ----------------------------------------------------
void loop() {

    // Reconnection logic
    if (connected && !pClient->isConnected()) {
        Serial.println("BLE disconnected. Reconnecting...");
        connected = false;
        connectToServer();
    } 
    else if (!connected) {
        connectToServer();
    }

    // ----------------------------------------------
    // Read serial commands from Python
    // ----------------------------------------------
    while (Serial.available()) {
        char c = Serial.read();

        if (c == '\n') {
            if (connected && pRemoteCharacteristic) {
                Serial.print("Sending BLE: ");
                Serial.println(incomingData);
                pRemoteCharacteristic->writeValue(incomingData.c_str());
            }
            incomingData = "";
        } else {
            incomingData += c;
        }
    }

    // ----------------------------------------------
    // Manual button override
    // ----------------------------------------------
    static bool lastState = HIGH;
    bool currentState = digitalRead(BUTTON_PIN);

    if (connected) {
        if (currentState == LOW && lastState == HIGH) {
            pRemoteCharacteristic->writeValue("Forward");
            Serial.println("Button → Forward");
        }
        if (currentState == HIGH && lastState == LOW) {
            pRemoteCharacteristic->writeValue("Stop");
            Serial.println("Button → Stop");
        }
    }

    lastState = currentState;

    delay(10);
}
