# Opis plikow projektu DAQ

## Cel projektu

Projekt realizuje prosty system testowy DAQ. Aplikacja Pythonowa pozwala uruchomic akwizycje danych, wyswietlac sygnaly na wykresie, sprawdzac limity, zapisywac pomiary do pliku CSV oraz generowac symulowany sygnal AO. Dane moga pochodzic z symulacji albo z makiety ESP32 podlaczonej przez port COM.

---

## `daq/main.py`

To glowny plik aplikacji. Odpowiada za uruchomienie okna GUI w Tkinterze, obsluge przyciskow, wybor trybu pracy, rysowanie wykresu oraz zapis pomiarow.

Najwazniejsze elementy:

- `MainApp` - glowna klasa aplikacji.
- `_setup_ui()` - tworzy caly interfejs: panel po lewej stronie, przyciski, pola konfiguracyjne i wykres.
- `change_backend()` - przelacza zrodlo danych pomiedzy `Symulacja` i `ESP32 joystick`.
- `handle_start_daq()` - uruchamia akwizycje danych.
- `handle_stop_daq()` - zatrzymuje akwizycje.
- `toggle_meas()` - rozpoczyna albo konczy okres pomiaru, czyli fragment danych, ktory bedzie oceniany i zapisany.
- `update_gui()` - cyklicznie pobiera nowe probki z akwizycji, aktualizuje etykiety i wykres.
- `save_data()` - zapisuje dane pomiarowe do pliku CSV.
- `start_gen()` i `stop_gen()` - uruchamiaja i zatrzymuja symulowana generacje AO.

W tym pliku znajduje sie logika laczaca wszystkie pozostale moduly. `main.py` sam nie czyta pinow ESP32 i sam nie liczy sygnalu AO od zera, tylko korzysta z klas z innych plikow.

---

## `daq/daq_acquisition.py`

Ten plik odpowiada za symulowana akwizycje danych. Jest uzywany wtedy, gdy w GUI wybrany jest tryb `Symulacja`.

Najwazniejsza klasa:

- `AnalogAcquisition`

Co robi:

- generuje sztuczny sygnal analogowy podobny do sinusoidy,
- generuje proste sygnaly cyfrowe,
- dziala w osobnym watku, zeby nie blokowac GUI,
- zapisuje probki do bufora,
- udostepnia funkcje `get_samples()`, ktora zwraca probki do aplikacji i czysci bufor.

Najwazniejsze funkcje:

- `configure()` - ustawia czestotliwosc i zakres napiecia.
- `start()` - uruchamia symulacje.
- `stop()` - zatrzymuje symulacje.
- `_acquisition_loop()` - petla dzialajaca w tle, ktora co pewien czas dodaje probki do bufora.
- `_build_sample()` - tworzy pojedyncza probke z polami takimi jak `time_s`, `ai_v`, `di`, `potentiometer`, `switch`.

Ten plik jest przydatny do testowania aplikacji bez podlaczonego ESP32.

---

## `daq/daq_acquisition_esp32.py`

Ten plik odpowiada za odbior danych z ESP32 przez port szeregowy, np. `COM7`.

Najwazniejsza klasa:

- `ESP32JoystickAcquisition`

Co robi:

- otwiera port COM,
- wysyla do ESP32 komende z czestotliwoscia probkowania, np. `RATE,10`,
- odbiera linie CSV wysylane przez ESP32,
- zamienia odebrane tekstowe dane na slownik Pythona,
- zapisuje probki w buforze,
- udostepnia probki przez `get_samples()`.

Najwazniejsze funkcje:

- `configure()` - ustawia czestotliwosc i zakres napiecia.
- `start()` - otwiera port COM i uruchamia watek odbioru danych.
- `stop()` - zamyka port COM i zatrzymuje watek.
- `send_command()` - wysyla komende tekstowa do ESP32.
- `_acquisition_loop()` - stale odbiera dane z ESP32.
- `_parse_line()` - parsuje jedna linie CSV, np. `time_ms,ai0_v,ai1_v,di0,di1`.

Najwazniejsze pola probki:

- `time_s` - czas probki w sekundach,
- `ai_v` - glowny kanal analogowy, czyli `AI0`,
- `ai1_v` - drugi kanal analogowy,
- `di0` - przycisk joysticka,
- `di1` - osobny button,
- `potentiometer` - wartosc `AI0` przeliczona na zakres 0..1,
- `switch` - stan buttona.

Ten plik jest lacznikiem pomiedzy aplikacja Pythonowa a fizyczna makieta ESP32.

---

