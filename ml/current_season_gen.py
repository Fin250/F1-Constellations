import pandas as pd
import requests
import time
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from io import StringIO
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
import numpy as np
from dateutil.relativedelta import relativedelta

script_dir = os.path.dirname(os.path.abspath(__file__))

# Function to calculate points and wins prior to the race
def lookup(df, team, points):
    df['lookup1'] = df.season.astype(str) + df[team] + df['round'].astype(str)
    df['lookup2'] = df.season.astype(str) + df[team] + (df['round'] - 1).astype(str)
    new_df = df.merge(df[['lookup1', points]], how='left', left_on='lookup2', right_on='lookup1')
    new_df.drop(['lookup1_x', 'lookup2', 'lookup1_y'], axis=1, inplace=True)
    new_df.rename(columns={points + '_x': points + '_after_race', points + '_y': points}, inplace=True)
    new_df[points].fillna(0, inplace=True)
    return new_df

# Data structure for races
races = {
    'season': [], 'round': [], 'circuit_id': [],
    'lat': [], 'long': [], 'country': [],
    'date': [], 'url': []
}

year = 2025
url = f'https://api.jolpi.ca/ergast/f1/{year}.json'
success = False
retries = 3
delay = 1.5  # seconds

for attempt in range(retries):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        success = True
        break
    except requests.exceptions.HTTPError as e:
        if r.status_code == 429 and attempt < retries - 1:
            time.sleep(3)
            continue
        print(f"[ERROR] Failed to fetch data for {year}: {e}")
        break
    except Exception as e:
        print(f"[ERROR] Unexpected error for {year}: {e}")
        break

if success:
    for item in data['MRData']['RaceTable']['Races']:
        races['season'].append(int(item.get('season', None)))
        races['round'].append(int(item.get('round', None)))
        races['circuit_id'].append(item.get('Circuit', {}).get('circuitId'))

        loc = item.get('Circuit', {}).get('Location', {})
        races['lat'].append(float(loc.get('lat', None)) if loc.get('lat') else None)
        races['long'].append(float(loc.get('long', None)) if loc.get('long') else None)
        races['country'].append(loc.get('country', None))
        races['date'].append(item.get('date', None))
        races['url'].append(item.get('url', None))

    time.sleep(delay)

# Convert to DataFrame and save
races_df_2025 = pd.DataFrame(races)

# Load races for 2025 only
race = races_df_2025

rounds = [(2025, list(race[race.season == 2025]['round']))]

checkpoint_path = "f1_results_2025_checkpoint.csv"

# Load checkpoint if it exists
if os.path.exists(checkpoint_path):
    csv_path = os.path.join(script_dir, checkpoint_path)
    results_df = pd.read_csv(csv_path)
    completed_rounds = set(zip(results_df['season'], results_df['round']))
    print(f"[INFO] Loaded checkpoint: {results_df.shape[0]} rows, {len(completed_rounds)} rounds completed.")
else:
    results_df = pd.DataFrame(columns=[
        'season', 'round', 'circuit_id', 'driver',
        'date_of_birth', 'nationality', 'constructor',
        'grid', 'time', 'status', 'points',
        'podium', 'url'
    ])
    completed_rounds = set()
    print("[INFO] Starting from scratch.")

results = {
    'season': [], 'round': [], 'circuit_id': [], 'driver': [],
    'date_of_birth': [], 'nationality': [], 'constructor': [],
    'grid': [], 'time': [], 'status': [], 'points': [],
    'podium': [], 'url': []
}

backoff_limit = 30
backoff_attempts = 0
delay = 1.5

