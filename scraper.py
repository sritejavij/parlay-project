from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import Location, Outcome, OutputType, OutputWriteOption, Position, PeriodType, Team
from datetime import datetime, date, timedelta
from pathlib import Path
import pandas as pd
import time
from unidecode import unidecode
import os
import json

YEAR = 2024
CURRENT_YEAR = datetime.now().year + 1
START_DATE = date(2024, 4, 8)
END_DATE = date(2024, 4, 10)
CURRENT_DATE = datetime.now().date()
REQUEST_DELAY = 12
CWD = Path('.')
OUT = CWD / "out"
TEAM_TO_TEAM_ABBREVIATIONS = {
    Team.ATLANTA_HAWKS: 'ATL',
    Team.BOSTON_CELTICS: 'BOS',
    Team.BROOKLYN_NETS: 'BRK',
    Team.CHICAGO_BULLS: 'CHI',
    Team.CHARLOTTE_HORNETS: 'CHO',
    Team.CLEVELAND_CAVALIERS: 'CLE',
    Team.DALLAS_MAVERICKS: 'DAL',
    Team.DENVER_NUGGETS: 'DEN',
    Team.DETROIT_PISTONS: 'DET',
    Team.GOLDEN_STATE_WARRIORS: 'GSW',
    Team.HOUSTON_ROCKETS: 'HOU',
    Team.INDIANA_PACERS: 'IND',
    Team.LOS_ANGELES_CLIPPERS: 'LAC',
    Team.LOS_ANGELES_LAKERS: 'LAL',
    Team.MEMPHIS_GRIZZLIES: 'MEM',
    Team.MIAMI_HEAT: 'MIA',
    Team.MILWAUKEE_BUCKS: 'MIL',
    Team.MINNESOTA_TIMBERWOLVES: 'MIN',
    Team.NEW_ORLEANS_PELICANS: 'NOP',
    Team.NEW_YORK_KNICKS: 'NYK',
    Team.OKLAHOMA_CITY_THUNDER: 'OKC',
    Team.ORLANDO_MAGIC: 'ORL',
    Team.PHILADELPHIA_76ERS: 'PHI',
    Team.PHOENIX_SUNS: 'PHO',
    Team.PORTLAND_TRAIL_BLAZERS: 'POR',
    Team.SACRAMENTO_KINGS: 'SAC',
    Team.SAN_ANTONIO_SPURS: 'SAS',
    Team.TORONTO_RAPTORS: 'TOR',
    Team.UTAH_JAZZ: 'UTA',
    Team.WASHINGTON_WIZARDS: 'WAS',
    
    # DEPRECATED TEAMS
    #Team.KANSAS_CITY_KINGS: 'KCK',
    #Team.NEW_JERSEY_NETS: 'NJN',
    #Team.NEW_ORLEANS_HORNETS: 'NOH',
    #Team.NEW_ORLEANS_OKLAHOMA_CITY_HORNETS: 'NOK',
    #Team.CHARLOTTE_BOBCATS: 'CHA',
    #Team.CHARLOTTE_HORNETS: 'CHH',
    #Team.SEATTLE_SUPERSONICS: 'SEA',
    #Team.ST_LOUIS_HAWKS: 'STL',
    #Team.VANCOUVER_GRIZZLIES: 'VAN',
    #Team.WASHINGTON_BULLETS: 'WSB'
}
POSITION_TO_POSITION_ABBREVIATIONS = {
    Position.POINT_GUARD: "PG", Position.SHOOTING_GUARD: "SG", Position.SMALL_FORWARD: "SF", Position.POWER_FORWARD: "PF", Position.CENTER: "C"
}

def main():
    if END_DATE >= CURRENT_DATE:
        raise ValueError("END_DATE is out of range")
    if YEAR > CURRENT_YEAR:
        raise ValueError("YEAR is out of range")
    
    OUT.mkdir(exist_ok=True)

    #generate_data()
    #generate_positions()
    #merge_positions()
    #generate_extra()
    #generate_full_data()
    #generate_names()
    update_data()
    #download(scrape_schedule(YEAR), "schedule.csv")

