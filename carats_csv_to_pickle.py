import glob
from tkinter import filedialog

import pandas as pd


def create_track_frame() -> pd.DataFrame:
    """
    ファイル選択ダイアログを表示し、選択されたファイルを読み込んでTrackのDataFrameに変換する
    """
    #pathをダイアログで選択する
    path = filedialog.askdirectory()
    all_files = glob.glob(path + "/*.csv")

    li = []

    for filename in all_files:
        df = pd.read_csv(filename, index_col=None, header=None)
        li.append(df)

    frame = pd.concat(li, axis=0, ignore_index=True)
    frame.columns = ["time", "Callsign", "Latitude", "Longitude", "Altitude", "Type"]

    return frame

def create_aerodrome_frame() -> pd.DataFrame:
    """
    ファイル選択ダイアログを表示し、選択されたファイルを読み込んで空港のICAOコードとLatLonを含むDataFrameに変換する
    """
    #pathをダイアログで選択する
    path = filedialog.askopenfilename(title="select ap dict csv file.")

    frame = pd.read_csv(path, header=None, usecols=[0, 2, 3], delim_whitespace=True, names=["ICAO", "Latitude", "Longitude"])

    frame["Latitude_decimal"] = frame["Latitude"].apply(lambda x: round((int(x[:2]) + int(x[2:4])/60 + int(x[4:6])/3600),5))
    frame["Longitude_decimal"] = frame["Longitude"].apply(lambda x: round((int(x[:3]) + int(x[3:5])/60 + int(x[5:7])/3600),5))

    return frame