# Process only 2025
for season, season_rounds in rounds:
    print(f"[INFO] Starting season {season}")
    season_failed = False

    for rnd in season_rounds:
        if (season, rnd) in completed_rounds:
            continue

        url = f'https://api.jolpi.ca/ergast/f1/{season}/{rnd}/results.json'
        success = False
        retries = 3

        for attempt in range(retries):
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                data = r.json()
                success = True
                break
            except requests.exceptions.HTTPError as e:
                if r.status_code == 429:
                    backoff_attempts += 1
                    if backoff_attempts >= backoff_limit:
                        print(f"[ABORT] Backoff limit exceeded at {season} round {rnd}. Exiting without saving round.")
                        season_failed = True
                        break
                    time.sleep(10)
                    continue
                print(f"[ERROR] Failed for {season} round {rnd}: {e}")
                season_failed = True
                break
            except Exception as e:
                print(f"[ERROR] Unexpected error for {season} round {rnd}: {e}")
                season_failed = True
                break

        if season_failed or not success:
            print(f"[INFO] Skipping round {rnd} due to failure.")
            continue

        try:
            race_data = data['MRData']['RaceTable']['Races'][0]
            for item in race_data['Results']:
                results['season'].append(int(race_data.get('season', None)))
                results['round'].append(int(race_data.get('round', None)))
                results['circuit_id'].append(race_data.get('Circuit', {}).get('circuitId'))
                results['driver'].append(item.get('Driver', {}).get('driverId'))
                results['date_of_birth'].append(item.get('Driver', {}).get('dateOfBirth'))
                results['nationality'].append(item.get('Driver', {}).get('nationality'))
                results['constructor'].append(item.get('Constructor', {}).get('constructorId'))

                grid_val = item.get('grid')
                results['grid'].append(int(grid_val) if grid_val and grid_val.isdigit() else None)

                try:
                    results['time'].append(int(item.get('Time', {}).get('millis')))
                except:
                    results['time'].append(None)

                results['status'].append(item.get('status'))

                try:
                    results['points'].append(float(item.get('points')))
                except:
                    results['points'].append(None)

                try:
                    results['podium'].append(int(item.get('position')))
                except:
                    results['podium'].append(None)

                results['url'].append(race_data.get('url'))

        except Exception as e:
            print(f"[ERROR] Failed to parse data for round {rnd}: {e}")
            continue

        # Save checkpoint after each round
        round_df = pd.DataFrame(results)
        results_df = pd.concat([results_df, round_df], ignore_index=True)
        checkpoint_output_path = os.path.join(script_dir, checkpoint_path)
        results_df.to_csv(checkpoint_output_path, index=False)

        # Reset results for next round
        results = {k: [] for k in results}

        time.sleep(delay)

qualifying_results = pd.DataFrame()
base_url = "https://www.formula1.com"

year = 2025
url = f'{base_url}/en/results.html/{year}/races.html'

try:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
except Exception as e:
    print(f"[ERROR] Failed to fetch year page for {year}: {e}")
    exit()

soup = BeautifulSoup(r.text, 'html.parser')

# Get race links from table (avoids duplicates from footer/sidebar)
table = soup.find('table')
if table is None:
    print(f"[ERROR] No race table found for {year}")
    exit()

year_links = []
for a in table.find_all('a', href=True):
    href = a['href']
    if f"/en/results/{year}/races/" in href and 'race-result' in href:
        full_href = urljoin(base_url, href.replace('/../../', '/'))
        if full_href not in year_links:
            year_links.append(full_href)

if not year_links:
    print(f"[WARNING] No race links found for {year}")
    exit()

