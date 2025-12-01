"""airport_guesser module — AirportGuesser クラスを提供します."""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import List, Optional

class AirportGuesser:
    """
    トラッキングデータから出発/到着空港を推定するクラス。
    使用例:
      g = AirportGuesser(airport_file=".../Aerodrome_utf8.txt", target_airports=[...])
      g.load_trks_from_dates(['20190816'], ['00_12','12_18'], trk_dir="~/Desktop/201908")
      g.preprocess()
      g.assign(radius_km=10.0)
      df = g.get_guess_df()
      g.to_csv('airport_guess.csv')
    """
    def __init__(self, airport_file: str, target_airports: Optional[List[str]] = None):
        self.airport_file = airport_file
        self.target_airports = target_airports
        self.df_all_trk = pd.DataFrame()
        self.df_airport = pd.DataFrame()
        self.df_trk_departed = pd.DataFrame()
        self.df_trk_landed = pd.DataFrame()
        self.df_guess = pd.DataFrame()
        self._load_airports()

    def _load_airports(self):
        ap = pd.read_csv(self.airport_file, header=None, usecols=[0,2,3],
                         delim_whitespace=True, names=["ICAO","Latitude","Longitude"])
        ap["Latitude_decimal"] = ap["Latitude"].apply(
            lambda x: round((int(x[:2]) + int(x[2:4])/60 + int(x[4:6])/3600),5))
        ap["Longitude_decimal"] = ap["Longitude"].apply(
            lambda x: round((int(x[:3]) + int(x[3:5])/60 + int(x[5:7])/3600),5))
        self.df_airport = ap
        if self.target_airports is None:
            self.target_airports = ap['ICAO'].tolist()

    def load_trks_from_paths(self, paths: List[str]):
        frames = []
        for p in paths:
            df = pd.read_csv(p)
            df.columns = ["time","Callsign","Latitude","Longitude","Altitude","Type"]
            frames.append(df)
        if frames:
            self.df_all_trk = pd.concat([self.df_all_trk] + frames, ignore_index=True)

    def load_trks_from_dates(self, dates: List[str], source_times: List[str], trk_dir: str):
        paths = []
        for d in dates:
            for st in source_times:
                paths.append(f"{trk_dir}/trk{d}_{st}.csv")
        self.load_trks_from_paths(paths)

    def preprocess(self):
        if self.df_all_trk.empty:
            return
        self.df_all_trk = self.df_all_trk.sort_values(by=['Callsign','time'], ascending=[True, True])
        first = self.df_all_trk.groupby('Callsign', as_index=False).first()
        last = self.df_all_trk.groupby('Callsign', as_index=False).last()
        self.df_trk_departed = first[first['Altitude'] <= 6000].copy()
        self.df_trk_landed = last[last['Altitude'] <= 6000].copy()
        # 初期化カラム
        self.df_trk_departed['DEP_Airport'] = np.nan
        self.df_trk_departed['Distance_to_Airport'] = np.nan
        self.df_trk_landed['ARR_Airport'] = np.nan
        self.df_trk_landed['Distance_to_Airport'] = np.nan

    def assign(self, radius_km: float = 10.0):
        """target_airports の順に距離を計算して radius_km 以下なら割り当てる（最初に合致した空港を採用）"""
        if self.df_airport.empty or (self.df_trk_departed.empty and self.df_trk_landed.empty):
            return
        for icao in self.target_airports:
            row = self.df_airport[self.df_airport['ICAO'] == icao]
            if row.empty:
                continue
            lat = row['Latitude_decimal'].values[0]
            lon = row['Longitude_decimal'].values[0]

            # 出発
            mask_dep = self.df_trk_departed['DEP_Airport'].isna()
            if mask_dep.any():
                d_dep = np.sqrt((self.df_trk_departed.loc[mask_dep,'Latitude'] - lat)**2 +
                                (self.df_trk_departed.loc[mask_dep,'Longitude'] - lon)**2) * 111.32
                assign_mask = d_dep <= radius_km
                idxs = self.df_trk_departed.loc[mask_dep].index[assign_mask]
                self.df_trk_departed.loc[idxs, 'DEP_Airport'] = icao
                self.df_trk_departed.loc[idxs, 'Distance_to_Airport'] = d_dep[assign_mask]

            # 到着
            mask_arr = self.df_trk_landed['ARR_Airport'].isna()
            if mask_arr.any():
                d_arr = np.sqrt((self.df_trk_landed.loc[mask_arr,'Latitude'] - lat)**2 +
                                (self.df_trk_landed.loc[mask_arr,'Longitude'] - lon)**2) * 111.32
                assign_mask = d_arr <= radius_km
                idxs = self.df_trk_landed.loc[mask_arr].index[assign_mask]
                self.df_trk_landed.loc[idxs, 'ARR_Airport'] = icao
                self.df_trk_landed.loc[idxs, 'Distance_to_Airport'] = d_arr[assign_mask]

        # マージして結果を作る
        self.df_guess = pd.merge(
            self.df_trk_departed[['Callsign','DEP_Airport','Distance_to_Airport']],
            self.df_trk_landed[['Callsign','ARR_Airport','Distance_to_Airport']],
            on='Callsign', how='outer', suffixes=('_DEP','_ARR'))

    def get_guess_df(self) -> pd.DataFrame:
        return self.df_guess

    def to_csv(self, path: str):
        if self.df_guess.empty:
            return
        self.df_guess.to_csv(path, index=False)

# -------------------------
# 簡単な使用例（スクリプトとして使う場合）
if __name__ == "__main__":
    g = AirportGuesser(airport_file="~/programing/CARATS/MakeApt_v1/Aerodrome_utf8.txt",
                       target_airports=['RJTT','RJCC','RJAA'])
    g.load_trks_from_dates(['20190816'], ['00_12','12_18','18_24'], trk_dir="~/Desktop/201908")
    g.preprocess()
    g.assign(radius_km=10.0)
    print(g.get_guess_df().head())