"""airport_guesserモジュールのテストコード"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from airport_guesser import AirportGuesser


# テストデータのパス
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
TEST_AIRPORT_FILE = os.path.join(TEST_DATA_DIR, 'test_airports.txt')
TEST_TRK_FILE_1 = os.path.join(TEST_DATA_DIR, 'trk20190816_00_12.csv')
TEST_TRK_FILE_2 = os.path.join(TEST_DATA_DIR, 'trk20190816_12_18.csv')


class TestAirportGuesserInit:
    """AirportGuesserクラスの初期化に関するテスト"""
    
    def test_init_with_valid_airport_file(self):
        """正常な空港ファイルでの初期化テスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        assert guesser.airport_file == TEST_AIRPORT_FILE
        assert not guesser.df_airport.empty
        assert guesser.is_to_guess_fixes is False
        
    def test_init_with_target_airports(self):
        """target_airportsを指定した初期化テスト"""
        target = ['RJTT', 'RJAA']
        guesser = AirportGuesser(
            airport_file=TEST_AIRPORT_FILE,
            target_airports=target
        )
        assert guesser.target_airports == target
        
    def test_init_without_target_airports(self):
        """target_airportsを指定しない場合、全空港が対象になることをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        # target_airportsは全空港のICAOコードを含むべき
        assert 'RJTT' in guesser.target_airports
        assert 'RJAA' in guesser.target_airports
        assert 'RJCC' in guesser.target_airports
        
    def test_init_dataframes_are_empty(self):
        """初期化時にデータフレームが空であることをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        assert guesser.df_all_trk.empty
        assert guesser.df_trk_departed.empty
        assert guesser.df_trk_landed.empty
        assert guesser.df_guess.empty


class TestLoadAirportsAndFixes:
    """空港データの読み込みと座標変換に関するテスト"""
    
    def test_airport_data_loaded(self):
        """空港データが正しく読み込まれることをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        df = guesser.df_airport
        assert not df.empty
        assert 'ICAO' in df.columns
        assert 'Latitude' in df.columns
        assert 'Longitude' in df.columns
        
    def test_coordinate_conversion(self):
        """座標変換（DDMMSS → 10進数）が正しく行われることをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        df = guesser.df_airport
        
        # RJTT（東京国際空港）の座標をチェック
        rjtt = df[df['ICAO'] == 'RJTT'].iloc[0]
        # 354030 → 35 + 40/60 + 30/3600 = 35.675度
        expected_lat = round(35 + 40/60 + 30/3600, 5)
        assert rjtt['Latitude_decimal'] == expected_lat
        
        # 1394600 → 139 + 46/60 + 0/3600 = 139.76667度
        expected_lon = round(139 + 46/60 + 0/3600, 5)
        assert rjtt['Longitude_decimal'] == expected_lon
        
    def test_all_airports_have_decimal_coordinates(self):
        """すべての空港に10進数座標が設定されていることをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        df = guesser.df_airport
        assert 'Latitude_decimal' in df.columns
        assert 'Longitude_decimal' in df.columns
        assert not df['Latitude_decimal'].isna().any()
        assert not df['Longitude_decimal'].isna().any()


class TestLoadTrksFromPaths:
    """トラッキングデータの読み込みに関するテスト"""
    
    def test_load_single_file(self):
        """単一のトラッキングファイルを読み込むテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        assert not guesser.df_all_trk.empty
        assert 'Callsign' in guesser.df_all_trk.columns
        assert 'Latitude' in guesser.df_all_trk.columns
        assert 'Longitude' in guesser.df_all_trk.columns
        assert 'Altitude' in guesser.df_all_trk.columns
        
    def test_load_multiple_files(self):
        """複数のトラッキングファイルを読み込むテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1, TEST_TRK_FILE_2])
        assert not guesser.df_all_trk.empty
        # ファイル1には9行、ファイル2には5行のデータがある
        assert len(guesser.df_all_trk) == 14
        
    def test_load_empty_list(self):
        """空のリストを渡した場合のテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([])
        assert guesser.df_all_trk.empty
        
    def test_columns_are_renamed(self):
        """カラム名が正しく設定されることをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        expected_columns = ["time", "Callsign", "Latitude", "Longitude", "Altitude", "Type"]
        assert list(guesser.df_all_trk.columns) == expected_columns


class TestLoadTrksFromDates:
    """日付指定でのトラッキングデータ読み込みに関するテスト"""
    
    def test_load_from_dates(self):
        """日付とタイムスロットを指定して読み込むテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_dates(
            dates=['20190816'],
            source_times=['00_12', '12_18'],
            trk_dir=TEST_DATA_DIR
        )
        assert not guesser.df_all_trk.empty
        # 両方のファイルが読み込まれている
        assert len(guesser.df_all_trk) == 14