year_df = pd.DataFrame()
for n, link in enumerate(year_links):
    starting_grid_url = link.replace('race-result', 'starting-grid')
    try:
        r = requests.get(starting_grid_url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find('table')

        if table is None:
            print(f"    [WARNING] No table found at {starting_grid_url}")
            continue

        # Remove <tfoot> if it exists to avoid including notes
        tfoot = table.find('tfoot')
        if tfoot:
            tfoot.decompose()

        df = pd.read_html(StringIO(str(table)))[0]

        # Extract driver names properly
        driver_cells = table.find_all('tr')[1:]
        driver_names = []
        for i, row in enumerate(driver_cells):
            cols = row.find_all('td')
            if len(cols) < 3:
                print(f"      [Row {i}] Skipped: not enough columns")
                driver_names.append(None)
                continue
            driver_td = cols[2]
            full_name_span = driver_td.find('span', class_='max-md:hidden')
            raw_name = full_name_span.get_text(strip=True) if full_name_span else driver_td.get_text(strip=True)
            driver_name = re.sub(r'[A-Z]{1,3}$', '', raw_name)  # strip team codes
            driver_names.append(driver_name)

        try:
            df.iloc[:, 2] = driver_names
            df.rename(columns={df.columns[2]: 'Driver'}, inplace=True)
        except Exception as e:
            print(f"      [ERROR] Could not replace Driver column: {e}")
            continue

        df['season'] = year
        df['round'] = n + 1

        unnamed_cols = [col for col in df if 'Unnamed' in col]
        if unnamed_cols:
            df.drop(columns=unnamed_cols, inplace=True)

        year_df = pd.concat([year_df, df], ignore_index=True)

        time.sleep(1.5)  # polite delay

    except Exception as e:
        print(f"    [ERROR] Failed to process {starting_grid_url}: {e}")
        continue

if year_df.empty:
    print(f"  [WARNING] No data collected for {year}")

qualifying_results = pd.concat([qualifying_results, year_df], ignore_index=True)

# Final cleaning
qualifying_results.rename(columns={'Pos': 'grid_position',
                                   'Driver': 'driver_name',
                                   'Car': 'car',
                                   'Time': 'qualifying_time'}, inplace=True)

if 'NO.' in qualifying_results.columns:
    qualifying_results.drop('NO.', axis=1, inplace=True)

checkpoint_path = "driver_standings_checkpoint.csv"

# Load checkpoint if exists
if os.path.exists(checkpoint_path):
    csv_path = os.path.join(script_dir, checkpoint_path)
    standings_df = pd.read_csv(checkpoint_path)
    completed_seasons = set(standings_df['season'].unique())
else:
    standings_df = pd.DataFrame(columns=[
        'season', 'round', 'driver',
        'driver_points', 'driver_wins', 'driver_standings_pos'
    ])
    completed_seasons = set()

driver_standings = {
    'season': [], 'round': [], 'driver': [],
    'driver_points': [], 'driver_wins': [], 'driver_standings_pos': []
}

backoff_limit = 30
backoff_attempts = 0
delay = 1.5
backoff_exceeded = False

# Define the 2025 season rounds
rounds_2025 = [(2025, list(range(1, 24)))]  # F1 2025 has 23 rounds (adjust if official calendar changes)
rounds_to_process = [(s, r) for (s, r) in rounds_2025 if s not in completed_seasons]

for season, season_rounds in rounds_to_process:
    for rnd in season_rounds:
        url = f'https://api.jolpi.ca/ergast/f1/{season}/{rnd}/driverStandings.json'
        success = False
        retries = 3

        for attempt in range(retries):
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                data = r.json()
                success = True
                break
            except requests.exceptions.HTTPError as e:
                if r.status_code == 429 and attempt < retries - 1 and backoff_attempts < backoff_limit:
                    backoff_attempts += 1
                    time.sleep(10)
                    continue
                elif r.status_code == 429 and backoff_attempts >= backoff_limit:
                    print(f"[ABORT] Backoff limit exceeded at {season} round {rnd}. Exiting without saving season.")
                    backoff_exceeded = True
                    break
                print(f"[ERROR] Failed for {season} round {rnd}: {e}")
                break
            except Exception as e:
                print(f"[ERROR] Unexpected error for {season} round {rnd}: {e}")
                break

        if backoff_exceeded:
            break
        if not success:
            continue

        try:
            standings_list = data['MRData']['StandingsTable']['StandingsLists'][0]
            for item in standings_list['DriverStandings']:
                driver_standings['season'].append(int(standings_list.get('season')))
                driver_standings['round'].append(int(standings_list.get('round')))
                driver_standings['driver'].append(item.get('Driver', {}).get('driverId'))

                try:
                    driver_standings['driver_points'].append(int(item.get('points')))
                except:
                    driver_standings['driver_points'].append(None)

                try:
                    driver_standings['driver_wins'].append(int(item.get('wins')))
                except:
                    driver_standings['driver_wins'].append(None)

                try:
                    driver_standings['driver_standings_pos'].append(int(item.get('position')))
                except:
                    driver_standings['driver_standings_pos'].append(None)

        except Exception as e:
            print(f"[ERROR] Failed to parse data for {season} round {rnd}: {e}")
            continue

        time.sleep(delay)

    if backoff_exceeded:
        print("[INFO] Exiting before saving incomplete season.")
        break

    # Save season results
    season_df = pd.DataFrame(driver_standings)
    standings_df = pd.concat([standings_df, season_df], ignore_index=True)
    checkpoint_output_path = os.path.join(script_dir, checkpoint_path)
    standings_df.to_csv(checkpoint_output_path, index=False)
    driver_standings = {k: [] for k in driver_standings}  # Reset season buffer

# Load the saved checkpoint CSV into a DataFrame
csv_path = os.path.join(script_dir, "driver_standings_checkpoint.csv")
driver_standings_df = pd.read_csv(csv_path)

# Apply the lookup function
driver_standings_df = lookup(driver_standings_df, 'driver', 'driver_points')
driver_standings_df = lookup(driver_standings_df, 'driver', 'driver_wins')
driver_standings_df = lookup(driver_standings_df, 'driver', 'driver_standings_pos')

# Load 2025 races
race_2025 = races_df_2025

# Define rounds as a list of tuples (season, list_of_rounds)
rounds = [(2025, list(race_2025[race_2025.season == 2025]['round']))]

checkpoint_path = "constructor_standings_checkpoint.csv"

# Load checkpoint if exists
if os.path.exists(checkpoint_path):
    csv_path = os.path.join(script_dir, checkpoint_path)
    standings_df = pd.read_csv(csv_path)
    completed_seasons = set(standings_df['season'].unique())
else:
    standings_df = pd.DataFrame(columns=[
        'season', 'round', 'constructor',
        'constructor_points', 'constructor_wins', 'constructor_standings_pos'
    ])
    completed_seasons = set()

constructor_standings = {
    'season': [], 'round': [], 'constructor': [],
    'constructor_points': [], 'constructor_wins': [], 'constructor_standings_pos': []
}

backoff_limit = 30
backoff_attempts = 0
delay = 1.5
backoff_exceeded = False

# Skip already completed seasons
rounds_to_process = [(s, r) for (s, r) in rounds if s not in completed_seasons]

for season, season_rounds in rounds_to_process:
    for rnd in season_rounds:
        url = f'https://api.jolpi.ca/ergast/f1/{season}/{rnd}/constructorStandings.json'
        success = False
        retries = 3

        for attempt in range(retries):
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                data = r.json()
                success = True
                backoff_attempts = 0  # Reset backoff on success
                break
            except requests.exceptions.HTTPError as e:
                if r.status_code == 429:
                    if backoff_attempts < backoff_limit:
                        backoff_attempts += 1
                        time.sleep(10)
                        continue
                    else:
                        print(f"[ABORT] Backoff limit exceeded at {season} round {rnd}. Exiting without saving season.")
                        backoff_exceeded = True
                        break
                print(f"[ERROR] Failed for {season} round {rnd}: {e}")
                break
            except Exception as e:
                print(f"[ERROR] Unexpected error for {season} round {rnd}: {e}")
                break

        if backoff_exceeded:
            break
        if not success:
            continue

        try:
            standings_list = data['MRData']['StandingsTable']['StandingsLists'][0]
            for item in standings_list['ConstructorStandings']:
                constructor_standings['season'].append(int(standings_list.get('season')))
                constructor_standings['round'].append(int(standings_list.get('round')))
                constructor_standings['constructor'].append(item.get('Constructor', {}).get('constructorId'))

                try:
                    constructor_standings['constructor_points'].append(int(item.get('points')))
                except:
                    constructor_standings['constructor_points'].append(None)

                try:
                    constructor_standings['constructor_wins'].append(int(item.get('wins')))
                except:
                    constructor_standings['constructor_wins'].append(None)

                try:
                    constructor_standings['constructor_standings_pos'].append(int(item.get('position')))
                except:
                    constructor_standings['constructor_standings_pos'].append(None)

        except Exception as e:
            print(f"[ERROR] Failed to parse data for {season} round {rnd}: {e}")
            continue

        time.sleep(delay)

    if backoff_exceeded:
        break

    # Save season results
    season_df = pd.DataFrame(constructor_standings)
    standings_df = pd.concat([standings_df, season_df], ignore_index=True)
    checkpoint_output_path = os.path.join(script_dir, checkpoint_path)
    standings_df.to_csv(checkpoint_output_path, index=False)
    constructor_standings = {k: [] for k in constructor_standings}  # Reset season buffer

csv_path = os.path.join(script_dir, "constructor_standings_checkpoint.csv")
constructor_standings_df = pd.read_csv(csv_path)

constructor_standings_df = lookup(constructor_standings_df, 'constructor', 'constructor_points')

constructor_standings_df = lookup(constructor_standings_df, 'constructor', 'constructor_wins')

constructor_standings_df = lookup(constructor_standings_df, 'constructor', 'constructor_standings_pos')

# Load races and filter for 2025
races = races_df_2025
races_2025 = races[races['season'] == 2025]

# Prepare weather DataFrame
weather = races_2025.iloc[:, [0, 1, 2]]
info = []

# User-Agent to avoid 403 Forbidden
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Process each race
for idx, link in enumerate(races_2025.url):
    found = False

    try:
        # Fetch page with headers
        response = requests.get(link, headers=headers)
        response.raise_for_status()

        # Parse HTML tables
        tables = pd.read_html(response.text)

        # Search for Weather row
        for i, df in enumerate(tables):
            try:
                if 'Weather' in list(df.iloc[:, 0]):
                    n = list(df.iloc[:, 0]).index('Weather')
                    weather_info = df.iloc[n, 1]
                    info.append(weather_info)
                    found = True
                    break
            except Exception as e:
                print(f"[WARNING] Table {i} structure issue: {e}")
                continue

        # Selenium fallback if Weather not found
        if not found:
            print(f"[FALLBACK] Using Selenium for page: {link}")
            driver = webdriver.Chrome()
            driver.get(link)
            time.sleep(2)

            try:
                clima = driver.find_element(By.XPATH, '//*[@id="mw-content-text"]/div/table[1]/tbody/tr[9]/td').text
                info.append(clima)
                found = True
            except:
                info.append('not found')

            driver.quit()

    except Exception as e:
        print(f"[ERROR] Failed to read HTML from {link}: {e}")
        info.append('not found')

# Assign weather info safely
weather.loc[:, 'weather'] = info

# Weather categories
weather_dict = {
    'weather_warm': ['soleggiato', 'clear', 'warm', 'hot', 'sunny', 'fine', 'mild', 'sereno'],
    'weather_cold': ['cold', 'fresh', 'chilly', 'cool'],
    'weather_dry': ['dry', 'asciutto'],
    'weather_wet': ['showers', 'wet', 'rain', 'pioggia', 'damp', 'thunderstorms', 'rainy'],
    'weather_cloudy': ['overcast', 'nuvoloso', 'clouds', 'cloudy', 'grey', 'coperto']
}

# Map weather to categories
weather_df = pd.DataFrame(columns=weather_dict.keys())
for col in weather_df:
    weather_df[col] = weather['weather'].map(
        lambda x: 1 if any(i in str(x).lower().split() for i in weather_dict[col]) else 0
    )

# Combine results and save
weather_info = pd.concat([weather, weather_df], axis=1)

races = races_df_2025
results = results_df
qualifying = qualifying_results
driver_standings = driver_standings_df
constructor_standings = constructor_standings_df
weather = weather_info

qualifying.rename(columns = {'grid_position': 'grid'}, inplace = True)
driver_standings.drop(['driver_points_after_race', 'driver_wins_after_race', 'driver_standings_pos_after_race'] ,axis = 1, inplace = True)
constructor_standings.drop(['constructor_points_after_race', 'constructor_wins_after_race','constructor_standings_pos_after_race' ],axis = 1, inplace = True)

# --- Normaliser config ---
CANONICAL = [
    'red_bull', 'rb', 'mclaren', 'ferrari', 'mercedes',
    'aston_martin', 'alpine', 'haas', 'williams', 'sauber'
]

# Ordered rules — more specific first. Use word boundaries for short tokens.
CONSTRUCTOR_RULES = [
    (r'red bull racing', 'red_bull'),
    (r'red bull', 'red_bull'),
    (r'rb honda', 'rb'),
    (r'\brb\b', 'rb'),             # exact word 'rb'
    (r'mclaren', 'mclaren'),
    (r'aston martin', 'aston_martin'),
    (r'alpine', 'alpine'),
    (r'haas', 'haas'),
    (r'williams', 'williams'),
    (r'sauber', 'sauber'),
    (r'ferrari', 'ferrari'),
    (r'mercedes', 'mercedes'),
]

def normalize_constructor_name(raw):
    if pd.isna(raw):
        return np.nan
    s = str(raw).lower()
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)      # remove punctuation
    s = re.sub(r'\s+', ' ', s).strip()
    # try rules
    for pattern, canon in CONSTRUCTOR_RULES:
        if re.search(pattern, s):
            return canon
    # fallback: try canonical tokens
    for canon in CANONICAL:
        token = canon.replace('_', ' ')
        if token in s or canon in s:
            return canon
    # final fallback: collapse spaces to underscore
    return s.replace(' ', '_')