def update_data():
    year = YEAR
    old_df = pd.read_csv(OUT / f"{year}data.csv")

    dataframe = pd.DataFrame()
    dates = make_dates()
    progress = 0
    for i in dates:
        os.system("clear") # Terminal progress tracker
        print(f"Progress: {progress}/{len(dates)}\nDate: {i.strftime('%m/%d/%y')}")
        progress += 1

        time.sleep(REQUEST_DELAY)
        box_scores = scrape_box_scores(i)
        dataframe = pd.concat([box_scores, dataframe], ignore_index=True)
    os.system("clear") # Terminal progress tracker
    print(f"Progress: {progress}/{len(dates)}\nComplete!")

    dataframe = pd.concat([dataframe, old_df], ignore_index=True)
    download(dataframe, f"{YEAR}data.csv")

    merge_positions()
    generate_extra()
    print(dates)
    generate_full_data()
    generate_names()

def generate_full_data():
    year = YEAR
    exists = os.path.isfile(OUT / f"{year}data.csv")
    dataframe = pd.DataFrame()
    while exists:
        df = pd.read_csv(OUT / f"{year}data.csv")
        dataframe = pd.concat([dataframe, df])
        year = year - 1
        exists = os.path.isfile(OUT / f"{year}data.csv")

    download(dataframe, "full_data.csv")

def generate_names():
    df = pd.read_csv(OUT / "full_data.csv")
    if "FANTASY" in df.columns:
        df = df.groupby("NAME")["FANTASY"].mean()
        df = df.reset_index()
        df = df.sort_values("FANTASY", ascending=False)
        
    player_names = df["NAME"].unique()
    player_names = list(map(simplify_name, player_names))    

    with open(OUT / 'player_names.json', 'w') as file:
        json.dump(player_names, file)

def generate_data():
    dataframe = pd.DataFrame()
    dates = make_dates()
    progress = 0
    for i in dates:
        os.system("clear") # Terminal progress tracker
        print(f"Progress: {progress}/{len(dates)}\nDate: {i.strftime('%m/%d/%y')}")
        progress += 1

        time.sleep(REQUEST_DELAY)
        box_scores = scrape_box_scores(i)
        dataframe = pd.concat([box_scores, dataframe], ignore_index=True)
    
    os.system("clear") # Terminal progress tracker
    print(f"Progress: {progress}/{len(dates)}\nComplete!")
    
    download(dataframe, f"{YEAR}data.csv")

def generate_positions():
    positions = scrape_positions(YEAR)
    
    download(positions, f"{YEAR}positions.csv")

def merge_positions():
    dataframe = pd.read_csv(OUT / f"{YEAR}data.csv")
    positions = pd.read_csv(OUT / f"{YEAR}positions.csv")

    if "POSITION" in dataframe.columns:
        dataframe = dataframe.drop(columns="POSITION")
    dataframe = dataframe.merge(positions, on="NAME", how="left")
    dataframe["POSITION"] = dataframe["POSITION"].fillna("N/A")
    
    dataframe = dataframe[["DATE", "TEAM", "OPPONENT", "NAME", "POSITION", "MINUTES", "POINTS", "REBOUNDS", "ASSISTS", "STEALS", "BLOCKS",
                           "TURNOVERS", "FOULS", "FGM", "FGA", "3PM", "3PA", "FTM", "FTA", "OREB", "DREB", "STARTER?", "HOME?", "WIN?", 
                           "game_id"]]
    
    if "N/A" in dataframe["POSITION"]:
        print(f"N/A Position Found!")
    
    download(dataframe, f"{YEAR}data.csv")

def generate_extra():
    dataframe = pd.read_csv(OUT / f"{YEAR}data.csv")
    dataframe["PTS+REB+AST"] = dataframe["POINTS"] + dataframe["REBOUNDS"] + dataframe["ASSISTS"]
    dataframe["FANTASY"] = dataframe["POINTS"] + 1.2 * dataframe["REBOUNDS"] + 1.5 * dataframe["ASSISTS"] + 3 * (dataframe["STEALS"] + dataframe["BLOCKS"]) - dataframe["TURNOVERS"]
    dataframe["FANTASY"] = dataframe["FANTASY"].round(1)
    dataframe = dataframe[["DATE", "TEAM", "OPPONENT", "NAME", "POSITION", "MINUTES", "POINTS", "REBOUNDS", "ASSISTS", "PTS+REB+AST", "STEALS", "BLOCKS",
                           "TURNOVERS", "FOULS", "FGM", "FGA", "3PM", "3PA", "FTM", "FTA", "OREB", "DREB", "FANTASY", "STARTER?", "HOME?", "WIN?",  
                           "game_id"]]
    
    download(dataframe, f"{YEAR}data.csv")