class TestPreprocess:
    """前処理に関するテスト"""
    
    def test_preprocess_sorts_data(self):
        """前処理でデータがソートされることをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        # CallsignとTimeでソートされている
        callsigns = guesser.df_all_trk['Callsign'].tolist()
        assert callsigns == sorted(callsigns)
        
    def test_preprocess_separates_departed_landed(self):
        """前処理で出発・到着を分離することをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        
        # 最初の高度が6000ft以下のものが出発として抽出される
        assert not guesser.df_trk_departed.empty
        # 最後の高度が6000ft以下のものが到着として抽出される
        assert not guesser.df_trk_landed.empty
        
    def test_preprocess_filters_by_altitude(self):
        """前処理で高度によるフィルタリングが行われることをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        
        # 出発データは全て6000ft以下
        assert all(guesser.df_trk_departed['Altitude'] <= 6000)
        # 到着データは全て6000ft以下
        assert all(guesser.df_trk_landed['Altitude'] <= 6000)
        
    def test_preprocess_adds_required_columns(self):
        """前処理で必要なカラムが追加されることをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        
        assert 'EntryPoint' in guesser.df_trk_departed.columns
        assert 'Distance_to_EntryPoint' in guesser.df_trk_departed.columns
        assert 'ExitPoint' in guesser.df_trk_landed.columns
        assert 'Distance_to_ExitPoint' in guesser.df_trk_landed.columns
        
    def test_preprocess_with_empty_data(self):
        """空のデータで前処理を実行した場合のテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        # データを読み込まずに前処理
        guesser.preprocess()
        # エラーなく実行され、データフレームは空のまま
        assert guesser.df_trk_departed.empty
        assert guesser.df_trk_landed.empty


class TestAssign:
    """空港割り当てに関するテスト"""
    
    def test_assign_with_default_radius(self):
        """デフォルトの半径で空港を割り当てるテスト"""
        guesser = AirportGuesser(
            airport_file=TEST_AIRPORT_FILE,
            target_airports=['RJTT', 'RJAA']
        )
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        guesser.assign(radius_km=10.0)
        
        assert not guesser.df_guess.empty
        
    def test_assign_within_radius(self):
        """半径内の空港が正しく割り当てられることをテスト"""
        guesser = AirportGuesser(
            airport_file=TEST_AIRPORT_FILE,
            target_airports=['RJTT', 'RJAA', 'RJCC']
        )
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        # 大きな半径で割り当て
        guesser.assign(radius_km=50.0)
        
        # JAL001は東京近郊から出発
        guess = guesser.df_guess[guesser.df_guess['Callsign'] == 'JAL001']
        assert not guess.empty
        
    def test_assign_creates_guess_dataframe(self):
        """割り当て後にguess DataFrameが作成されることをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        guesser.assign(radius_km=10.0)
        
        assert not guesser.df_guess.empty
        assert 'Callsign' in guesser.df_guess.columns
        assert 'EntryPoint' in guesser.df_guess.columns
        assert 'ExitPoint' in guesser.df_guess.columns
        
    def test_assign_with_empty_data(self):
        """空のデータで割り当てを実行した場合のテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        # データを読み込まずに割り当て
        guesser.assign(radius_km=10.0)
        # エラーなく実行される
        assert guesser.df_guess.empty


class TestGetGuessDF:
    """推定結果取得に関するテスト"""
    
    def test_get_guess_df_returns_dataframe(self):
        """get_guess_dfがDataFrameを返すことをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        guesser.assign(radius_km=10.0)
        
        result = guesser.get_guess_df()
        assert isinstance(result, pd.DataFrame)
        
    def test_get_guess_df_has_required_columns(self):
        """get_guess_dfが必要なカラムを持つことをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        guesser.assign(radius_km=10.0)
        
        result = guesser.get_guess_df()
        expected_columns = [
            'Callsign', 'EntryPoint', 'Distance_to_EntryPoint',
            'ExitPoint', 'Distance_to_ExitPoint'
        ]
        for col in expected_columns:
            assert col in result.columns
            
    def test_get_guess_df_before_assignment(self):
        """割り当て前にget_guess_dfを呼んだ場合のテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        result = guesser.get_guess_df()
        assert result.empty