## `daq/daq_generation.py`

Ten plik odpowiada za symulowana generacje AO, czyli sygnalu wyjsciowego.

Najwazniejsza klasa:

- `AnalogGeneration`

Co robi:

- generuje wartosc sinusoidy albo PWM,
- dziala w osobnym watku,
- przechowuje aktualna wartosc sygnalu,
- pozwala GUI odczytywac aktualna wartosc i rysowac ja na wykresie.

Najwazniejsze funkcje:

- `set_sine(amplitude, frequency)` - ustawia sinusoidę o podanej amplitudzie i czestotliwosci.
- `set_pwm(amplitude, duty_cycle, frequency)` - ustawia PWM o podanej amplitudzie, wypelnieniu i czestotliwosci.
- `start()` - uruchamia generacje.
- `stop()` - zatrzymuje generacje.
- `get_value()` - zwraca aktualna wartosc sygnalu.
- `get_elapsed_time()` - zwraca czas od startu generacji.
- `_generation_loop()` - w tle oblicza kolejne wartosci sygnalu.

W projekcie AO jest generowane programowo, czyli nie wychodzi fizycznie z ESP32. Jest to symulacja potrzebna do czesci zadania dotyczacej generacji AO.

---

## `daq/ao_generation.py`

To maly plik testowy pokazujacy, jak uzyc klasy `AnalogGeneration`.

Co robi:

- tworzy obiekt generatora AO,
- uruchamia sinusoidę na 2 sekundy,
- zatrzymuje ja,
- uruchamia PWM na 2 sekundy,
- zatrzymuje go.

Najwazniejszy fragment:

```python
ao = AnalogGeneration()
ao.set_sine(amplitude=10, frequency=2)
ao.start()
time.sleep(2)
ao.stop()
```

Ten plik nie jest glowna aplikacja. Bardziej sluzy jako prosty test lub demonstracja dzialania generatora.

---

## `esp32_daq_joystick/src/main.cpp`

To program wgrywany na ESP32. Odczytuje sygnaly z makiety i wysyla je do komputera przez Serial.

Co robi:

- odczytuje dwa wejscia analogowe:
  - `JOY_X_PIN = 7`,
  - `JOY_Y_PIN = 2`,
- odczytuje dwa wejscia cyfrowe:
  - `JOY_SW_PIN = 4`,
  - `BUTTON_PIN = 5`,
- przelicza odczyt ADC na napiecie w voltach,
- wysyla dane w formacie CSV,
- obsluguje komende `RATE`, ktora ustawia czestotliwosc wysylania probek.

Format wysylanych danych:

```text
time_ms,ai0_v,ai1_v,di0,di1
```

Przyklad:

```text
1200,1.532,2.101,0,1
```

Oznacza to:

- `1200` - czas od startu programu w ms,
- `1.532` - napiecie na pierwszym wejsciu analogowym,
- `2.101` - napiecie na drugim wejsciu analogowym,
- `0` - stan przycisku joysticka,
- `1` - stan buttona.

Najwazniejsze funkcje:

- `readAdcVoltage()` - odczytuje ADC i przelicza wynik na napiecie.
- `printCsvHeader()` - wysyla naglowek CSV.
- `printSample()` - wysyla jedna probke danych.
- `handleCommand()` - obsluguje komendy z Pythona, np. `RATE,10`.
- `setup()` - konfiguruje Serial, piny i ADC.
- `loop()` - stale odbiera komendy i cyklicznie wysyla probki.

---

## Pliki `data_*.csv`

To pliki z zapisanymi pomiarami. Powstaja automatycznie po zakonczeniu pomiaru w aplikacji.

Zawieraja m.in.:

- czas probki,
- wartosc analogowa,
- stan wejsc cyfrowych,
- wybrany sygnal oceniany limitami,
- informacje `limit_ok`, czyli czy probka byla w zakresie.

Te pliki sa wynikiem pracy aplikacji, a nie kodem zrodlowym.

---

## Podsumowanie przeplywu danych

1. ESP32 odczytuje joystick, potencjometr i button.
2. ESP32 wysyla dane przez port COM jako CSV.
3. `daq_acquisition_esp32.py` odbiera i parsuje dane.
4. `main.py` pobiera probki przez `get_samples()`.
5. Aplikacja pokazuje dane na wykresie i w etykietach.
6. Podczas pomiaru aplikacja sprawdza limity.
7. Po zakonczeniu pomiaru dane sa zapisywane do pliku CSV.

W trybie `Symulacja` zamiast ESP32 dane generuje `daq_acquisition.py`.
