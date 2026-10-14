#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

const int irFront = 4;
const int irBack  = 27;
const int buzzer  = 2;

float distance = 1.30;

unsigned long t1 = 0, t2 = 0;
bool carDetected = false;

void setup() {
  pinMode(irFront, INPUT);
  pinMode(irBack, INPUT);
  pinMode(buzzer, OUTPUT);

  Serial.begin(115200);

  lcd.begin();        // ✅ correct for your library
  lcd.backlight();

  lcd.setCursor(0,0);
  lcd.print("Speed Monitor");
}

void loop() {

  if (!carDetected && digitalRead(irFront) == LOW) {
    delay(50);
    if (digitalRead(irFront) == LOW) {
      carDetected = true;
      t1 = millis();

      lcd.clear();
      lcd.setCursor(0,0);
      lcd.print("Detecting...");
    }
  }

  if (carDetected && digitalRead(irBack) == LOW) {
    delay(50);
    if (digitalRead(irBack) == LOW) {
      t2 = millis();

      float dt = (t2 - t1) / 1000.0;

      if (dt > 0) {
        float speed = (distance / dt) * 3.6;

        Serial.print("Speed: ");
        Serial.println(speed);

        lcd.clear();
        lcd.setCursor(0,0);
        lcd.print("Speed:");
        lcd.setCursor(0,1);
        lcd.print(speed);
        lcd.print(" km/h");

        if (speed > 10) {
          digitalWrite(buzzer, HIGH);
          delay(1000);
          digitalWrite(buzzer, LOW);
        }
      }

      carDetected = false;
      delay(500);
    }
  }
}