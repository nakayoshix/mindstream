# MindStream

BlueMuse + Muse2を使用したリアルタイム脳波可視化プログラム

## 特徴

- Muse2の4チャンネル（TP9, AF7, AF8, TP10）をリアルタイム表示
- 時間軸・振幅スケールの動的調整
- LSL (Lab Streaming Layer) 経由でBlueMuseと接続

## 必要条件

- Python 3.10以上
- [uv](https://docs.astral.sh/uv/) (Pythonパッケージマネージャー)
- [BlueMuse](https://github.com/kowalej/BlueMuse) (Windows)
- Muse2 ヘッドバンド

## セットアップ

```bash
git clone <repository-url>
cd eeg_test1
uv sync
```

## 使用方法

1. BlueMuseを起動し、Muse2に接続
2. BlueMuseで「Start Streaming」をクリックしてLSLストリーミングを開始
3. プログラムを実行:

```bash
uv run python main.py
```

## 操作方法

| キー | 動作 |
|------|------|
| `ESC` | 終了 |
| `SPACE` | 再接続 |
| `R` | バッファリセット |
| `↑` | 振幅スケール縮小（波形拡大） |
| `↓` | 振幅スケール拡大（波形縮小） |
| `←` | 時間軸短縮（1秒〜） |
| `→` | 時間軸延長（〜30秒） |

## ライセンス

[GNU Affero General Public License v3.0](LICENSE)
