# Character Scene Tools

ラフ画像の構図・ポーズを保ちながら、参照画像のキャラクターへ置き換えるためのComfyUIカスタムノード集です。キャラクターの画像・特徴とシーン設定を分けて管理し、Positive／Negative Promptを組み立てます。

**新しく使い始める場合は、JSON版のBuild Scene Promptsをおすすめします。** JSON版は後から開発した新方式で、TXT版の運用を踏まえてプロンプトをより洗練しています。構図の固定、位置ごとのキャラクター割り当て、重複や特徴の混在を防ぐ指示を詳細テンプレートにまとめ、キャラクターを差し替えても同じ形式で出力できます。

## JSON版とTXT版の違い

| | JSON版：新方式・推奨 | TXT版：従来方式 |
|---|---|---|
| 主なノード | **Build Scene Prompts** | **Load Character Reference**／**Load Character References (Up to 5)** |
| キャラクター情報 | 参照画像＋`character.json` | 参照画像＋`positive.txt`＋`negative.txt` |
| シーン設定 | シーンJSONに保存し、必要な項目だけ上書き | ワークフロー内のテキストで指定 |
| プロンプト | より洗練した詳細テンプレートへ自動展開 | 読み込んだ文章をテキスト整形ノードなどで結合 |
| 参照キャラクター数 | 1〜3人 | 単体ローダーは1人、複数ローダーは最大5人 |
| 向いている使い方 | シーンとキャラクターを再利用し、統一した詳細指示で生成する | 既存のTXT資産や手動で調整した文章を使い続ける |

JSON形式そのものが画質を向上させるわけではありません。JSON版の違いは、設定を整理し、より詳細に調整したプロンプトへ展開する仕組みにあります。生成結果はモデル・参照画像・シーン設定にも依存します。

### ワークフローを開く

- **[JSON版ワークフロー](examples/workflows/character-replacement-from-json.json)** — Build Scene Promptsを使用
- **[TXT版ワークフロー](examples/workflows/character-replacement-from-txt.json)** — 従来の複数キャラクターローダーを使用

ダウンロードしたJSONをComfyUIへドラッグ＆ドロップするか、ファイルを開く操作で読み込んでください。ラフ画像とモデルの選択は、ご自身の環境に合わせて変更します。

## インストール

リポジトリ全体を、次のように1つのフォルダーとして配置します。

```text
ComfyUI/
└── custom_nodes/
    └── character-scene-tools/
        ├── __init__.py
        ├── nodes/
        ├── presets/
        └── ...
```

`__init__.py`が`custom_nodes/character-scene-tools/`の直下にあることを確認してください。

Gitを使う場合は、実際のComfyUIの場所に合わせて実行します。

```shell
git clone https://github.com/MKDir43/comfyui-image-prompt-package.git ComfyUI/custom_nodes/character-scene-tools
```

配置後、ComfyUIを再起動して画面を再読み込みします。リポジトリのフォルダー名が`comfyui-image-prompt-package`のままでも読み込めます。

依存ライブラリは`numpy`、`Pillow`、`torch`です。不足している場合は、ComfyUIが使用するPython環境で次を実行してください。

```shell
python -m pip install -r requirements.txt
```

## JSON版を使う

### 1. キャラクターを用意する

1人につき1つのフォルダーを作り、参照画像と`character.json`を入れます。

```text
CharacterReferences/
├── character_01/
│   ├── image.png
│   └── character.json
└── character_02/
    ├── image.png
    └── character.json
```

`character.json`には名前、髪、目、識別特徴、避けたい描写などを記載します。画像のファイル名はJSONの`image`で指定します。

記載例は [サンプルのcharacter.json](examples/character-references/charactor01/character.json)、各項目は [Build Sceneの説明](docs/scene-prompt-builder.md) を参照してください。既存のTXTからJSONへの自動変換・同期は行いません。

### 2. シーンを用意する

`presets/scenes/`の [reference-layout.json](presets/scenes/reference-layout.json) をコピーして、背景・照明・衣装・人物の配置やポーズを設定します。

**[シーンJSONの書き方・全項目一覧](presets/scenes/README.md)** に、コピーして使える例と各設定の意味をまとめています。

新しいシーンファイルを追加したら、ComfyUIを再起動して画面を再読み込みしてください。既存ファイルの内容変更は次回実行時に読み直します。

### 3. Build Scene Promptsを設定する

