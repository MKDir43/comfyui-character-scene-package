# Build Scene Prompts

## テンプレートが異なる2つのノード

| 表示名 | ノードID | 使用するテンプレート |
|---|---|---|
| Build Scene Prompts | `ScenePromptTemplate` | `nodes/scene_templates.py` |
| Build Scene Prompts (NSFW) | `ScenePromptTemplateNSFW` | `nodes/scene_templates_nsfw.py` |

入力・出力名、順序、型は同じです。シーンJSON、キャラクターJSON、`character_root`も共通の形式で使用できます。ComfyUIのノード検索で使いたい方を追加してください。既存のBuild Sceneは引き続き元のテンプレートを使います。

NSFWのテンプレートは、追加時点の元テンプレートと同じ内容で独立したファイルとして用意しています。NSFW側の`FIELD_DEFAULTS`、`POSITIVE_TEMPLATE`、`NEGATIVE_TEMPLATE`、`render_template`を変更しても、元ノードには反映されません。変更後はComfyUI本体を再起動してください。PythonファイルはJSONと異なり実行のたびに再読み込みされません。

`FIELD_DEFAULTS`はシーンJSONや`scene_overrides`より優先順位が低いため、JSON側で指定済みの項目はJSONの値になります。新しい共通変数をNSFW側の`FIELD_DEFAULTS`に追加した場合、そのノードでのみ`values`から指定できます。キャラクター項目・スロット項目の形式は共通です。

現在の人数別展開はテンプレート内の見出し・区切りを使用します。固定文を編集する際も、`[SCENE]`／`[CHARACTER]`、位置対応行、`A (`／`B (`／`C (`、`CHARACTER A —`などの人物ブロック見出し、`Each position uses only`／`All characters in this group:`の区切りは維持してください。テンプレート全体の構造を変える場合は、`scene_prompt_builder.py`の`selected_templates`も対応が必要です。

Build Scene専用のJSONを使い、詳細なCOMMON／SCENE／CHARACTERテンプレートへキャラクターとシーンの設定を展開します。既存の2つの参照ローダーは従来どおりTXTを読み込みます。

## 使い方

