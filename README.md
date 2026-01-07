# EEG Test1

BlueMuse + Muse2を使用したリアルタイム脳波可視化プログラム

## セットアップ

```bash
uv sync
```

## 使用方法

1. BlueMuseを起動し、Muse2に接続
2. BlueMuseでLSLストリーミングを開始
3. プログラムを実行:

```bash
uv run python main.py
```

## 操作方法

- `ESC`: 終了
- `SPACE`: 再接続
- `R`: バッファリセット