# --- Utility: show unique raw values -> normalized mapping for debugging ---
def debug_normalisation(series, name):
    uniques = series.dropna().astype(str).unique()
    mapped = {u: normalize_constructor_name(u) for u in uniques}
    # show values not mapped to canonical for your review
    unmapped = {u:v for u,v in mapped.items() if v not in CANONICAL}
    return mapped

# --- Apply normaliser to every source column that may contain constructor/team names ---
# results, constructor_standings have 'constructor' column (short keys)
if 'constructor' in results.columns:
    results['constructor'] = results['constructor'].astype(str).apply(normalize_constructor_name)
if 'constructor' in constructor_standings.columns:
    constructor_standings['constructor'] = constructor_standings['constructor'].astype(str).apply(normalize_constructor_name)

# qualifying may have a TEAM column with long sponsor names; normalize that into a constructor column
# handle different possible column names (TEAM, Team, team)
qual_team_col = next((c for c in qualifying.columns if c.lower() == 'team' or c == 'TEAM'), None)
if qual_team_col:
    qualifying['constructor'] = qualifying[qual_team_col].astype(str).apply(normalize_constructor_name)
else:
    # if qualifying contains a column with long names under another header, adapt here
    if 'TEAM' in qualifying.columns:
        qualifying['constructor'] = qualifying['TEAM'].astype(str).apply(normalize_constructor_name)

