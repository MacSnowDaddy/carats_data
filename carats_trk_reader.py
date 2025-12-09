'''CARATSデータのトラックデータを読み込み、メモリ使用量を圧縮した上でDataFrameとして取得するためのコード'''
from typing import List
import pandas as pd
import argparse

class CaratsTrackReader:
    def __init__(self):
        self.df_all_trk = pd.DataFrame()

    def read_trk_files(self, trk_paths: List[str]) -> pd.DataFrame:
        frames = []
        for p in trk_paths:
            date = p.split('trk')[1].split('_')[0]
            df = pd.read_csv(p,
                header=None, 
                names=["time",
                       "Callsign",
                       "Latitude",
                       "Longitude",
                       "Altitude",
                       "Type"],
                dtype={"Callsign": "category",
                       "Latitude": "float32",
                       "Longitude": "float32",
                       "Altitude": "int32",
                       "Type": "category"}
            )
            df.insert(0, 'date', None)
            df.loc[:, 'date'] = date
            date_dt = pd.to_datetime(df['date'])
            time_td = pd.to_timedelta(df['time'])
            df['datetime'] = date_dt.dt.normalize() + time_td
            df = df.drop(columns=['date', 'time'])
            df = df.reindex(columns=['datetime', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Type'])
            frames.append(df)
        if frames:
            self.df_all_trk = pd.concat(
                [self.df_all_trk] + frames,
                 ignore_index=True
            )
        return self.df_all_trk

def main(argv=None):
    parser = argparse.ArgumentParser(description="Read CARATS trk CSV files into a compressed DataFrame.")
    parser.add_argument('--input', '-i', nargs='*', required=True, help='trk CSV file(s) or glob patterns. e.g. ~/Desktop/201908/*.csv')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    args = parser.parse_args(argv)
    reader = CaratsTrackReader()
    df = reader.read_trk_files(args.input)
    if args.verbose:
        print(df.head())
        print(df.info())

if __name__ == "__main__":
    main()