class TestToCsv:
    """CSV出力に関するテスト"""
    
    def test_to_csv_creates_file(self):
        """to_csvがファイルを作成することをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        guesser.assign(radius_km=10.0)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            output_path = f.name
        
        try:
            guesser.to_csv(output_path)
            assert os.path.exists(output_path)
            
            # ファイルが読み込めることを確認
            df = pd.read_csv(output_path)
            assert not df.empty
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
                
    def test_to_csv_with_include_trks(self):
        """include_trks=Trueでto_csvを実行するテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        guesser.assign(radius_km=10.0)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            output_path = f.name
        
        try:
            guesser.to_csv(output_path, include_trks=True)
            assert os.path.exists(output_path)
            
            # トラッキングデータ全体が含まれることを確認
            df = pd.read_csv(output_path)
            assert 'EntryPoint' in df.columns
            assert 'ExitPoint' in df.columns
            # 元のトラッキングデータのカラムも含まれる
            assert 'time' in df.columns
            assert 'Altitude' in df.columns
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
                
    def test_to_csv_with_empty_data(self):
        """空のデータでto_csvを実行した場合のテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            output_path = f.name
        
        try:
            # 空のデータでCSV出力（エラーなく実行されるべき）
            guesser.to_csv(output_path)
            # ファイルは作成されない（df_guessが空のため）
            # この動作は実装に依存する
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)


class TestEdgeCases:
    """エッジケースに関するテスト"""
    
    def test_distance_calculation_accuracy(self):
        """距離計算の精度をテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        guesser.assign(radius_km=50.0)
        
        # 距離が計算されていることを確認
        guess = guesser.get_guess_df()
        # NaNでない距離が存在する
        has_distance = ~guess['Distance_to_EntryPoint'].isna() | ~guess['Distance_to_ExitPoint'].isna()
        if has_distance.any():
            # 距離は負でない
            if not guess['Distance_to_EntryPoint'].isna().all():
                assert all(guess['Distance_to_EntryPoint'].dropna() >= 0)
            if not guess['Distance_to_ExitPoint'].isna().all():
                assert all(guess['Distance_to_ExitPoint'].dropna() >= 0)
    
    def test_multiple_callsigns(self):
        """複数のコールサインが正しく処理されることをテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        guesser.assign(radius_km=50.0)
        
        guess = guesser.get_guess_df()
        # 複数のコールサインが含まれる
        assert len(guess['Callsign'].unique()) > 1
        
    def test_no_matching_airports(self):
        """半径内に空港がない場合のテスト"""
        guesser = AirportGuesser(airport_file=TEST_AIRPORT_FILE)
        guesser.load_trks_from_paths([TEST_TRK_FILE_1])
        guesser.preprocess()
        # 非常に小さい半径で割り当て
        guesser.assign(radius_km=0.1)
        
        guess = guesser.get_guess_df()
        # データは存在するが、割り当てられていない可能性がある
        assert 'Callsign' in guess.columns


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
