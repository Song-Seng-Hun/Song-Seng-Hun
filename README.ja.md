<p align="center"><a href="README.md">한국어</a> · <a href="README.en.md">English</a> · <b>日本語</b></p>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/worldmap-dark.svg">
  <img src="assets/worldmap-light.svg" width="100%" alt="ピクセルアートの世界地図。旅人が物理研究所を出発し、ロボット工房とビジョンデータ工場を通り過ぎ、感覚研究所で Claude が、AI チーム本部で Codex と Gemini が仲間に加わって、4 人で霧に包まれたゲームの村へ向かいます。">
</picture>

<h3 align="center">AI のチームを組んでツールを作り、そのチームと一緒にゲームを作っています</h3>
<p align="center"><sub>From physics through robots and vision AI — now running a team of AI agents and building a small game with it.</sub></p>

<p align="center">
  <a href="https://hilarious-muscari-8df.notion.site/Seunghun-Song-Portfolio-408f183740be81629c70e01092be4962">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/button-portfolio-dark.svg">
      <img src="assets/button-portfolio-light.svg" alt="Portfolio (Notion)">
    </picture>
  </a>
</p>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/header-current-quest-dark.svg">
  <img src="assets/header-current-quest-light.svg" alt="Current quest">
</picture>

- **AI チームの運営** · Claude、Codex、Gemini が記憶を共有しながら一緒に働く作業環境を運営しています。チームの役割とルールを設計し、方向を決めて結果をレビューします。
- **AI に目と耳を付ける** · 映像のシーンと動き、音楽のリズム・コード・歌詞を AI が読める形に変える分析ツールを、チームと一緒に作っています。
- **小さなゲーム** · このチームと一緒に作る最初のゲームです。完成すると地図の霧が晴れます。

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/header-quest-log-dark.svg">
  <img src="assets/header-quest-log-light.svg" alt="Quest log">
</picture>

<details>
<summary><b>01 物理研究所</b> · 物理学の学士、量子光学の修士課程を中退</summary>

大学院で、NV センター・ダイヤモンドを使った温度センシングをシミュレーションで研究しました。

</details>

<details>
<summary><b>02 ロボット工房</b> · ロボットの連携と初期立ち上げ、1 年未満</summary>

- ROS ベースの AMR に、外部システムからの移動命令をソケットで伝達
- ロボットアーム制御用の gRPC 通信を試験し、ロボットアームのカメラ映像を接続
- 機材が届く前に Qt で FK/IK をシミュレーションし、Pico で PID 駆動を試験
- 音声命令を STT → LLM → ROS とつないでロボットを動かす連携
- [dobot](https://github.com/Song-Seng-Hun/dobot) · YOLO でブロックの色と形を認識するロボットアームのプロジェクト
- [my_custom_stt_train](https://github.com/Song-Seng-Hun/my_custom_stt_train) · 韓国語音声認識（KoSpeech）の学習環境

</details>

<details>
<summary><b>03 ビジョンデータ工場</b> · 画像分類モデルの学習と運用、約 2 年</summary>

- EfficientNet ベースの分類モデルを顧客データに合わせて学習し、誤分類サンプルを分析
- データの検品と整理を繰り返し、検品スタッフに作業を分けて依頼
- Streamlit の検品ツール、Label Studio のモデル補助ラベリングのプロトタイプ（Jetson 推論サーバー + FastAPI）
- YOLO の予測を下書きラベルとして使うラベリング・パイプライン
- 学んだこと：私が扱ったデータでは、モデルの構造と同じくらい、サンプルの状態と撮影条件を確認することが大切でした。

</details>

<details>
<summary><b>04 感覚研究所</b> · AI の目と耳</summary>

映像はシーンの切り替わりと動きに、音楽はリズム・コード・歌詞に整理して、AI が読めるレポートを作るツールです。どちらも実際の映像と曲で検証しながら改良を続けています。（非公開）

</details>

<details>
<summary><b>05 AI チーム本部</b> · 複数の AI が一緒に働く作業環境</summary>

共有の記憶文書と作業日誌を置き、Claude、Codex、Gemini が役割を分担して働きます。私はその役割と作業ルールを設計し、結果をレビューします。（非公開）

</details>

<details>
<summary><b>06 ゲームの村</b> · 制作中</summary>

AI チームと一緒に作っている小さなゲームです。*To be continued.*

</details>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/header-inventory-dark.svg">
  <img src="assets/header-inventory-light.svg" alt="Inventory">
</picture>

| 分野 | 使ったもの |
|---|---|
| ビジョンとデータ | PyTorch · EfficientNet · YOLO · OpenCV · Streamlit · Label Studio · FastAPI |
| ロボット | ROS · ROS2 · gRPC · Qt · Raspberry Pi Pico |
| 言語 | Python · C++ · C |
| AI との協業 | Claude Code · Codex · Gemini |

絵・モーション・音楽を自分で作っているので、AI が作ったアセットを判断して直せます。
<!-- creative GIF: add when the user picks one of their own animated illustrations -->

<sub>地図とピクセルのタイトルは Claude が描きました（[tools/build_worldmap.py](tools/build_worldmap.py)）。</sub>
