#include <Arduino.h>

// Piny podlaczone do joysticka, potencjometru i przycisku.
constexpr uint8_t JOY_X_PIN = 7;
constexpr uint8_t JOY_Y_PIN = 2;
constexpr uint8_t JOY_SW_PIN = 4;
constexpr uint8_t BUTTON_PIN = 5;

// Parametry przeliczania odczytu ADC na napiecie.
constexpr float ADC_REF_VOLTAGE = 3.3F;
constexpr float ADC_MAX_VALUE = 4095.0F;

// Zmienne czasu uzywane do cyklicznego wysylania probek.
unsigned long startTimeMs = 0;
unsigned long lastSampleMs = 0;
unsigned long sampleIntervalMs = 100;

float clampFloat(float value, float low, float high) {
    // Ogranicza wartosc do podanego zakresu.
    if (value < low) {
        return low;
    }
    if (value > high) {
        return high;
    }
    return value;
}

float readAdcVoltage(uint8_t pin) {
    // Czyta ADC i przelicza wynik na wolty.
    const int raw = analogRead(pin);
    return raw * ADC_REF_VOLTAGE / ADC_MAX_VALUE;
}

void printCsvHeader() {
    // Naglowek danych wysylanych do Pythona.
    Serial.println("time_ms,ai0_v,ai1_v,di0,di1");
}

void printSample() {
    // Jedna probka: czas, dwa wejscia analogowe i dwa wejscia cyfrowe.
    const unsigned long timeMs = millis() - startTimeMs;
    const float ai0 = readAdcVoltage(JOY_X_PIN);
    const float ai1 = readAdcVoltage(JOY_Y_PIN);

    const int di0 = digitalRead(JOY_SW_PIN) == LOW ? 1 : 0;
    const int di1 = digitalRead(BUTTON_PIN) == LOW ? 1 : 0;

    Serial.print(timeMs);
    Serial.print(",");
    Serial.print(ai0, 3);
    Serial.print(",");
    Serial.print(ai1, 3);
    Serial.print(",");
    Serial.print(di0);
    Serial.print(",");
    Serial.println(di1);
}

float getCsvValue(const String& command, int index, float fallback) {
    // Pobiera wartosc z komendy tekstowej rozdzielonej przecinkami.
    int start = 0;
    for (int i = 0; i < index; ++i) {
        start = command.indexOf(',', start);
        if (start < 0) {
            return fallback;
        }
        ++start;
    }

    int end = command.indexOf(',', start);
    if (end < 0) {
        end = command.length();
    }
    return command.substring(start, end).toFloat();
}

void handleCommand(String command) {
    // Obsluga komend przychodzacych z aplikacji Pythonowej.
    command.trim();
    command.toUpperCase();

    if (command == "HEADER") {
        printCsvHeader();
    } else if (command.startsWith("RATE,")) {
        // RATE ustawia czestotliwosc wysylania probek.
        const float frequencyHz = clampFloat(getCsvValue(command, 1, 10.0F), 1.0F, 1000.0F);
        sampleIntervalMs = max(1UL, static_cast<unsigned long>(1000.0F / frequencyHz));
        Serial.print("# RATE_HZ=");
        Serial.println(frequencyHz, 2);
    }
}

void setup() {
    // Start komunikacji szeregowej z komputerem.
    Serial.begin(115200);
    const unsigned long serialStartMs = millis();
    while (!Serial && millis() - serialStartMs < 5000) {
        delay(10);
    }

    // Wejscia cyfrowe dzialaja z wewnetrznym podciaganiem.
    pinMode(JOY_SW_PIN, INPUT_PULLUP);
    pinMode(BUTTON_PIN, INPUT_PULLUP);

    // Konfiguracja rozdzielczosci i zakresu ADC.
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);

    delay(500);
    startTimeMs = millis();
    lastSampleMs = 0;

    Serial.println("# ESP32-S3 DAQ joystick logger");
    Serial.println("# AI0=GPIO7, AI1=GPIO2, DI0=GPIO4, DI1=GPIO5");
    printCsvHeader();
}

void loop() {
    // Najpierw sprawdzamy, czy Python wyslal jakas komende.
    while (Serial.available() > 0) {
        const String command = Serial.readStringUntil('\n');
        handleCommand(command);
    }

    // Probki wysylamy cyklicznie zgodnie z sampleIntervalMs.
    const unsigned long nowMs = millis();
    if (nowMs - lastSampleMs >= sampleIntervalMs) {
        lastSampleMs = nowMs;
        printSample();
    }
}
