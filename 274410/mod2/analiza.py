import pandas as pd 
import matplotlib.pyplot as plt 
import matplotlib.dates as mdates
import numpy as np 
import matplotlib.cm as cm
import matplotlib.colors as mcolors


print("Wczytywanie danych z pliku CSV...")
df = pd.read_csv('mod2/energydata_complete.csv')

# Konwersja daty
df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d %H:%M:%S')

# Tworzę globalną ramkę danych uśrednioną do pełnych godzin
# To rozwiązuje problem "szumu" we wszystkich zadaniach naraz
df_h = df.set_index('date').resample('h').mean().reset_index()

# Dodaje pomocnicze kolumny do uśrednionych danych
df_h['day_name'] = df_h['date'].dt.day_name()
df_h['hour'] = df_h['date'].dt.hour

print("Dane zostały uśrednione do godzin. Rozpoczynam generowanie zadań...")



# zadanie 1 : Profil stylu życia (Pon vs Niedz)
print("\nGeneruję Zadanie 1: Profil stylu życia (Pon vs Niedz)...")

# Wybieram dane dla poniedziałków i niedziel z uśrednionej bazy
data_sub = df_h[df_h['day_name'].isin(['Monday', 'Sunday'])]
daily_profile = data_sub.groupby(['hour', 'day_name'])['Appliances'].mean().unstack()

plt.figure(figsize=(12, 6))
plt.plot(daily_profile.index, daily_profile['Monday'], label='Typowy Poniedziałek', color='#1f77b4', linewidth=2.5)
plt.plot(daily_profile.index, daily_profile['Sunday'], label='Typowa Niedziela', color='#ff7f0e', linewidth=2.5)

plt.xticks(range(0, 24))
plt.title('Profil energetyczny: Średnie zużycie prądu w skali godziny', fontsize=14)
plt.xlabel('Godzina doby')
plt.ylabel('Średnie zużycie (Wh)')
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('mod2/typowa_doba.png')
plt.show()


# zadanie 2 : Mapa intensywności zużycia prądu (heatmapa)
print("\nGeneruję Zadanie 2: Mapa intensywności zużycia prądu")

days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
pivot_table = df_h.pivot_table(index='day_name', columns='hour', values='Appliances', aggfunc='mean').reindex(days_order)

plt.figure(figsize=(12, 6))
plt.imshow(pivot_table, aspect='auto', cmap='YlGnBu')
plt.colorbar(label='Średnie zużycie na godzinę (Wh)')

plt.yticks(range(len(days_order)), ['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Niedz'])
plt.xticks(range(0, 24))
plt.title('Mapa intensywności zużycia prądu (Średnie godzinowe)', fontsize=14)
plt.xlabel('Godzina (0-23)')
plt.ylabel('Dzień tygodnia')
plt.tight_layout()
plt.savefig('mod2/heatmapa_tygodniowa.png')
plt.show()


# zadanie 3 : Wpływ warunków atmosferycznych na mikroklimat domu
print("\nGeneruję Zadanie 3: Wpływ warunków atmosferycznych na mikroklimat domu")

start_date = pd.to_datetime('2016-02-10')
end_date = pd.to_datetime('2016-02-17')

# Filtruje dane z już uśrednionej bazy godzinowej
df_subset = df_h[(df_h['date'] >= start_date) & (df_h['date'] <= end_date)]

plt.figure(figsize=(12, 6))
plt.fill_between(df_subset['date'], df_subset['RH_out'], color='#99ccff', alpha=0.6, label='Zewnątrz')
plt.fill_between(df_subset['date'], df_subset['RH_1'], color='#f5b041', alpha=0.9, label='Wnętrze (Kuchnia)')

# Pionowe linie oddzielające dni
for day in pd.date_range(start=start_date.date(), end=end_date.date(), freq='D'):
    plt.axvline(x=day, color='black', linestyle='--', linewidth=1.5, alpha=0.5)

plt.title('Porównanie wilgotności: Zewnątrz vs Wnętrze (Średnie godzinowe)', fontsize=14)
plt.ylabel('Wilgotność (%)')
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
plt.legend()
plt.tight_layout()
plt.savefig('mod2/wilgotnosc_obszarowy.png')
plt.show()


# zadanie 4 : Wykres kołowy - Porównanie średnich temperatur w domu (Maj)
print("\nGeneruję Zadanie 4: Wykres kołowy - Porównanie średnich temperatur w domu (Maj)")
df_may = df_h[df_h['date'].dt.month == 5]
temp_cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T7', 'T8']
labels = ['Salon', 'Kuchnia', 'Sypialnia', 'Łazienka', 'Biuro', 'Prasowalnia', 'Pokój Dzieci']

srednie_maj = df_may[temp_cols].mean()

plt.figure(figsize=(10, 8))
kolory = ['#2ecc71', '#27ae60', '#16a085', '#1abc9c', '#3498db', '#2980b9', '#9b59b6']

plt.pie(srednie_maj, labels=labels, 
        autopct=lambda p: '{:.1f}°C'.format(p * sum(srednie_maj) / 100),
        startangle=140, colors=kolory, pctdistance=0.82, explode=[0.02]*len(labels),
        wedgeprops={'edgecolor': 'black', 'linewidth': 0.5},
        textprops={'fontsize': 10, 'weight': 'bold'})

# Rysuje środek wykresu kołowego 
plt.gca().add_artist(plt.Circle((0,0), 0.70, fc='white'))
plt.title('Rozkład średnich temperatur w pokojach (Maj)', fontsize=14, pad=20)
plt.axis('equal')
plt.tight_layout()
plt.savefig('mod2/temp_pomieszczenia_maj.png')
plt.show()


# zadanie 5 : Analiza zużycia energii w różnych porach dnia (Tydzień zimowy)
print("\nGeneruję Zadanie 5: Analiza zużycia energii w różnych porach dnia (Tydzień zimowy)...")

start_w = '2016-01-18'; end_w = '2016-01-24'
df_week = df_h[(df_h['date'] >= start_w) & (df_h['date'] <= end_w)].copy()

def przypisz_pore(godzina):
    if 0 <= godzina < 6: return '1. Noc (0-6)'
    if 6 <= godzina < 12: return '2. Poranek (6-12)'
    if 12 <= godzina < 18: return '3. Dzień (12-18)'
    return '4. Wieczór (18-24)'

df_week['Pora_Dnia'] = df_week['hour'].map(przypisz_pore)
fazy_dnia = df_week.groupby('Pora_Dnia')['Appliances'].mean()

plt.figure(figsize=(10, 6))
kolory_f = ['#1a2a6c', '#fdbb2d', '#b21f1f', '#1f4068']
bars = plt.bar(fazy_dnia.index, fazy_dnia.values, color=kolory_f, edgecolor='black', alpha=0.8)

for bar in bars:
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
             f'{round(bar.get_height(), 1)} Wh', ha='center', fontweight='bold')

plt.title(f'Średnie zużycie prądu w fazach dnia ({start_w} do {end_w})')
plt.ylabel('Wh / Godzina')
plt.grid(axis='y', linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig('mod2/fazy_dnia_styczen.png')
plt.show()