def make_dates():
    dates = []

    if YEAR == 2024:
        start_date = START_DATE
        end_date = END_DATE
        no_games = [date(2023, 11, 7), date(2023, 11, 23), date(2023, 12, 3), date(2023, 12, 10), date(2023, 12, 24), date(2024, 2, 16), 
                    date(2024, 2, 17), date(2024, 2, 18), date(2024, 2, 19), date(2024, 2, 20), date(2024, 2, 21), date(2024, 4, 8), 
                    date(2024, 4, 13)]
    elif YEAR == 2023:
        start_date = date(2022, 10, 18)
        end_date = date(2023, 4, 9)
        no_games = [date(2022, 11, 8), date(2022, 11, 24), date(2022, 12, 24), date(2023, 2, 17), date(2023, 2, 18), date(2023, 2, 19), 
                    date(2023, 2, 20), date(2023, 2, 21), date(2023, 2, 22), date(2023, 4, 3)]
    elif YEAR == 2022:
        start_date = date(2021, 10, 19)
        end_date = date(2022, 4, 10)
        no_games = [date(2021, 11, 25), date(2021, 12, 24), date(2022, 2, 18), date(2022, 2, 19), date(2022, 2, 20), date(2022, 2, 21), 
                    date(2022, 2, 22), date(2022, 2, 23), date(2022, 4, 4)]
    elif YEAR == 2021:
        start_date = date(2020, 12, 22)
        end_date = date(2021, 5, 16)
        no_games = [date(2020, 12, 24), date(2021, 3, 5), date(2021, 3, 6), date(2021, 3, 7), date(2021, 3, 8), date(2021, 3, 9), 
                    date(2021, 3, 5)]
    elif YEAR == 2020:
        start_date = date(2019, 10, 22)
        end_date = date(2020, 8, 14)
        no_games = [date(2019, 11, 28), date(2019, 12, 24), date(2020, 2, 14), date(2020, 2, 15), date(2020, 2, 16), date(2020, 2, 17),
                    date(2020, 2, 18), date(2020, 2, 19)]
        covid_start = date(2020, 3, 12)
        covid_end = date(2020, 7, 30)
        i = covid_start
        while i < covid_end:
            no_games.append(i)
            i = i + timedelta(days=1)
    
    num_days = (end_date - start_date).days + 1
    for i in range(num_days):
        day = start_date + timedelta(i)
        if day in no_games:
            continue
        dates.append(day)

    return dates
    
def scrape_dates(year):
    sched = client.season_schedule(season_end_year=year)
    end_date_exclusive = END_DATE + timedelta(days=1)

    dates = set()  # Create a set to store unique dates
    started = False
    for game_data in sched:
        date = game_data["start_time"].date()
        if not started:
            if date != START_DATE:
                continue
            else:
                started = True
        if date == end_date_exclusive:
            break
        dates.add(date)

    dates = sorted(list(dates))

    return dates

def scrape_schedule(year):
    sched = client.season_schedule(season_end_year=year)
    end_date_exclusive = END_DATE + timedelta(days=1)

    dates, homes, aways = [], [], []
    started = False
    for game_data in sched:
        date = game_data["start_time"].date()
        if not started:
            if date != START_DATE:
                continue
            else:
                started = True
        if date == end_date_exclusive:
            break
        #date = date - timedelta(1) # Editing out inconsistincies
        formatted_date = date.strftime('%m/%d/%y')
        dates.append(formatted_date)

        home = game_data["home_team"]
        formatted_home = TEAM_TO_TEAM_ABBREVIATIONS[home]
        homes.append(formatted_home)

        away = game_data["away_team"]
        formatted_opponent = TEAM_TO_TEAM_ABBREVIATIONS[away]
        aways.append(formatted_opponent)

    df = pd.DataFrame({"DATE":dates, "HOME":homes, "AWAY":aways})

    return df

def scrape_positions(year):
    stats = client.players_season_totals(season_end_year=year)

    names, positions = [], []
    for player_data in stats:
        name = format_name(player_data["name"])
        if name in names:
            continue
        names.append(name)
        positions.append(POSITION_TO_POSITION_ABBREVIATIONS[player_data["positions"][0]])

    df = pd.DataFrame({"NAME":names, "POSITION":positions})
    df = df.sort_values(by="NAME")
    
    return df

