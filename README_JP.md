# Product Hunt スクレイパー ドキュメント

## 概要

このアプリケーションは、Product Hunt のページから製品情報をスクレイピングし、OpenAI の GPT モデルを使用して詳細な説明と分析を生成します。複数の製品を並列処理し、結果を CSV ファイルに出力します。

## 前提条件

- Python 3.7 以上
- 環境変数に設定された OpenAI API キー
- 必要なパッケージ：
  - openai
  - beautifulsoup4
  - requests
  - typing

## 主要コンポーネント

### 1. OpenAI 連携（`generate_all_in_one`）

製品情報を GPT で処理し、強化されたコンテンツを生成します。

**入力パラメータ：**

- `product_name`：製品名（文字列）
- `desc_en`：英語での製品説明
- `launches_en`：英語でのローンチ情報
- `reviews_data`：以下の構造のレビューデータリスト：
  ```python
  [
    {
      "stars": int,  # 星評価（1-5）
      "text_en": str # 英語でのレビューテキスト
    }
  ]
  ```

**出力フォーマット：**

```json
{
  "enhancedDescription": "詳細な製品説明",
  "enhancedLaunches": "ローンチ情報",
  "reviews": "集約されたレビュー",
  "businessContext": {
    "initialCustomers": "初期顧客ターゲット",
    "persona": "ユーザーペルソナ",
    "marketSize": "市場規模分析"
  },
  "etcInfo": "追加インサイト"
}
```

### 2. Web スクレイパー（`scrape_product_hunt`）

Product Hunt ページから情報を抽出します。

**入力：** Product Hunt URL
**出力：** 以下を含む辞書：

- 製品名
- 説明
- 最近のローンチ
- レビュー
- 製品 URL
- ビジネスコンテキスト
- その他の情報

**スクレイピング要素：**

- 製品タイトル（h1 タグ）
- 説明文（class="text-18 font-normal text-light-gray"の div）
- 最近のローンチ（data-sentry-component="RecentLaunches"の div）
- レビュー（data-sentry-component="RatingReview"の div）
- 製品 URL（data-test="product-header-visit-button"の a）

### 3. CSV ライター（`write_csv`）

スクレイピングしたデータを CSV 形式で書き出します。

**パラメータ：**

- `data`：製品情報を含む辞書のリスト
- `csv_filename`：出力ファイル名

### 4. メインプロセス

- ThreadPoolExecutor を使用して複数の Product Hunt URL を並列処理
- デフォルトで最大 10 の同時ワーカー
- try-except ブロックでエラーを適切に処理
- コンソールに進捗を出力

## 使用方法

1. 環境変数の設定：

```bash
export OPENAI_API_KEY='あなたのAPIキー'
```

2. `TARGET_URLS`に Product Hunt URL のリストを準備

3. スクリプトの実行：

```bash
python main.py
```

## 出力

"producthunt_result.csv"という CSV ファイルを生成し、以下のカラムを含みます：

- 製品名
- 説明
- 最近のローンチ
- レビュー
- ProductHuntURL
- 製品 URL
- その他
- 初期顧客
- ペルソナ
- 市場規模

## エラー処理

- URL スクレイピングの失敗はログに記録され、実行は継続
- JSON 解析エラーはデフォルト構造の空の辞書を返す
- ネットワークエラーはキャッチしてログに記録
- BeautifulSoup の安全な解析による不正な HTML の処理

## パフォーマンスに関する考慮事項

- URL の並列処理によりスループットを改善
- 製品あたり最初の 20 レビューまでに制限
- CSV の適切な処理のために UTF-8-SIG エンコーディングを使用

## 制限事項

- Product Hunt の HTML 構造に依存
- 大量のリクエストに対してはレート制限が必要な場合あり
- OpenAI API のコストは使用量に応じて増加
- 製品あたり最大 20 レビューまで処