# If driver_standings or others contain constructor names, normalise them too (defensive)
if 'constructor' in driver_standings.columns:
    driver_standings['constructor'] = driver_standings['constructor'].astype(str).apply(normalize_constructor_name)

# Debug print samples (helps find unmatched names)
_ = debug_normalisation(results.get('constructor', pd.Series(dtype=str)), 'results.constructor')
_ = debug_normalisation(constructor_standings.get('constructor', pd.Series(dtype=str)), 'constructor_standings.constructor')
_ = debug_normalisation(qualifying.get('constructor', pd.Series(dtype=str)), 'qualifying.constructor')

# Mapping for driver names to unify naming conventions
name_map = {
    'max_verstappen': 'Verstappen',
    'kevin_magnussen': 'Magnussen'
}

# Apply mapping to results and driver_standings before merges
results['driver'] = results['driver'].str.lower().map(name_map).fillna(results['driver'].str.title())
driver_standings['driver'] = driver_standings['driver'].str.lower().map(name_map).fillna(driver_standings['driver'].str.title())

# Qualifying uses driver_name, normalize case to title
qualifying['driver'] = qualifying['driver_name'].str.title()

# Rename qualifying columns to prepare for merge
qualifying.rename(columns={
    'Pos': 'grid_position',
    'Driver': 'driver_name',
    'Car': 'car',
    'Time': 'qualifying_time'
}, inplace=True)

