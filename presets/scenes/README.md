# シーンJSONの書き方

Build Scene Promptsで使う、背景・画風・衣装・配置・ポーズなどの設定ファイルです。キャラクターを差し替えても同じ場面を使えるよう、人物の固有名や髪色ではなく、位置を表すA／B／Cで指定します。

既存のLoad Character Reference／Load Character Referencesは従来のTXTを使用します。このJSONはBuild Scene専用です。

## 作成して選択する

1. 同じフォルダーの [reference-layout.json](reference-layout.json) をコピーし、例えば`courtyard.json`として保存します。
2. 必要な項目だけ編集します。文字コードはUTF-8です。
3. ComfyUIを再起動して画面を再読み込みし、Build Sceneの`scene`でファイル名を選びます。
4. `character_root`にキャラクター参照の親フォルダーを指定し、`character_a`／`character_b`／`character_c`には、その配下にある人物フォルダー名を入力します。`character_root`が空欄なら従来の`examples/character-references/`を使います。使わない枠は`None`にします。
5. ラフ画像をImage 01として生成側へ接続し、選択した人数分の参照画像出力とPositive／Negativeを接続します。

配置先は`character-scene-tools/presets/scenes/`直下です。サブフォルダー内のJSONは一覧に出ません。選択済みファイルの内容を編集した場合は、次回実行時に読み直します。

## 基本構造

| キー | 型 | 内容 |
|---|---|---|
| `schema_version` | 整数 | 必須。現在は`1` |
| `name` | 文字列 | 任意の説明用名称。ノードの選択肢にはファイル名が表示される |
| `values` | オブジェクト | 画風、背景、照明などの全体設定。省略可能 |
| `slots` | オブジェクト | `a`／`b`／`c`ごとの位置、ポーズ、視線など。省略可能 |

この4つ以外のトップレベルキーは使用できません。

### コピーして使える1人用の例

ノードではAにキャラクターを選び、B／Cを`None`にします。人数は選択数から自動設定されるため、ここでは指定しません。

```json
{
  "schema_version": 1,
  "name": "中庭で立つ",
  "values": {
    "environment_description": "A quiet courtyard with a stone path",
    "lighting": "Soft daylight",
    "background_treatment": "Slightly blurred distant trees",
    "clothing_rule": "Each character wears the complete, opaque outfit and shoes from their own assigned reference. Preserve the outfit construction and colors.",
    "allowed_clothing": "the complete outfit and shoes from each assigned reference",
    "gaze_rule": "toward the camera",
    "gaze_violations": "Looking away from the camera"
  },
  "slots": {
    "a": {
      "position": "center of the frame, full body",
      "pose": "Standing upright with both feet on the ground and arms relaxed at the sides, matching Image 01",
      "gaze": "looking toward the camera",
      "expression": "A relaxed smile",
      "unique_details": "",
      "nearby_props": "A wooden bench behind the character",
      "omitted_features": ""
    }
  }
}
```

日本語の値も入力できます。テンプレートの固定文は英語で、入力した値をそのまま差し込みます。翻訳は行いません。

## キャラクターJSONとの役割分担

| シーンJSONに書く | キャラクターJSONに書く |
|---|---|
| 位置、ポーズ、表情、視線の方向 | 名前、髪型・髪色、目の色 |
| 背景、照明、カメラ | 顔の印、識別特徴、髪のシルエット |
| 今回の衣装ルール、持ち物とのやりとり | 固有アクセサリーの構造、特徴を保つための指示 |
| 今回だけ省略する特徴とその理由 | キャラクター固有の失敗例 |

目の色と視線は、キャラクター側の`eye_color`とシーン側の`gaze`を組み合わせます。シーンに`a_name`や`hair_spec`などの人物設定を書くことはできません。

キャラクターJSONの仕様は [Build Sceneの説明](../../docs/scene-prompt-builder.md) を参照してください。

## `slots`：位置ごとの設定

キーは小文字の`a`／`b`／`c`です。各枠で使える項目は以下の7つです。値はすべて文字列にします。