def scrape_box_scores(date):
    box_scores = client.player_box_scores(day=date.day, month=date.month, year=date.year)
    dates, team, opponent, name, position, minutes, seconds, points, rebounds, assists, steals, blocks, turnovers, fouls, fgm, fga, tpm, tpa, ftm, fta, oreb, dreb, starter, home, win, game_ids = [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []
    for player_data in box_scores:
        dates.append(date.strftime('%m/%d/%y'))
        teamName = TEAM_TO_TEAM_ABBREVIATIONS[player_data["team"]]
        team.append(teamName)
        opponentName = TEAM_TO_TEAM_ABBREVIATIONS[player_data["opponent"]]
        opponent.append(opponentName)
        name.append(format_name(player_data["name"])) # Stephen Curry format
        #position.append("N/A")
        minutes.append(int(player_data["seconds_played"] / 60))
        seconds.append(player_data["seconds_played"]) # Temporary Row
        points.append(2 * player_data["made_field_goals"] + player_data["made_three_point_field_goals"] + player_data["made_free_throws"])
        rebounds.append(player_data["offensive_rebounds"] + player_data["defensive_rebounds"])
        assists.append(player_data["assists"])
        steals.append(player_data["steals"])
        blocks.append(player_data["blocks"])
        turnovers.append(player_data["turnovers"])
        fouls.append(player_data["personal_fouls"])
        fgm.append(player_data["made_field_goals"])
        fga.append(player_data["attempted_field_goals"])
        tpm.append(player_data["made_three_point_field_goals"])
        tpa.append(player_data["attempted_three_point_field_goals"])
        ftm.append(player_data["made_free_throws"])
        fta.append(player_data["attempted_free_throws"])
        oreb.append(player_data["offensive_rebounds"])
        dreb.append(player_data["defensive_rebounds"])
        starter.append(False)
        homeTracker = player_data["location"] == Location.HOME
        home.append(homeTracker)
        win.append(player_data["outcome"] == Outcome.WIN)

        # Creating game_ids
        dateString = date.strftime('%Y%m%d')
        teamString = teamName
        if not homeTracker:
            teamString = opponentName
        
        game_ids.append(f"{teamString.lower()}{dateString}")

    df = pd.DataFrame({"DATE":dates, "TEAM":team, "OPPONENT":opponent, "NAME":name, "MINUTES":minutes, "SECONDS":seconds, 
                       "POINTS":points, "REBOUNDS":rebounds, "ASSISTS":assists, "STEALS":steals, "BLOCKS":blocks, "TURNOVERS":turnovers, 
                       "FOULS":fouls, "FGM":fgm, "FGA":fga, "3PM":tpm, "3PA":tpa, "FTM":ftm, "FTA":fta, "OREB":oreb, "DREB": dreb, 
                       "STARTER?":starter, "HOME?":home, "WIN?":win, "game_id":game_ids})
    df = df[df["SECONDS"] >= 1] # Players must play at least 8 minutes to be counted

    # Define a custom sorting key function
    def custom_sort_key(row):
        if row["HOME?"]:
            return (row["TEAM"], 0, 0 - row["MINUTES"])  # Home team players first (0 for home)
        else:
            return (row["OPPONENT"], 1, 0 - row["MINUTES"])  # Opposing team players next (1 for away)
    #print(df)    

    df["SORT_KEY"] = df.apply(custom_sort_key, axis=1)
    df = df.sort_values(by=["SORT_KEY"])
    df = df.reset_index(drop=True)
    df = df.drop(columns=["SECONDS", "SORT_KEY"])

    return df

def format_name(full_name):
    full_name = unidecode(full_name)
    names = full_name.split()
    formatted_name = "ERROR"

    if len(names) >= 2:
        first_name = names[0]
        last_name = names[1]

        formatted_name = f"{first_name} {last_name}"

    return formatted_name

def simplify_name(name):
    name = unidecode(name)
    name = name.lower()
    name = name.replace(".", "")
    name = name.replace("'", "")
    name = name.replace("-", "")

    return name

def download(df, filename):
    df.to_csv(OUT / filename, index=False , mode="w")

if __name__ == "__main__":
    main()