# Add driver column normalized in qualifying
qualifying['driver'] = qualifying['driver_name'].str.title()

# Merge steps using the consistent 'driver' column everywhere

df1 = pd.merge(races, weather, how='inner', on=['season', 'round', 'circuit_id']) \
        .drop(['lat', 'long', 'country', 'weather'], axis=1)

df2 = pd.merge(df1, results, how='inner', on=['season', 'round', 'circuit_id', 'url']) \
        .drop(['url', 'points', 'status', 'time'], axis=1)

df3 = pd.merge(df2, driver_standings, how='left', on=['season', 'round', 'driver'])

df4 = pd.merge(df3, constructor_standings, how='left', on=['season', 'round', 'constructor'])

final_df = pd.merge(df4, qualifying, how='left', on=['season', 'round', 'driver'])


missing_qualifying = final_df['TIME'].isna().sum()

# sanity check: require normalize_constructor_name to exist
try:
    normalize_constructor_name  # noqa: F401
except NameError:
    raise RuntimeError("normalize_constructor_name is not defined. Define it earlier (the name normalization rules).")

# Candidate columns to inspect (order matters: earlier -> preferred)
candidate_cols = [
    'constructor', 'constructor_x', 'constructor_y',
    'TEAM', 'team', 'team_name', 'constructor_name'
]

# Keep only candidates that actually exist in final_df
existing_candidates = [c for c in candidate_cols if c in final_df.columns]
if not existing_candidates:
    print("[WARN] No constructor-like columns found in final_df. Check merge steps and source column names.")
else:
    # Ensure candidate cols are objects (avoid mixed types)
    for c in existing_candidates:
        final_df[c] = final_df[c].astype(object)

    # Helper: return first non-empty, non-null candidate value for each row
    def first_non_empty(row_values):
        for v in row_values:
            if pd.notna(v):
                s = str(v).strip()
                if s != '' and s.lower() != 'nan':
                    return s
        return np.nan

    final_df['constructor'] = final_df[existing_candidates].apply(first_non_empty, axis=1)

    # If constructor is still missing for some rows and qualifying.df has TEAM column, try joining by (season, round, driver)
    # (optional) Uncomment if you want to prefer qualifying.TEAM where merge missed it:
    # if 'TEAM' in qualifying.columns:
    #     q_map = qualifying.set_index(['season','round','driver'])['TEAM'].to_dict()
    #     missing_mask = final_df['constructor'].isna()
    #     for idx in final_df[missing_mask].index:
    #         key = (final_df.at[idx, 'season'], final_df.at[idx, 'round'], final_df.at[idx, 'driver'])
    #         if key in q_map and pd.notna(q_map[key]):
    #             final_df.at[idx, 'constructor'] = q_map[key]

    # Normalize constructor names (uses your normalize_constructor_name function)
    final_df['constructor'] = final_df['constructor'].apply(
        lambda x: normalize_constructor_name(x) if pd.notna(x) else np.nan
    )

# Dummify
df_dum = pd.get_dummies(final_df, columns=['circuit_id', 'nationality', 'constructor'])

# --- Calculate driver age, but keep 'date' for calendar features ---
if 'date' in final_df.columns and 'date_of_birth' in final_df.columns:
    final_df['date'] = pd.to_datetime(final_df['date'])
    final_df['date_of_birth'] = pd.to_datetime(final_df['date_of_birth'])
    final_df['driver_age'] = final_df.apply(
        lambda x: relativedelta(x['date'], x['date_of_birth']).years, axis=1
    )
    # Drop only 'date_of_birth', keep 'date' in final_df
    final_df.drop(columns=['date_of_birth'], inplace=True, errors='ignore')
else:
    final_df['driver_age'] = np.nan

# Fill/drop nulls
for col in ['driver_points', 'driver_wins', 'driver_standings_pos',
            'constructor_points', 'constructor_wins', 'constructor_standings_pos']:
    final_df[col].fillna(0, inplace=True)
    final_df[col] = final_df[col].astype(int)

# Fix grid positions where grid == 0
grid_corrections = []

# Group by season + round to handle each race separately
for (season, rnd), group in final_df.groupby(['season', 'round']):
    max_grid = group['grid'].max()
    # Drivers with grid 0
    zero_grid_mask = group['grid'] == 0
    zero_grid_drivers = group[zero_grid_mask]
    if not zero_grid_drivers.empty:
        new_grid_pos = max_grid + 1
        final_df.loc[zero_grid_drivers.index, 'grid'] = new_grid_pos
        for idx, row in zero_grid_drivers.iterrows():
            grid_corrections.append((row['driver'], season, rnd, new_grid_pos))

for col in ['weather_warm', 'weather_cold', 'weather_dry', 'weather_wet', 'weather_cloudy']:
    if col in final_df.columns:
        final_df[col] = final_df[col].map(lambda x: bool(x))