| 入力 | 設定するもの |
|---|---|
| `scene` | 使用するシーンJSONのファイル名 |
| `character_root` | キャラクターフォルダーの親ディレクトリ。空欄ならパッケージ内の`examples/character-references/` |
| `character_a`／`character_b`／`character_c` | 親ディレクトリ配下のキャラクターフォルダー名。使わない枠は空欄または`None` |
| `scene_overrides` | 今回だけ変更するシーン設定。通常は`{}` |

パッケージ内のサンプルを試す場合：

```text
scene           = reference-layout.json
character_root  = （空欄）
character_a     = charactor01
character_b     = None
character_c     = None
scene_overrides = {}
```

キャラクターは1人以上指定してください。A／B／Cすべてを埋める必要はありません。

### 4. 画像とプロンプトを接続する

```text
ラフ画像                         → 生成側のImage 01
Build Sceneのimage_02以降         → 生成側のImage 02以降
Build Sceneのpositive_prompt      → Positiveのテキスト入力
Build Sceneのnegative_prompt      → Negativeのテキスト入力
```

- **Image 01**：構図・ポーズ・カメラ・人物同士の位置関係
- **Image 02以降**：顔・髪・配色・固有の特徴など、キャラクターのデザイン

A／B／Cはシーンの位置を表します。例えばAとCだけを指定すると、AはImage 02、CはImage 03になりますが、Cの配置・ポーズはシーンの`slots.c`を維持します。

参照画像は使用人数分だけ接続してください。未使用の画像出力は1×1の黒画像です。`character_mapping`で対応を、`diagnostics`で診断を確認できます。

## プロンプトの構成

Positive／Negativeは、次の3層で管理します。

| セクション | 内容 |
|---|---|
| **COMMON** | 画風、構図固定、参照画像の役割、全体の共通条件 |
| **SCENE** | 背景、照明、位置、ポーズ、視線、表情、今回の衣装や小道具 |
| **CHARACTER** | キャラクター固有の特徴と失敗対策 |

JSON版では、この詳細な構成へ設定値を自動展開します。キャラクターの髪型などをシーンごとに書き直す必要がなく、位置やポーズを維持したまま人物を入れ替えられます。

## TXT版を使う

TXT版は従来どおり使用できます。各キャラクターフォルダーに`image.png`、`positive.txt`、`negative.txt`を配置し、ローダーの`root_path`とフォルダー名を指定します。

- **Load Character Reference**：1人分の画像と文章を読み込みます。
- **Load Character References (Up to 5)**：最大5人分を読み込み、未使用枠を除いてA、B、C…と連続して割り当てます。

TXT版はキャラクター枠を詰めて割り当てるため、シーンの位置識別子を保つJSON版とは割り当ての扱いが異なります。

詳しくは [TXT版の使い方](docs/character-replacement.md) を参照してください。

## 既存環境から更新する場合

- 旧パッケージを個別に配置している場合は、同じノードが重複登録されないよう、旧フォルダーを`custom_nodes`の外へ退避してから統合版を配置してください。
- 既存のTXTローダーとTXTデータはそのまま使えます。サンプルの場所を変更した場合は`root_path`を更新してください。
- 旧Build Sceneや更新前の入力欄が残る場合は、ComfyUIを再起動し、Build Sceneノードを追加し直してください。

## ファイルの場所

| 場所 | 内容 |
|---|---|
| `examples/workflows/` | JSON版・TXT版のワークフロー |
| `examples/character-references/` | キャラクター参照のサンプル |
| `presets/scenes/` | シーンJSONと記載方法のREADME |
| `docs/` | 各ノードとワークフローの詳しい説明 |
| `nodes/` | ノード実装と詳細テンプレート |
| `tests/` | 読み込み・プロンプト組み立てなどのテスト |

## 開発・検証

ノードの保存用識別子は`ImagePromptPackageLoader`、`MultiPromptPackageLoader`、`ScenePromptTemplate`です。ComfyUIのメニューでは`Character Scene Tools/References`と`Character Scene Tools/Prompts`に表示されます。

リポジトリのルートから実行します。

```shell
python -m unittest discover -s tests -v
```

テストはノード登録、参照画像・JSONの読み込み、人物の差し替え、シーンの維持、詳細テンプレートの一致を確認します。モデルによる画像生成やComfyUI画面の操作確認は含みません。