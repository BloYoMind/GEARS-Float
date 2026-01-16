#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClient.h>
#include <Wire.h>
#include <FS.h>
#include <SPIFFS.h>

// ======================================================
// ADS1115 DRIVER (C++ translation of your MicroPython version)
// ======================================================

class ADS1115 {
public:
    ADS1115(TwoWire &i2c = Wire, uint8_t address = 0x48, uint8_t gain = 1)
        : i2c(i2c), address(address), gain(gain) {}

    void begin() {
        i2c.begin();
    }

    float raw_to_v(int16_t raw) {
        static const float GAINS_V[6] = {
            6.144f, 4.096f, 2.048f, 1.024f, 0.512f, 0.256f
        };
        float v_per_bit = GAINS_V[gain] / 32768.0f;
        return raw * v_per_bit;
    }

    int16_t read(uint8_t channel = 0, uint8_t rate = 4) {
        uint16_t config =
            0x8000 |                      // OS_SINGLE
            (0x4000 + (channel << 12)) |  // MUX_SINGLE_x
            GAINS[gain] |
            RATES[rate] |
            0x0100 |                      // MODE_SINGLE
            0x0003;                       // Disable comparator

        writeRegister(0x01, config);

        while (!(readRegister(0x01) & 0x8000)) {
            delay(1);
        }

        return readRegister(0x00);
    }

private:
    TwoWire &i2c;
    uint8_t address;
    uint8_t gain;

    const uint16_t GAINS[6] = {
        0x0000, 0x0200, 0x0400, 0x0600, 0x0800, 0x0A00
    };

    const uint16_t RATES[8] = {
        0x0000, 0x0020, 0x0040, 0x0060,
        0x0080, 0x00A0, 0x00C0, 0x00E0
    };

    void writeRegister(uint8_t reg, uint16_t value) {
        i2c.beginTransmission(address);
        i2c.write(reg);
        i2c.write(value >> 8);
        i2c.write(value & 0xFF);
        i2c.endTransmission();
    }

    int16_t readRegister(uint8_t reg) {
        i2c.beginTransmission(address);
        i2c.write(reg);
        i2c.endTransmission();

        i2c.requestFrom(address, (uint8_t)2);
        uint16_t hi = i2c.read();
        uint16_t lo = i2c.read();
        uint16_t raw = (hi << 8) | lo;

        return (raw < 32768) ? raw : raw - 65536;
    }
};

// ======================================================
// GLOBALS
// ======================================================

String html = "";
unsigned long startTime = 0;
bool debugMode = false;

ADS1115 ads(Wire, 0x48, 1);

WiFiServer server(80);

// ======================================================
// UTILITY
// ======================================================

float mapFloat(float x, float in_min, float in_max, float out_min, float out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

String loadFile(const char* path) {
    File f = SPIFFS.open(path, "r");
    if (!f) return "";
    String s = f.readString();
    f.close();
    return s;
}

// ======================================================
// SQUID CONTROL CLASS
// ======================================================

class SquidControl {
public:
    int lightPin = 33;
    int syringeOutPin = 25;
    int syringeInPin = 5;

    SquidControl() {
        pinMode(lightPin, OUTPUT);
        pinMode(syringeOutPin, OUTPUT);
        pinMode(syringeInPin, OUTPUT);

        digitalWrite(lightPin, LOW);
        digitalWrite(syringeOutPin, LOW);
        digitalWrite(syringeInPin, LOW);
    }

    void surface(unsigned long seconds) {
        digitalWrite(syringeOutPin, HIGH);
        delay(seconds * 1000);
        digitalWrite(syringeOutPin, LOW);
    }

    void surfaceThread(unsigned long seconds) {
        struct Params { SquidControl* self; unsigned long sec; };
        Params* p = new Params{ this, seconds };

        xTaskCreate([](void* ptr) {
            Params* p = (Params*)ptr;
            digitalWrite(p->self->syringeOutPin, HIGH);
            delay(p->sec * 1000);
            digitalWrite(p->self->syringeOutPin, LOW);
            delete p;
            vTaskDelete(NULL);
        }, "surfaceTask", 2048, p, 1, NULL);
    }

    void sink(unsigned long seconds) {
        digitalWrite(syringeInPin, HIGH);
        delay(seconds * 1000);
        digitalWrite(syringeInPin, LOW);
    }

    void sinkThread(unsigned long seconds) {
        struct Params { SquidControl* self; unsigned long sec; };
        Params* p = new Params{ this, seconds };

        xTaskCreate([](void* ptr) {
            Params* p = (Params*)ptr;
            digitalWrite(p->self->syringeInPin, HIGH);
            delay(p->sec * 1000);
            digitalWrite(p->self->syringeInPin, LOW);
            delete p;
            vTaskDelete(NULL);
        }, "sinkTask", 2048, p, 1, NULL);
    }

    void blinkLight(int times, float rate) {
        struct Params { SquidControl* self; int t; float r; };
        Params* p = new Params{ this, times, rate };

        xTaskCreate([](void* ptr) {
            Params* p = (Params*)ptr;
            for (int i = 0; i < p->t; i++) {
                digitalWrite(p->self->lightPin, HIGH);
                delay(p->r * 1000);
                digitalWrite(p->self->lightPin, LOW);
                delay(p->r * 1000);
            }
            delete p;
            vTaskDelete(NULL);
        }, "blinkTask", 2048, p, 1, NULL);
    }

    float getPressure() {
        if (!debugMode) {
            int16_t raw = ads.read(0);
            float v = ads.raw_to_v(raw);
            float p = mapFloat(v, 0.5, 4.5, 0, 206.8427) + 101.325;
            return p;
        } else {
            return 100.0 + (rand() % 3000) / 100.0;
        }
    }

    std::vector<std::array<String, 3>> record(String direction) {
        Serial.println("Going " + direction);
        std::vector<std::array<String, 3>> out;

        for (int i = 0; i < 8; i++) {
            float t = (millis() - startTime) / 1000.0;
            float p = getPressure();
            float depth = (p - 101.325) / 9.81;

            out.push_back({ String(t, 2), String(p, 2), String(depth, 2) });

