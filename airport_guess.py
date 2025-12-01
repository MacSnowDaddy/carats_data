import pandas as pd
import numpy as np

dates = ['20190816']#, '20190813', '20190814', '20190815', '20190816', '20190817', '20190818']
source_times = ['00_12', '12_18', '18_24']

df_all_trk = pd.DataFrame()

df_airport_guess = pd.DataFrame()

df_trk_just_deperted = pd.DataFrame()
df_trk_just_before_landed = pd.DataFrame()

# 抽出する空港の順番を設定。数の多いものから順に設定することで効率化を図る。
target_airports = ['RJTT', 'RJFF', 'RJBB', 'RJAA', 'ROAH', 'RJCC', 'RJGG', 'RJOO', 'RJSS', 'RJFK']

for date in dates:
    for source_time in source_times:
        df_trk_reading = pd.read_csv(f'~/Desktop/201908/trk{date}_{source_time}.csv')
        df_trk_reading.columns = ["time", "Callsign", "Latitude", "Longitude", "Altitude", "Type"]
        df_airport = pd.read_csv("~/programing/CARATS/MakeApt_v1/Aerodrome_utf8.txt",
                            header=None, usecols=[0, 2, 3], delim_whitespace=True, names=["ICAO", "Latitude", "Longitude"])

        df_airport["Latitude_decimal"] =df_airport["Latitude"].apply(lambda x: round((int(x[:2]) + int(x[2:4])/60 + int(x[4:6])/3600),5))
        df_airport["Longitude_decimal"] =df_airport["Longitude"].apply(lambda x: round((int(x[:3]) + int(x[3:5])/60 + int(x[5:7])/3600),5))

        df_all_trk = pd.concat([df_all_trk, df_trk_reading], ignore_index=True)

# filterd_trk_frameをCallsign, timeの順でソートする
df_all_trk_sorted = df_all_trk.sort_values(by=['Callsign', 'time'], ascending=[True, True])

# 各Callsignについて、最初のデータと最後のデータを取得する
df_first_data_of_each_callsign = df_all_trk_sorted.groupby('Callsign', as_index=False).first()
df_last_data_of_each_callsign = df_all_trk_sorted.groupby('Callsign', as_index=False).last()

# first_dataが6000ft以下のものを出発した便とする
# last_dataが6000ft以下のものを着陸した便とする
df_trk_just_deperted = df_first_data_of_each_callsign[df_first_data_of_each_callsign['Altitude'] <= 6000]
df_trk_just_before_landed = df_last_data_of_each_callsign[df_last_data_of_each_callsign['Altitude'] <= 6000]

df_temp_dep_flight = pd.DataFrame()
df_temp_arr_flight = pd.DataFrame()

df_trk_just_deperted['DEP_Airport'] = np.nan
df_trk_just_before_landed['ARR_Airport'] = np.nan

for target_airport in target_airports:
    # 使用するデータはap_frameの緯度経度。
    # TARGET_AIRPORTの緯度経度を取得
    target_airport_df = df_airport[df_airport['ICAO'] == target_airport]
    target_airport_lat = target_airport_df['Latitude_decimal'].values[0]
    target_airport_lon = target_airport_df['Longitude_decimal'].values[0]
    
    # 出発空港、到着空港が未設定のものに対して、TARGET_AIRPORTまでの距離を計算
    df_trk_just_deperted.loc[df_trk_just_deperted['DEP_Airport'].isna(), 'Distance_to_Airport_temp'] = \
        np.sqrt((df_trk_just_deperted['Latitude']       - target_airport_lat)**2
                + (df_trk_just_deperted['Longitude']      - target_airport_lon)**2) * 111.32
    df_trk_just_before_landed.loc[df_trk_just_before_landed['ARR_Airport'].isna(), 'Distance_to_Airport_temp'] = \
        np.sqrt((df_trk_just_before_landed['Latitude']  - target_airport_lat)**2
                + (df_trk_just_before_landed['Longitude'] - target_airport_lon)**2) * 111.32

    # Distance_to_Airportが10km以下のものを抽出(出発空港、到着空港未設定のものに対して)
    df_trk_just_deperted.loc[
        df_trk_just_deperted['DEP_Airport'].isna() & (df_trk_just_deperted['Distance_to_Airport_temp'] <= 10.0),
        'DEP_Airport'] = target_airport

    df_trk_just_deperted.loc[
        df_trk_just_deperted['DEP_Airport'].isna() & (df_trk_just_deperted['Distance_to_Airport_temp'] <= 10.0),
         ['Distance_to_Airport']] = df_trk_just_deperted['Distance_to_Airport_temp']

    df_trk_just_before_landed.loc[
        df_trk_just_before_landed['ARR_Airport'].isna() & (df_trk_just_before_landed['Distance_to_Airport_temp'] <= 10.0),
         ['ARR_Airport']] = target_airport
    df_trk_just_before_landed.loc[
        df_trk_just_before_landed['ARR_Airport'].isna() & (df_trk_just_before_landed['Distance_to_Airport_temp'] <= 10.0),
         ['Distance_to_Airport']] = df_trk_just_before_landed['Distance_to_Airport_temp']

    # 不要な列を削除
    df_trk_just_deperted.drop(['Distance_to_Airport_temp'], axis=1, inplace=True)
    df_trk_just_before_landed.drop(['Distance_to_Airport_temp'], axis=1, inplace=True)

df_airport_guess = pd.merge(df_trk_just_deperted[['Callsign', 'DEP_Airport', 'Distance_to_Airport']],
                          df_trk_just_before_landed[['Callsign', 'ARR_Airport', 'Distance_to_Airport']],
                          on='Callsign', how='outer', suffixes=('_DEP', '_ARR'))
