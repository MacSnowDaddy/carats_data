"""airport_guesser module — AirportGuesser クラスを提供します."""
from __future__ import annotations

import warnings
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
    def __init__(self, airport_file: str, fixes_file: str=None, target_airports: Optional[List[str]] = None):
        '''
        Docstring for __init__
        
        :param airport_file: file of aerodromes. tsv format. columns should include 'ICAO', 'Japanese-ad-name, 'Latitude(ddmmss)', 'Longitude(ddmmss)'.
        :param fixes_file: file of bdyFixs. Optional. tsv format. columns should include 'Name',dummy-column, 'Latitude(ddmmss)', 'Longitude(ddmmss)'.
        :type airport_file: str This file's format should be... [name, any, lat[ddmmss], lon[ddmmss], [...]]
        :param target_airports: List of ICAO codes to be target airports. If None, all airports in airport_file are used.
        :type target_airports: Optional[List[str]]
        '''
        self.airport_file = airport_file
        if fixes_file is not None:
            self.is_to_guess_fixes = True
        else:
            self.is_to_guess_fixes = False
        self.fixes_file = fixes_file
        self.target_airports = target_airports
        self.df_all_trk = pd.DataFrame()
        self.df_airport = pd.DataFrame()
        self.df_trk_departed = pd.DataFrame()
        self.df_trk_landed = pd.DataFrame()
        self.df_guess = pd.DataFrame()
        self._load_airports_and_fixes()

    def _load_airports_and_fixes(self):
        ap = pd.read_csv(self.airport_file, header=None, usecols=[0,2,3],
                         delim_whitespace=True, names=["ICAO","Latitude","Longitude"])
        ap["Latitude_decimal"] = ap["Latitude"].apply(
            lambda x: round((int(x[:2]) + int(x[2:4])/60 + int(x[4:6])/3600),5))
        ap["Longitude_decimal"] = ap["Longitude"].apply(
            lambda x: round((int(x[:3]) + int(x[3:5])/60 + int(x[5:7])/3600),5))
        self.df_airport = ap

        if self.is_to_guess_fixes is True:
            fix = pd.read_csv(self.fixes_file, header=None, usecols=[0,2,3],
                            delim_whitespace=True, names=["Name","dummy","Latitude","Longitude"])
            fix["Latitude_decimal"] = fix["Latitude"].apply(
                lambda x: round((int(x[:2]) + int(x[2:4])/60 + int(x[4:6])/3600),5))
            fix["Longitude_decimal"] = fix["Longitude"].apply(
                lambda x: round((int(x[:3]) + int(x[3:5])/60 + int(x[5:7])/3600),5))
            self.df_fixes = fix
        if self.target_airports is None:
            self.target_airports = ap['ICAO'].tolist()
        if self.is_to_guess_fixes is True:
            self.target_airports += self.df_fixes['Name'].tolist()

    def set_trks_df(self, df_trks: pd.DataFrame):
        """
        AirportGuesserにトラッキングデータのDataFrameを設定します。
        
        :param df_trks: 使用するトラッキングデータのDataFrame。カラムは['date','time','Callsign','Latitude','Longitude','Altitude','Type']を含む必要があります。
        """
        self.df_all_trk = df_trks.copy()

    def load_trks_from_paths(self, paths: List[str]):
        warn_msg = "`deprecated_method` is deprecated and will be removed"
        warnings.warn(warn_msg, UserWarning)
        frames = []
        for p in paths:
            date = p.split('trk')[1].split('_')[0]
            df = pd.read_csv(p)
            df.columns = ["time","Callsign","Latitude","Longitude","Altitude","Type"]
            df.insert(0, 'date', None)
            df.loc[:, 'date'] = date
            frames.append(df)
        if frames:
            self.df_all_trk = pd.concat([self.df_all_trk] + frames, ignore_index=True)

    def load_trks_from_dates(self, dates: List[str], source_times: List[str], trk_dir: str):
        warn_msg = "`deprecated_method` is deprecated and will be removed"
        warnings.warn(warn_msg, UserWarning)
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
        # guess airports for departed and landed
        self.df_trk_departed = first[first['Altitude'] <= 6000].copy()
        self.df_trk_landed = last[last['Altitude'] <= 6000].copy()
        # df_trk_departed, df_trk_landedには含まれない、df_all_trkを保持するためのdfを作成する。
        # fixの抽出のために使用する。
        if self.is_to_guess_fixes is True:
            self.df_trk_in_the_air_at_first = first[~first['Callsign'].isin(
                pd.concat([self.df_trk_departed['Callsign'], self.df_trk_landed['Callsign']], ignore_index=True)
            )].copy()
            self.df_trk_in_the_air_at_last = last[~last['Callsign'].isin(
                pd.concat([self.df_trk_departed['Callsign'], self.df_trk_landed['Callsign']], ignore_index=True)
            )].copy()

        # 初期化カラム
        self.df_trk_departed['EntryPoint'] = np.nan
        self.df_trk_departed['Distance_to_EntryPoint'] = np.nan
        self.df_trk_landed['ExitPoint'] = np.nan
        self.df_trk_landed['Distance_to_ExitPoint'] = np.nan
        if self.is_to_guess_fixes is True:
            self.df_trk_in_the_air_at_first['EntryPoint'] = np.nan
            self.df_trk_in_the_air_at_first['Distance_to_EntryPoint'] = np.nan
            self.df_trk_in_the_air_at_last['ExitPoint'] = np.nan
            self.df_trk_in_the_air_at_last['Distance_to_ExitPoint'] = np.nan

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
            mask_dep = self.df_trk_departed['EntryPoint'].isna()
            if mask_dep.any():
                d_dep = np.sqrt((self.df_trk_departed.loc[mask_dep,'Latitude'] - lat)**2 +
                                (self.df_trk_departed.loc[mask_dep,'Longitude'] - lon)**2) * 111.32
                assign_mask = d_dep <= radius_km
                idxs = self.df_trk_departed.loc[mask_dep].index[assign_mask]
                self.df_trk_departed.loc[idxs, 'EntryPoint'] = icao
                self.df_trk_departed.loc[idxs, 'Distance_to_EntryPoint'] = d_dep[assign_mask]

            # 到着
            mask_arr = self.df_trk_landed['ExitPoint'].isna()
            if mask_arr.any():
                d_arr = np.sqrt((self.df_trk_landed.loc[mask_arr,'Latitude'] - lat)**2 +
                                (self.df_trk_landed.loc[mask_arr,'Longitude'] - lon)**2) * 111.32
                assign_mask = d_arr <= radius_km
                idxs = self.df_trk_landed.loc[mask_arr].index[assign_mask]
                self.df_trk_landed.loc[idxs, 'ExitPoint'] = icao
                self.df_trk_landed.loc[idxs, 'Distance_to_ExitPoint'] = d_arr[assign_mask]

        if self.is_to_guess_fixes is True:
            for _, fix_row in self.df_fixes.iterrows():
                name = fix_row['Name']
                lat = fix_row['Latitude_decimal']
                lon = fix_row['Longitude_decimal']

                # 最初に飛行中だったもの
                mask_first = self.df_trk_in_the_air_at_first['EntryPoint'].isna()
                if mask_first.any():
                    d_first = np.sqrt((self.df_trk_in_the_air_at_first.loc[mask_first,'Latitude'] - lat)**2 +
                                    (self.df_trk_in_the_air_at_first.loc[mask_first,'Longitude'] - lon)**2) * 111.32
                    assign_mask = d_first <= radius_km
                    idxs = self.df_trk_in_the_air_at_first.loc[mask_first].index[assign_mask]
                    self.df_trk_in_the_air_at_first.loc[idxs, 'EntryPoint'] = name
                    self.df_trk_in_the_air_at_first.loc[idxs, 'Distance_to_EntryPoint'] = d_first[assign_mask]

                # 最後に飛行中だったもの
                mask_last = self.df_trk_in_the_air_at_last['ExitPoint'].isna()
                if mask_last.any():
                    d_last = np.sqrt((self.df_trk_in_the_air_at_last.loc[mask_last,'Latitude'] - lat)**2 +
                                    (self.df_trk_in_the_air_at_last.loc[mask_last,'Longitude'] - lon)**2) * 111.32
                    assign_mask = d_last <= radius_km
                    idxs = self.df_trk_in_the_air_at_last.loc[mask_last].index[assign_mask]
                    self.df_trk_in_the_air_at_last.loc[idxs, 'ExitPoint'] = name
                    self.df_trk_in_the_air_at_last.loc[idxs, 'Distance_to_ExitPoint'] = d_last[assign_mask]
            #EntryPoint,ExitPointがfixで推定されたものを、df_trk_departed, df_trk_landedに追加する
            self.df_trk_departed = pd.concat(
                [self.df_trk_departed, self.df_trk_in_the_air_at_first], ignore_index=True)
            self.df_trk_landed = pd.concat(
                [self.df_trk_landed, self.df_trk_in_the_air_at_last], ignore_index=True)

        # マージして結果を作る
        self.df_guess = pd.merge(
            self.df_trk_departed[['date', 'Callsign','EntryPoint','Distance_to_EntryPoint']],
            self.df_trk_landed[['date', 'Callsign','ExitPoint','Distance_to_ExitPoint']],
            on=['date', 'Callsign'], how='outer')

    def get_guess_df(self, include_date=False) -> pd.DataFrame:
        """推定結果のDataFrameを取得します。
        Returns:
            pd.DataFrame: 推定結果のDataFrame.空の時は空のDataFrameを返します. 
            カラムは 'date'(指定時), 'Callsign', 'EntryPoint', 'Distance_to_EntryPoint', 
            'ExitPoint', 'Distance_to_ExitPoint' です.
        """
        if self.df_guess.empty:
            return self.df_guess

        if include_date is False:
            return self.df_guess[['Callsign', 'EntryPoint', 'Distance_to_EntryPoint',
                                  'ExitPoint', 'Distance_to_ExitPoint']]
        else:
            return self.df_guess

    def to_csv(self, path: str, include_trks=False, include_date=False):
        '''To write csv file of this output.
        
        param:
        include_trks: If this args is True, write all trks 
        appended thire EntryPoint and ExitPoint. Default:False'''
        warn_msg = "`deprecated_method` is deprecated and will be removed in v0.5"
        warnings.warn(warn_msg, UserWarning)
        if self.df_guess.empty:
            return
        if include_trks is True:
            self.df_all_trk = pd.merge(
                self.df_all_trk,
                self.df_guess[['Callsign', 'EntryPoint', 'ExitPoint']],
                how='left',
                on='Callsign'
                )
            if include_date is False:
                self.df_all_trk.drop(columns=['date']).to_csv(path, index=False)
            else:
                self.df_all_trk.to_csv(path, index=False)
        else:
            if include_date is False:
                self.df_guess[['Callsign', 'EntryPoint', 'Distance_to_EntryPoint',
                               'ExitPoint', 'Distance_to_ExitPoint']].to_csv(path, index=False)
            else:
                self.df_guess.to_csv(path, index=False)
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