| 項目 | 内容 | 例 |
|---|---|---|
| `position` | 画面内の位置と奥行き。選択された枠では空文字不可 | `front-right, nearest camera` |
| `pose` | 体・手足・接地などの具体的な姿勢 | `Sitting on a bench with both feet on the ground` |
| `gaze` | 視線の方向 | `looking toward the camera` |
| `expression` | 表情 | `A gentle smile with the mouth closed` |
| `unique_details` | その位置の人物と物・他の枠とのやりとり | `Holding a book with both hands` |
| `nearby_props` | 近くの物と、身体に対する位置 | `A closed bag beside the right foot` |
| `omitted_features` | 今回は省略する参照画像の特徴と理由 | `The usual scarf is omitted because this scene uses a summer outfit` |

省略した項目は既定値を使います。既定の位置はAが手前右、Bが中央、Cが奥左です。1人を中央へ置く場合は、上の例のようにAの`position`を明示してください。

### 枠と画像番号の関係

枠は場面上の位置、画像番号は選択した参照画像の順番です。

| 選択する枠 | 参照画像の割り当て |
|---|---|
| Aのみ | A = Image 02 |
| A・B | A = Image 02、B = Image 03 |
| A・C | A = Image 02、C = Image 03 |
| A・B・C | A = Image 02、B = Image 03、C = Image 04 |

A・Cだけを選んだ場合も、Cの位置・ポーズは`slots.c`のままです。未選択枠の記述は出力から除外されます。全枠`None`、同じキャラクターの重複選択はエラーです。

## `values`：全体設定の全項目

必要なものだけ記述します。以下の値は、人数を含めて**すべて文字列**です。

### 画風・焦点

| 項目 | 内容 |
|---|---|
| `medium_and_finish` | 媒体・仕上がり。例：`Polished finished 2D anime illustration` |
| `linework_shading_color_rules` | 線、陰影、配色の指示 |
| `crisp_elements` | 鮮明に描く対象 |
| `softened_elements` | 少し柔らかく描く背景・前景 |
| `excluded_styles` | 除外する画風。PositiveとNegative両方へ反映 |

### 人数・識別・共通条件

| 項目 | 内容 |
|---|---|
| `n_total` | 追加人物を含む総人数。例：`"3"`。省略時は選択したキャラクター数 |
| `category_breakdown` | 総人数の内訳。省略時は選択した枠の一覧 |
| `forbidden_extras` | 追加してほしくない人物の種類 |
| `unique_feature_guard` | 特徴的な人物を重複させない追加指示 |
| `distinguishability_rule` | 人物の見分けを維持する指示 |
| `shared_category_rule` | 一部または全員に共通する条件。対象の枠を明記する |
| `secondary_character_group_spec` | 参照キャラクター以外の人物の人数・位置・服装・動作 |
| `shared_body_type_spec` | 体格・年齢感に関する共通指示 |
| `gaze_rule` | 全員に共通する視線の指示。各枠の`gaze`と揃える |

### 衣装

| 項目 | 内容 |
|---|---|
| `global_override_name` | 衣装などの上書きルール名。既定は`CLOTHING` |
| `clothing_rule` | Positive側の衣装指定。適用する枠と着用物を明示する |
| `allowed_clothing` | Negative側で参照する許可衣装。`clothing_rule`と整合させる |
| `forbidden_clothing_items` | 着用させない衣装・アクセサリー |

既定の衣装指定は普段着と靴です。参照画像の衣装を維持したい場合は、上の例または`reference-layout.json`の衣装設定を使ってください。

### 背景・カメラ

| 項目 | 内容 |
|---|---|
| `environment_description` | 場所、材質、主要な物の配置 |
| `lighting` | 光源、光の方向、色など |
| `background_treatment` | 背景の見せ方、ぼかし |
| `no_modern_items_list` | 時代設定に合わず除外したい物 |
| `pov_type` | 視点の種類 |
| `pov_alias` | 視点の補足名 |
| `angle_and_direction` | カメラの角度と向き |
| `framing_description` | 画面の切り取り、手前から奥への構成 |
| `foreground_intrusion` | 画面端に入る前景などの追加説明 |

### Negative側の条件

