'''
Docstring for trk_plotter
'''
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

class TrkPlotter:
    def __init__(self, df_trk: pd.DataFrame):
        """Initialize TrkPlotter with tracking data.

        This class provides methods to plot flight paths from tracking data.
        tracking data should include columns:['time', 'Latitude', 'Longitude']
        Args:
            df_trk (pd.DataFrame): DataFrame containing tracking data includes columns
                                   'time', 'Latitude', 'Longitude'.
        """
        self.df_trk = df_trk.copy()
        self.df_trk['time'] = pd.to_datetime(self.df_trk['time'])
    

    def plot_geojson_flight_points(self, key_column=None, key=None, title=None):
        """Plot geojson file of the flight trk as points.

        param:
            key_column:あとに指定するkeyが含まれるcolumn名
            key:column名に含まれるkeyword
        
        column='DEP_Airport', key='RJTT'などの使い方もできる。
        # 出力形式は以下の通り
        # {
        #   "type": "FeatureCollection",
        #   "features": [
        #     {
        #       "type": "Feature",
        #       "properties": {
        #         "_markerType": "CircleMarker",
        #         "_color": "#000000",
        #         "_opacity": 0.5,
        #         "_weight": 3,
        #         "_fillColor": "#ff0000",
        #         "_fillOpacity": 0.5,
        #         "_radius": 2
        #       },
        #       "geometry": {
        #         "type": "Point",
        #         "coordinates": [
        #           140.449219,
        #           42.358544
        #         ]
        #       },
        #     },
        #     {
        #       "type": "Feature",
        #       "properties": {
        #         "_markerType": "CircleMarker",
        #         "_color": "#000000",
        #         "_opacity": 0.5,
        #         "_weight": 3,
        #         "_fillColor": "#ff0000",
        #         "_fillOpacity": 0.5,
        #         "_radius": 2
        #       },
        #       "geometry": {
        #         "type": "Point",
        #         "coordinates": [
        #           140.394287,
        #           42.240719
        #         ]
        #       }
        #     }
        #   ]
        # }
        """
        if title is None:
            title = str(datetime.now())

        index_mask = self.df_trk[key_column] == key

        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        for index, row in self.df_trk[index_mask].iterrows():
            feature = {
                        "type": "Feature",
                        "properties": {
                            "_markerType": "CircleMarker",
                            "_color": "#000000",
                            "_opacity": 0.5,
                            "_weight": 3,
                            "_fillColor": "#ff0000",
                            "_fillOpacity": 0.5,
                            "_radius": 2
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": [
                                row['Longitude'],
                                row['Latitude']
                            ]
                        }
                    }
            geojson["features"].append(feature)
        import json
        with open(f'{title}.geojson', 'w') as f:
            json.dump(geojson, f, indent=4)

    def plot_geojson_flight_path(self, key_column=None, key=None, title=None):
        """Plot the flight path as line. 

        Basicly, key should be Callsign and key_column should be the column name
        which has Callsign.

        param:
            key_column:column name which contains callsign.
            key:callsign
        """
        if title is None:
            title = str(datetime.now())

        index_mask = self.df_trk[key_column] == key

        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        feature = {
                    "type": "Feature",
                    "properties": {
                        "_color": "#000000",
                        "_opacity": 0.5,
                        "_weight": 3
                    },
                    'geometry': {
                        'type':'LineString',
                        'coordinates':[]
                    }
                }
        for index, row in self.df_trk[index_mask].iterrows():
            coordinate =  [
                                row['Longitude'],
                                row['Latitude']
                            ]
            feature["geometry"]['coordinates'].append(coordinate)
        geojson["features"].append(feature)
        import json
        with open(f'{title}.geojson', 'w') as f:
            json.dump(geojson, f, indent=4)