# ---------------------------
# 8) Qualifying time conversion & imputation
# robustly handle either TIME or qualifying_time columns present
# ---------------------------
time_col_candidate = None
for c in ['TIME', 'qualifying_time', 'Time']:
    if c in final_df.columns:
        time_col_candidate = c
        break

def convert_qualifying_time(x):
    if pd.isna(x) or x == '':
        return np.nan
    if isinstance(x, str):
        if x == '00.000':
            return 0.0
        if ':' in x:
            try:
                minutes, seconds = map(float, x.split(':'))
                return seconds + 60 * minutes
            except Exception:
                return np.nan
        try:
            return float(x)
        except Exception:
            return np.nan
    try:
        return float(x)
    except Exception:
        return np.nan

if time_col_candidate is not None:
    final_df['qualifying_time'] = final_df[time_col_candidate].apply(convert_qualifying_time)
else:
    final_df['qualifying_time'] = np.nan

def impute_qualifying_times(df):
    for (season, round_), group in df.groupby(['season', 'round']):
        idx = group.index
        top_10_mask = group['grid'].between(1, 10, inclusive='both') if 'grid' in group else pd.Series(False, index=group.index)
        mid_11_15_mask = group['grid'].between(11, 15, inclusive='both') if 'grid' in group else pd.Series(False, index=group.index)
        low_16_plus_mask = group['grid'] >= 16 if 'grid' in group else pd.Series(False, index=group.index)

        slowest_top_10 = group.loc[top_10_mask, 'qualifying_time'].max()
        slowest_mid_11_15 = group.loc[mid_11_15_mask, 'qualifying_time'].max()
        slowest_low_16_plus = group.loc[low_16_plus_mask, 'qualifying_time'].max()

        fallback = group['qualifying_time'].max()
        if pd.isna(fallback):
            fallback = 999.0
        else:
            fallback = fallback + 5.0

        if top_10_mask.any():
            mask = top_10_mask & group['qualifying_time'].isna()
            if mask.any():
                df.loc[idx[mask], 'qualifying_time'] = slowest_top_10 if not pd.isna(slowest_top_10) else fallback
        if mid_11_15_mask.any():
            mask = mid_11_15_mask & group['qualifying_time'].isna()
            if mask.any():
                df.loc[idx[mask], 'qualifying_time'] = slowest_mid_11_15 if not pd.isna(slowest_mid_11_15) else fallback
        if low_16_plus_mask.any():
            mask = low_16_plus_mask & group['qualifying_time'].isna()
            if mask.any():
                df.loc[idx[mask], 'qualifying_time'] = slowest_low_16_plus if not pd.isna(slowest_low_16_plus) else fallback
    return df

final_df = impute_qualifying_times(final_df)

# compute qualifying_time cumulative per race
if 'grid' in final_df.columns:
    final_df.sort_values(['season', 'round', 'grid'], inplace=True)
    final_df['qualifying_time_diff'] = final_df.groupby(['season', 'round'])['qualifying_time'].diff()
    final_df['qualifying_time_diff'] = final_df['qualifying_time_diff'].fillna(0)
    final_df['qualifying_time'] = final_df.groupby(['season', 'round'])['qualifying_time_diff'].cumsum()
    final_df.drop(columns=['qualifying_time_diff'], inplace=True, errors='ignore')

# ---------------------------
# 10) Fill NaNs for integer count fields
# ---------------------------
for col in ['driver_points', 'driver_wins', 'driver_standings_pos',
            'constructor_points', 'constructor_wins', 'constructor_standings_pos']:
    if col in final_df.columns:
        final_df[col].fillna(0, inplace=True)
        # safe-cast where possible
        try:
            final_df[col] = final_df[col].astype(int)
        except Exception:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0).astype(int)

# ---------------------------
# 11) Drop ephemeral/unneeded columns (defensive)
# ---------------------------
for drop_c in ['TEAM', 'TIME', 'Pos', 'POS.', 'driver_name', 'car']:
    if drop_c in final_df.columns:
        final_df.drop(columns=[drop_c], inplace=True, errors='ignore')

# --- Resolve constructor merge columns ---
if 'constructor_x' in final_df.columns and 'constructor_y' in final_df.columns:
    # Prefer constructor_x unless it's NaN, else use constructor_y
    final_df['constructor'] = final_df['constructor_x'].combine_first(final_df['constructor_y'])
    final_df.drop(columns=['constructor_x', 'constructor_y'], inplace=True, errors='ignore')
elif 'constructor_x' in final_df.columns:
    final_df.rename(columns={'constructor_x': 'constructor'}, inplace=True)
elif 'constructor_y' in final_df.columns:
    final_df.rename(columns={'constructor_y': 'constructor'}, inplace=True)

# Normalize constructor names
final_df['constructor'] = final_df['constructor'].astype(object).apply(
    lambda x: normalize_constructor_name(x) if pd.notna(x) else np.nan
)

