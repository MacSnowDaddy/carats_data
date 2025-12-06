# airport_guesser テストドキュメント

このディレクトリには `airport_guesser` モジュールのテストコードが含まれています。

## テストの実行方法

### 全てのテストを実行

```bash
python3 -m pytest tests/test_airport_guesser.py -v
```

### 特定のテストクラスを実行

```bash
python3 -m pytest tests/test_airport_guesser.py::TestAirportGuesserInit -v
```

### 特定のテストメソッドを実行

```bash
python3 -m pytest tests/test_airport_guesser.py::TestAirportGuesserInit::test_init_with_valid_airport_file -v
```

## テストの構成

### TestAirportGuesserInit
- `test_init_with_valid_airport_file`: 正常な空港ファイルでの初期化
- `test_init_with_target_airports`: 対象空港を指定した初期化
- `test_init_without_target_airports`: 対象空港を指定しない場合
- `test_init_dataframes_are_empty`: 初期化時のデータフレーム状態

### TestLoadAirportsAndFixes
- `test_airport_data_loaded`: 空港データの読み込み
- `test_coordinate_conversion`: 座標変換（DDMMSS → 10進数）
- `test_all_airports_have_decimal_coordinates`: 全空港の座標変換

### TestLoadTrksFromPaths
- `test_load_single_file`: 単一トラッキングファイルの読み込み
- `test_load_multiple_files`: 複数トラッキングファイルの読み込み
- `test_load_empty_list`: 空リストの処理
- `test_columns_are_renamed`: カラム名の設定

### TestLoadTrksFromDates
- `test_load_from_dates`: 日付指定での読み込み

### TestPreprocess
- `test_preprocess_sorts_data`: データのソート
- `test_preprocess_separates_departed_landed`: 出発・到着の分離
- `test_preprocess_filters_by_altitude`: 高度フィルタリング
- `test_preprocess_adds_required_columns`: 必要カラムの追加
- `test_preprocess_with_empty_data`: 空データの処理

### TestAssign
- `test_assign_with_default_radius`: デフォルト半径での割り当て
- `test_assign_within_radius`: 半径内の空港割り当て
- `test_assign_creates_guess_dataframe`: 推定データフレームの作成
- `test_assign_with_empty_data`: 空データでの割り当て

### TestGetGuessDF
- `test_get_guess_df_returns_dataframe`: DataFrameの返却
- `test_get_guess_df_has_required_columns`: 必要カラムの確認
- `test_get_guess_df_before_assignment`: 割り当て前の呼び出し

### TestToCsv
- `test_to_csv_creates_file`: CSVファイルの作成
- `test_to_csv_with_include_trks`: トラッキングデータを含むCSV出力
- `test_to_csv_with_empty_data`: 空データのCSV出力

### TestEdgeCases
- `test_distance_calculation_accuracy`: 距離計算の精度
- `test_multiple_callsigns`: 複数コールサインの処理
- `test_no_matching_airports`: マッチする空港がない場合

## テストデータ

`test_data/` ディレクトリには以下のテストデータが含まれています：

- `test_airports.txt`: テスト用空港データ（RJTT、RJAA、RJCC、RJOO、RJFF）
- `trk20190816_00_12.csv`: テスト用トラッキングデータ（午前）
- `trk20190816_12_18.csv`: テスト用トラッキングデータ（午後）

## 必要な依存関係

- Python 3.12+
- pandas
- numpy
- pytest

依存関係のインストール:
```bash
pip install pandas numpy pytest
```

## テストカバレッジ

このテストスイートは以下の機能をカバーしています：

- ✅ クラスの初期化
- ✅ 空港データの読み込みと座標変換
- ✅ トラッキングデータの読み込み
- ✅ データの前処理
- ✅ 空港の割り当て
- ✅ 結果の取得
- ✅ CSV出力
- ✅ エッジケースの処理
