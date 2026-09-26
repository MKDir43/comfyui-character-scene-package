# Qwen Image Edit Character Replacement Workflow

![ComfyUI Screenshot](./screenshot.png)

## 概要

ComfyUI + Qwen Image Editを使用し、ラフ画像のポーズ・構図を維持しながら、キャラクターシートのデザインへ置き換えるワークフロー。

基本的な役割は以下。

- Image 01 = WHERE / HOW（ポーズ・構図）
- Image 02+ = WHO（キャラクターデザイン）
- SCENE = WHAT IS HAPPENING（動作・状況・表情）

## Reference Image

### Image 01: Rough Reference

Image 01はポーズ・構図の参照画像として使用する。

参照する情報:
- ポーズ・重心
- キャラクター配置
- カメラアングル・パース・foreshortening
- 前後関係・オーバーラップ
- キャラクター同士の位置・接触関係

顔、髪型、服装などのキャラクターデザインは継承しない。

棒人間、人体マネキン、手描きラフなどを使用できる。強いパースやforeshorteningが必要な場合はラフにも明確に反映する。

### Image 02+: Character Reference

Image 02以降はキャラクターデザインの参照画像。

| Reference | Character |
|---|---|
| Image 01 | Rough |
| Image 02 | Character A |
| Image 03 | Character B |
| Image 04 | Character C |
| ... | ... |

顔、年齢感、体格、髪型、服装、色、アクセサリーなどはCharacter Referenceを基準とする。

## Prompt Structure

Positive / Negativeともに以下の3層で管理する。

1. COMMON — 全生成共通のルール
2. SCENE — 人物割り当て、動作、状況、表情
3. CHARACTER — キャラクター固有の特徴・制約

結合順:

`COMMON → SCENE → CHARACTER`

同じ指示を複数の層に重複して記載しない。

## Character Package

1キャラクターを1Packageとして管理する。

```text
<root>/
├─ character_01/
│  ├─ image.png
│  ├─ positive.txt
│  └─ negative.txt
├─ character_02/
│  ├─ image.png
│  ├─ positive.txt
│  └─ negative.txt
└─ ...
```

- `image.png` — Character Reference
- `positive.txt` — キャラクター固有の特徴
- `negative.txt` — キャラクター固有の禁止事項・既知の失敗対策

`positive.txt` / `negative.txt`にはCharacter A/B/Cなどの割り当てを記載しない。割り当てはMulti Prompt Package Loaderが行う。

## Multi Prompt Package Loader

選択されたPackageからCharacter ReferenceとPromptを読み込む。

`None`のスロットは除外し、有効なPackageを上から連続して割り当てる。

例:

```text
package_1 = character_01
package_2 = None
package_3 = character_07
package_4 = character_12
```

割り当て:

```text
character_01 → Character A → Image 02
character_07 → Character B → Image 03
character_12 → Character C → Image 04
```

Package Slot NumberとCharacter番号は一致しない。Image 01は常にRoughのため、1番目の有効PackageはImage 02から開始する。

## Prompt Assembly

ComfyUIの「テキスト整形」ノードでPositive / Negativeをそれぞれ結合する。

```text
[COMMON]
{a}

[SCENE]
{b}

[CHARACTER]
{c}
```

入力:

```text
a = COMMON
b = SCENE
c = CHARACTER
```

## Prompt Tuning

Promptは必要以上に長くせず、実際に発生した失敗に対して必要最小限の指示を追加する。

- 全シーンで発生する問題 → COMMON
- 特定シーンだけの問題 → SCENE
- 特定キャラクターだけの問題 → CHARACTER

Negative PromptもPositive Promptの反対語を列挙するのではなく、実際の失敗防止を中心に記述する。