1. [パッケージ全体をインストール](../README.md#インストール)します。
2. **Build Scene Prompts**を追加します。旧版の大量の変数欄があるノードは、削除して新しく追加してください。今回このノードの入力構成を変更しています。
3. `scene`で`reference-layout.json`、`character_a`に`charactor01`を入力します。使わないB／Cは`None`にします。
4. `positive_prompt`／`negative_prompt`をテキストエンコード側へ、`image_02`以降を参照画像側へ接続します。Image 01のラフ画像は従来の画像ノードで別途読み込みます。
5. 別のキャラクターJSONを登録したら、A／B／Cの選択を変えるだけで画像と特徴文が切り替わります。

既存ノードの`root_path`に指定しているデータと同じ場所を使えます。ノードの`character_root`に参照フォルダーの絶対パスを入力してください。空欄の場合はインストール先の`examples/character-references/`を使います。`character_a`／`character_b`／`character_c`には、その配下のフォルダー名を入力します。TXTだけでは読み込めず、`character.json`が必要です。

```text
comfyui-character-scene-package/
├── examples/character-references/
│   └── charactor01/
│       ├── image.png
│       ├── positive.txt       # 既存ローダー専用。変更不要
│       ├── negative.txt       # 既存ローダー専用。変更不要
│       └── character.json     # Build Scene専用
└── presets/scenes/
    └── reference-layout.json  # Build Scene専用
```

追加したシーンJSONを選択肢へ反映するにはComfyUIを再起動して画面を再読み込みしてください。キャラクターはフォルダー名を直接入力するため、追加時の再起動は不要です。選択済みJSONの内容や画像を編集した場合、次回実行で読み直します。

## キャラクターJSON

ファイル名は`character.json`です。既存の`charactor01/character.json`は同フォルダーのTXTを元に作成した初期設定です。画像から新しい特徴を推測して追加してはいません。

```json
{
  "schema_version": 1,
  "image": "character.png",
  "fields": {
    "name": "キャラクター名",
    "hair_spec": "Long black hair reaching mid-back",
    "eye_color": "Blue eyes",
    "facial_marks": "A beauty mark below the character's own LEFT eye",
    "hair_silhouette": "Long straight hair",
    "age_and_context": "Preserve apparent age from the reference",
    "fixed_features": "Preserve the reference face, hairstyle and outfit construction",
    "accessory_specs": "No invented accessories",
    "failure_modes": "Wrong hair color, missing beauty mark, mirrored beauty mark"
  }
}
```

`image`はJSONと同じフォルダーからの相対パスです。`image.png`や`character.png`など、実際のファイル名を指定できます。`name`・`hair_spec`・`eye_color`・`fixed_features`は必須です。

`fields`の値は自由記述の文字列です。複数行はJSONの`\n`で記述します。名前・髪・目・特徴・Negativeの失敗例を一度登録し、複数のシーンで再利用できます。TXTとの自動同期や書き戻しは行いません。

## シーンJSON

全項目の一覧と詳しい記載例は [シーンJSONの書き方](../presets/scenes/README.md) を参照してください。

`presets/scenes/`のJSONを選びます。`values`には画風、背景、照明、衣装ルールなど、`slots`には位置A／B／Cの配置・ポーズ・視線を保存します。

```json
{
  "schema_version": 1,
  "name": "Courtyard",
  "values": {
    "environment_description": "A quiet courtyard",
    "lighting": "Soft daylight"
  },
  "slots": {
    "a": {
      "position": "front-right, nearest camera",
      "pose": "Standing at the gate",
      "gaze": "looking toward the camera",
      "expression": "A relaxed smile"
    }
  }
}
```

- `values`は[テンプレート定義](../nodes/scene_templates.py)の`FIELD_DEFAULTS`にある共通変数を指定します。省略した値は既定値を使います。
- `slots.a/b/c`は`position`、`gaze`、`pose`、`expression`、`unique_details`、`nearby_props`、`omitted_features`を指定できます。髪や名前などキャラクターの識別特徴は上書きしません。
- 空文字の項目を含むテンプレート行は省略します。任意の装飾・小道具の指定は空にできます。
- 既定では全体人数は選択したキャラクター数です。追加人物がいるシーンでは`n_total`、`category_breakdown`、`secondary_character_group_spec`を設定してください。`n_total`も文字列（例：`"4"`）です。
- A／B／Cは場所の識別子です。Bを`None`にしてもCの場所は変わりません。画像番号だけは選択順にImage 02から連続します。1〜3人の参照キャラクターに対応します。
- テンプレートの詳細な構図固定指示、参照の対応付け、COMMON／SCENE／CHARACTERの構成は維持しています。A／B／Cすべてを使う場合のテンプレート一致はテストしています。

## 一時的なテキスト変更

通常は`scene_overrides`を`{}`のまま使います。保存済みのシーンを編集せず今回だけ変更するときは、同じ形式の一部を入力できます。この欄は複数行STRINGなので、他ノードからのテキスト接続も可能です。

```json
{
  "values": {"lighting": "Warm evening light"},
  "slots": {"a": {"expression": "A gentle smile"}}
}
```

優先順は「テンプレート既定値 → シーンJSON → scene_overrides」です。キャラクター情報は選択した`character.json`から読み込みます。

## 出力

- `positive_prompt`／`negative_prompt`：組み立て済みテキスト
- `diagnostics`：不足する追加人物説明などの診断
- `image_02`〜`image_04`：選択した参照画像。未使用出力は1×1の黒画像
- `character_count`：参照キャラクター数（追加人物は含まない）
- `character_mapping`：位置識別子、画像番号、キャラクター名、フォルダー名の対応

JSONの誤ったキーや形式、画像の欠落、同じキャラクターの重複選択はエラーになります。自然文同士の意味的な矛盾や画像生成結果は自動判定しません。


### 任意の参照ルートの例

```text
character_root = D:\CharacterReferences
character_a = character01
character_b = None
character_c = None
```

この例では、D:\CharacterReferences\character01\character.jsonを読み込みます。パスはComfyUIを実行しているPC上のものを指定します。新しい入力欄が表示されない場合は、ComfyUIを再起動してノードを追加し直してください。