# ---------------------------
# 12) Dummify final_df -> df_dum and save
# ---------------------------
df_dum = pd.get_dummies(final_df, columns=['circuit_id', 'nationality', 'constructor'], dtype=bool)

df = df_dum
races_csv = races_df_2025

# Determine missing rounds (2025 only)
existing_rounds = df['round'].unique()
all_rounds = races_csv['round'].unique()
missing_rounds = [r for r in all_rounds if r not in existing_rounds]

# Identify all circuit one-hot columns in the current df
circuit_cols = [col for col in df.columns if col.startswith('circuit_id_')]

# Add any missing circuits from races.csv to the main df upfront
for circuit in races_csv['circuit_id'].unique():
    circuit_col = f'circuit_id_{circuit}'
    if circuit_col not in df.columns:
        df[circuit_col] = False
        circuit_cols.append(circuit_col)

# --- NEW: only take drivers from the most recent round in df ---
last_round = df['round'].max()
current_drivers = df[df['round'] == last_round]['driver'].unique()

predicted_rows = []

for rnd in missing_rounds:
    race_info = races_csv[races_csv['round'] == rnd].iloc[0]
    race_circuit = race_info['circuit_id']
    circuit_col_name = f'circuit_id_{race_circuit}'

    for driver_name in current_drivers:
        driver_rows = df[df['driver'] == driver_name]
        driver_row = driver_rows.sort_values('round').iloc[-1].copy()

        driver_row['round'] = rnd
        driver_row['date'] = race_info['date']
        driver_row['podium'] = 10

        # Weather: dry
        driver_row['weather_dry'] = 1
        driver_row['weather_warm'] = 0
        driver_row['weather_cold'] = 0
        driver_row['weather_wet'] = 0
        driver_row['weather_cloudy'] = 0

        # Grid & qualifying_time: mean for this driver
        driver_row['grid'] = driver_rows['grid'].mean()
        driver_row['qualifying_time'] = driver_rows['qualifying_time'].mean()

        # Reset all circuit one-hot columns to False
        for col in circuit_cols:
            driver_row[col] = False

        # Set current race circuit to True
        driver_row[circuit_col_name] = True

        predicted_rows.append(driver_row)

predicted_df = pd.DataFrame(predicted_rows)

# Ensure all circuit columns exist in predicted_df
for col in circuit_cols:
    if col not in predicted_df.columns:
        predicted_df[col] = False

# Reorder columns to match original df (will be adjusted properly below)
full_cols = list(df.columns)
predicted_df = predicted_df[full_cols]

# Combine old + predicted
full_season_df = pd.concat([df, predicted_df], ignore_index=True)

# Identify core columns
core_cols = ['season','round','date','weather_warm','weather_cold','weather_dry','weather_wet',
             'weather_cloudy','driver','grid','podium','driver_points','driver_wins','driver_standings_pos',
             'constructor_points','constructor_wins','constructor_standings_pos','driver_age','qualifying_time']

# Circuit one-hot columns
circuit_cols = sorted([col for col in full_season_df.columns if col.startswith('circuit_id_')])

# Nationality one-hot columns
nationality_cols = sorted([col for col in full_season_df.columns if col.startswith('nationality_')])

# Constructor one-hot columns only (exclude stats columns)
constructor_cols = sorted([col for col in full_season_df.columns 
                           if col.startswith('constructor_') 
                           and col not in ['constructor_points','constructor_wins','constructor_standings_pos']])

# Combine into final column order
final_cols = core_cols + circuit_cols + nationality_cols + constructor_cols

# Reorder DataFrame
full_season_df = full_season_df[final_cols]

# Save
current_season_output_path = os.path.join(script_dir, "current_season_df.csv")
full_season_df.to_csv(current_season_output_path, index=False)
print(f"Current season DF saved, total rows: {len(full_season_df)}")

# Load the existing full dataset and 2025 dataset
csv_path = os.path.join(script_dir, 'historical_df.csv')
full_df = pd.read_csv(csv_path)
csv_path = os.path.join(script_dir, 'current_season_df.csv')
season_2025_df = pd.read_csv(csv_path)

# Ensure all columns from full_df exist in 2025 dataset
for col in full_df.columns:
    if col not in season_2025_df.columns:
        # Fill missing columns
        if col.startswith('circuit_id_') or col.startswith('nationality_') or col.startswith('constructor_'):
            season_2025_df[col] = False
        else:
            season_2025_df[col] = 0

# Ensure the column order matches the full dataset
season_2025_df = season_2025_df[full_df.columns]

# Append 2025 season to full_df
full_df = pd.concat([full_df, season_2025_df], ignore_index=True)

# Save the updated full dataframe
final_df_path = os.path.join(script_dir, "final_df.csv")
full_df.to_csv(final_df_path, index=False)
print(f"Updated full_df saved with {len(full_df)} total rows including 2025 season.")