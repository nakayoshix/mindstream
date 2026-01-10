# MindStream

BlueMuse + Muse2を使用したリアルタイム脳波可視化プログラム

## 特徴

- **マルチウィンドウ表示**: メインウィンドウ（脳状態インジケーター）とサブウィンドウ（生EEG波形）
- Muse2の4チャンネル（TP9, AF7, AF8, TP10）をリアルタイム表示
- **脳状態インジケーター**: 集中度、リラックス度、瞑想度をリアルタイム表示
- **周波数帯域解析**: デルタ、シータ、アルファ、ベータ波のパワーをリアルタイム表示
- **パワートレンド**: 周波数帯域パワーの時系列推移をグラフ表示
- 時間軸・振幅スケールの動的調整（キーボード＆スライダーUI）
- LSL (Lab Streaming Layer) 経由でBlueMuseと接続
- TOML設定ファイルとCLI引数による柔軟な設定

## 必要条件

- Python 3.14以上
- [uv](https://docs.astral.sh/uv/) (Pythonパッケージマネージャー)
- [BlueMuse](https://github.com/kowalej/BlueMuse) (Windows)
- Muse2 ヘッドバンド

## セットアップ

```bash
git clone https://github.com/nakayoshix/mindstream.git
cd mindstream
uv sync
```

## 使用方法

1. BlueMuseを起動し、Muse2に接続
2. BlueMuseで「Start Streaming」をクリックしてLSLストリーミングを開始
3. プログラムを実行:

```bash
# デフォルト設定で起動
uv run mindstream

# 設定ファイルを指定して起動
uv run mindstream -c config.toml

# CLI引数で設定を上書き
uv run mindstream --width 1920 --height 1080 --fps 120
```

### CLI オプション

```
mindstream [-c FILE] [--width N] [--height N] [--fps N]
           [--time-window N] [--amplitude N]

オプション:
  -c, --config FILE    設定ファイル（TOML形式）
  --width N            ウィンドウ幅（デフォルト: 1200）
  --height N           ウィンドウ高さ（デフォルト: 800）
  --fps N              フレームレート（デフォルト: 60）
  --time-window N      初期表示時間幅（秒）（デフォルト: 5）
  --amplitude N        初期振幅スケール（μV）（デフォルト: 100）
```

### 設定ファイル

`config.example.toml`をコピーして`config.toml`を作成することで、デフォルト設定を変更できます:

```bash
cp config.example.toml config.toml
# config.tomlを編集
```

設定の優先順位（高い順）:
1. CLI引数
2. `-c`で指定した設定ファイル
3. カレントディレクトリの`config.toml`（存在する場合）
4. ビルトインのデフォルト値

## 画面構成

### メインウィンドウ（脳状態表示）

起動時に表示されるメインウィンドウです。

```
┌────────────────────────────────────────────────────────────────────────┐
│ [EEG Window]                                         ● Connected       │
├──────────────────────────────────────────────────────┬─────────────────┤
│                                                      │                 │
│              Power Trend Graph                       │   Frequency     │
│           (Delta/Theta/Alpha/Beta)                   │                 │
│                                                      │   Delta ████    │
│                                                      │   Theta ███     │
│                                                      │   Alpha ██      │
│                                                      │   Beta  █       │
├──────────────────────────────────────────────────────┴─────────────────┤
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│   │    Focus     │  │    Relax     │  │   Meditate   │                 │
│   │     72%      │  │     45%      │  │     38%      │                 │
│   │  [========]  │  │  [=====]     │  │  [====]      │                 │
│   │    ↑ +5%     │  │    ↓ -2%     │  │    → 0%      │                 │
│   └──────────────┘  └──────────────┘  └──────────────┘                 │
└────────────────────────────────────────────────────────────────────────┘
```

- **Power Trend**: 各周波数帯域のパワー推移グラフ
- **Frequency**: 現在の周波数帯域パワー（相対値%）
- **Focus/Relax/Meditate**: 脳状態インジケーター（変化量付き）

### サブウィンドウ（EEG波形）

「EEG Window」ボタンまたは`E`キーで表示/非表示を切り替えます。

```
┌────────────────────────────────────────────────────────────────────────┐
│                         EEG Signals                                    │
│                        ● Connected                                     │
├────────────────────────────────────────────────────────────────────────┤
│     TP9  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            │
│     AF7  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            │
│     AF8  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            │
│     TP10 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~            │
├────────────────────────────────────────────────────────────────────────┤
│  Amplitude: [=========|=================] 100 uV                       │
│  Time:      [================|==========] 5 sec                        │
└────────────────────────────────────────────────────────────────────────┘
```

- **EEG波形**: 4チャンネルの生脳波をリアルタイム表示
- **スライダー**: 振幅スケール（10-2000μV）、時間幅（1-30秒）を調整

## 操作方法

### キーボード操作

| キー | 動作 |
|------|------|
| `ESC` | 終了 |
| `SPACE` | LSLストリームに再接続 |
| `R` | バッファリセット |
| `E` | サブウィンドウ（EEG波形）の表示/非表示 |
| `↑` | 振幅スケール縮小（+100μV、波形拡大） |
| `↓` | 振幅スケール拡大（-100μV、波形縮小） |
| `←` | 時間軸短縮（-1秒、最小1秒） |
| `→` | 時間軸延長（+1秒、最大30秒） |

### スライダーUI（サブウィンドウ）

サブウィンドウ下部にスライダーが表示されます:
- **Amplitude**: 振幅スケール（10〜2000μV）をドラッグで調整
- **Time**: 表示時間幅（1〜30秒）をドラッグで調整

スライダーとキーボード操作は連動しています。

### 周波数帯域

| 帯域 | 周波数範囲 | 関連する脳状態 |
|------|-----------|---------------|
| Delta (δ) | 0.5-4 Hz | 深い睡眠 |
| Theta (θ) | 4-8 Hz | 瞑想、眠気 |
| Alpha (α) | 8-13 Hz | リラックス、閉眼 |
| Beta (β) | 13-30 Hz | 集中、活動的思考 |

## プロジェクト構造

```
mindstream/
├── src/mindstream/
│   ├── __init__.py          # パッケージ初期化
│   ├── __main__.py          # python -m mindstream エントリポイント
│   ├── app.py               # MindStreamApp（マルチウィンドウ統括）
│   ├── cli.py               # CLI引数パーサー
│   ├── config.py            # 設定管理（dataclasses + TOML）
│   ├── constants.py         # 定数定義
│   ├── data_hub.py          # 共有データ管理（LSL接続、バッファ、解析器）
│   ├── frequency.py         # 周波数解析（FFT）
│   ├── indicator.py         # 脳状態インジケーター計算
│   ├── themes/
│   │   └── default.json     # pygame-gui テーマ
│   ├── ui/                  # UIコンポーネント（レガシー）
│   │   └── frequency_bar.py # 周波数バー定数
│   └── windows/             # ウィンドウモジュール
│       ├── __init__.py
│       ├── base.py          # BaseWindow抽象クラス
│       ├── main_window.py   # メインウィンドウ
│       └── sub_window.py    # サブウィンドウ（EEG波形）
├── tests/                   # テストコード
│   ├── conftest.py          # pytest fixtures
│   ├── test_cli.py          # CLI引数テスト
│   ├── test_config.py       # 設定読み込みテスト
│   ├── test_frequency.py    # 周波数解析テスト
│   └── test_ui.py           # UIテスト
├── config.example.toml      # 設定ファイルサンプル
├── pyproject.toml           # プロジェクト設定
└── .pre-commit-config.yaml  # pre-commit設定
```

## 開発

### テストの実行

```bash
uv run pytest           # テスト実行
uv run pytest -v        # 詳細出力
```

### 静的解析

```bash
uv run ruff check src/ tests/    # リント
uv run ruff format src/ tests/   # フォーマット
uv run ty check src/             # 型チェック
```

### pre-commit フック

コミット前に自動で静的解析を実行するには:

```bash
uv run pre-commit install        # フックをインストール
uv run pre-commit run --all-files  # 全ファイルに対して手動実行
```

## ライセンス

[GNU Affero General Public License v3.0](LICENSE)
