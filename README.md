# MindStream

BlueMuse + Muse2を使用したリアルタイム脳波可視化プログラム

## 特徴

- Muse2の4チャンネル（TP9, AF7, AF8, TP10）をリアルタイム表示
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

## 操作方法

### キーボード操作

| キー | 動作 |
|------|------|
| `ESC` | 終了 |
| `SPACE` | 再接続 |
| `R` | バッファリセット |
| `↑` | 振幅スケール縮小（波形拡大） |
| `↓` | 振幅スケール拡大（波形縮小） |
| `←` | 時間軸短縮（1秒〜） |
| `→` | 時間軸延長（〜30秒） |

### スライダーUI

画面右側にスライダーパネルが表示されます:
- **Amplitude**: 振幅スケール（10〜5000μV）をドラッグで調整
- **Time**: 表示時間幅（1〜30秒）をドラッグで調整

スライダーとキーボード操作は連動しています。スライダーを無効にするには`config.toml`で`slider.enabled = false`を設定してください。

## プロジェクト構造

```
mindstream/
├── src/mindstream/          # ソースコード
│   ├── __init__.py          # パッケージ初期化
│   ├── __main__.py          # python -m mindstream エントリポイント
│   ├── cli.py               # CLI引数パーサー
│   ├── config.py            # 設定管理（dataclasses + TOML）
│   ├── constants.py         # 定数定義
│   ├── ui.py                # UIコンポーネント（スライダー等）
│   └── visualizer.py        # EEGVisualizerクラス
├── tests/                   # テストコード
│   ├── conftest.py          # pytest fixtures
│   ├── test_config.py       # 設定読み込みテスト
│   ├── test_cli.py          # CLI引数テスト
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