| 項目 | 内容 |
|---|---|
| `whose_arm` | 各手がどの腕につながるべきか。固定文`every hand must connect to …`へ挿入 |
| `shared_rule_violations` | 共通条件に対する違反 |
| `age_proportion_violations` | 避けたい年齢感・体格の変化 |
| `forbidden_prop_type` | 出してほしくない小道具 |
| `camera_violations` | 避けたい視点・構図 |
| `gaze_violations` | 避けたい視線 |
| `secondary_character_violations` | 追加人物の誤った描写 |
| `setting_violations` | 場所・時代設定に合わない描写 |

### 各セクションへの自由文追加

| 項目 | 挿入先 |
|---|---|
| `extra_common_positive` | PositiveのCOMMON末尾 |
| `extra_scene_positive` | PositiveのSCENE末尾 |
| `extra_character_positive` | PositiveのCHARACTER末尾 |
| `extra_common_negative` | NegativeのCOMMON末尾 |
| `extra_scene_negative` | NegativeのSCENE末尾 |
| `extra_character_negative` | NegativeのCHARACTER末尾 |

自由文は既存の指示へ追加されます。既存文を置き換える機能ではありません。

## 人数を固定する場合

人数を変えて再利用するシーンでは、`n_total`と`category_breakdown`を省略するのがおすすめです。明記した値は、キャラクター選択を変えても自動更新されません。

参照キャラクターA／Bの2人と、背景の店員1人を描く場合は、`values`に次のように設定します。

```json
{
  "n_total": "3",
  "category_breakdown": "two assigned characters A and B, and one adult shopkeeper",
  "secondary_character_group_spec": "One fully clothed adult shopkeeper stands behind the counter in the background. There are no other people."
}
```

これは`values`の内容の例であり、ファイル全体ではありません。店員用の参照画像は自動追加されません。ノード出力の`character_count`は参照キャラクター数なので、この例では`2`です。

総人数が選択した人数より少ない場合はエラーになります。総人数が多いのに追加人物の説明が空の場合は、`diagnostics`へ注意文が出ます。人数の内訳の自然文までは自動検証しません。

## 今回だけ変更する：`scene_overrides`

ノードの`scene_overrides`には、シーンJSONと同じ`values`／`slots`形式で変更部分だけ入力できます。通常は`{}`のままで構いません。

```json
{
  "values": {
    "lighting": "Warm evening light"
  },
  "slots": {
    "a": {
      "expression": "A cheerful smile"
    }
  }
}
```

優先順位は「テンプレート既定値 → シーンJSON → `scene_overrides`」です。各項目単位で上書きするので、この例ではAの表情だけが変わり、位置やポーズは残ります。保存済みJSONへの書き戻しは行いません。

`scene_overrides`では`schema_version`と`name`を指定しません。複数行STRING入力なので、他ノードのテキスト出力も接続できます。

## 省略・空文字・JSONの注意点

- **キーの省略**：既定値を使います。
- **空文字`""`**：その変数を含むテンプレート行を丸ごと省略します。例えば`lighting`を空にすると、同じ行にある`background_treatment`の説明も出力されません。通常は意味のある値を指定してください。
- `schema_version`のみ整数です。`values`と各`slots`の値に数値、配列、`null`、真偽値を使うとエラーになります。
- JSONにはコメントや末尾の余分なカンマを書けません。改行は文字列内で`\n`、ダブルクォートは`\"`と記述します。
- 値には完成した説明文を書きます。値の中に`{{a_name}}`などを書いても再展開されません。
- 未定義のキーはエラーになります。人数、位置、視線、衣装の説明同士が矛盾していないかは、出力したPositive／Negativeを読んで確認してください。

このJSONは詳細テンプレートへの値の指定です。構図固定、各人物1回のみ、参照画像の用途などの固定指示は維持されます。テンプレートには2Dイラスト・不透明な衣装などの前提もあるため、画風名など一項目を書き換えるだけで任意の表現へ切り替わるわけではありません。

実装上のキー・既定値は [scene_templates.py](../../nodes/scene_templates.py)、読み込み・上書き処理は [scene_prompt_builder.py](../../nodes/scene_prompt_builder.py) で確認できます。
