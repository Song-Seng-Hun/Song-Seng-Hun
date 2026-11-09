<p align="center"><b>한국어</b> · <a href="docs/README.en.md">English</a> · <a href="docs/README.ja.md">日本語</a></p>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/worldmap-dark.svg">
  <img src="assets/worldmap-light.svg" width="100%" alt="픽셀아트 월드맵. 여행자가 물리 연구소에서 출발해 로봇 공방과 비전 데이터 공장을 지나고, 감각 연구소에서 Claude가, AI 팀 본부에서 Codex와 Gemini가 합류해 넷이 함께 안개 낀 게임 마을로 향합니다.">
</picture>

<h3 align="center">AI 팀을 꾸려 도구를 만들고, 그 팀과 함께 게임을 만들고 있습니다</h3>
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

- **AI 팀 운영** · Claude, Codex, Gemini가 기억을 나누며 함께 일하는 작업 환경을 운영합니다. 팀의 역할과 규칙을 설계하고, 방향을 정하고 결과를 검토합니다.
- **AI에게 눈과 귀 달아 주기** · 영상의 장면과 움직임, 음악의 박자와 코드와 가사를 AI가 읽을 수 있게 바꿔 주는 분석 도구를 팀과 함께 만듭니다.
- **작은 게임** · 이 팀과 함께 만드는 첫 게임입니다. 완성되면 지도의 안개가 걷힙니다.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/header-quest-log-dark.svg">
  <img src="assets/header-quest-log-light.svg" alt="Quest log">
</picture>

<details>
<summary><b>01 물리 연구소</b> · 물리학 학사, 양자광학 석사 과정 중단</summary>

대학원에서 NV센터 다이아몬드를 이용한 온도 센싱을 시뮬레이션으로 연구했습니다.

</details>

<details>
<summary><b>02 로봇 공방</b> · 로봇 연동과 초기 구동, 1년 미만</summary>

- ROS 기반 AMR에 외부 시스템의 이동 명령을 소켓으로 전달
- 로봇팔 제어용 gRPC 통신 시험, 로봇팔 카메라 영상 연결
- 장비가 오기 전 Qt로 FK/IK 시뮬레이션, Pico에서 PID 구동 시험
- 음성 명령을 STT → LLM → ROS로 이어 로봇을 움직이는 연동
- [dobot](https://github.com/Song-Seng-Hun/dobot) · YOLO로 블록의 색과 모양을 인식하는 로봇팔 프로젝트
- [my_custom_stt_train](https://github.com/Song-Seng-Hun/my_custom_stt_train) · 한국어 음성인식(KoSpeech) 학습 환경

</details>

<details>
<summary><b>03 비전 데이터 공장</b> · 이미지 분류 모델 학습과 운영, 약 2년</summary>

- EfficientNet 기반 분류 모델을 고객 데이터에 맞춰 학습하고 오분류 샘플 분석
- 데이터 검수와 정제를 반복 진행하고, 검수 인력에게 작업을 나눠 전달
- Streamlit 검수 도구, Label Studio 모델 보조 라벨링 프로토타입(Jetson 추론 서버 + FastAPI)
- YOLO 예측을 초벌 라벨로 쓰는 라벨링 파이프라인
- 배운 점: 제가 다룬 데이터에서는 모델 구조만큼 샘플 상태와 촬영 조건을 살피는 일이 중요했습니다.

</details>

<details>
<summary><b>04 감각 연구소</b> · AI의 눈과 귀</summary>

**[LLM Video Lens](https://github.com/Song-Seng-Hun/llm_video_lens)** · AI가 영상 속 움직임을 읽게 해 주는 CLI 도구 (공개)

- 샷마다 몸·팔다리·카메라가 어느 방향으로 얼마나, 어떤 완급으로 움직였는지 글로 적고, 궤적을 겹쳐 그린 어니언 그림을 함께 만듭니다.
- 확실하지 않은 곳은 지어내지 않고 "모름"으로 남기며, 모든 내용을 원본 프레임 번호로 되짚을 수 있습니다.
- 사람 수를 먼저 훑어보고(`crowd`) 여러 명을 따로 추적합니다. 결과는 그림으로 점 위치를 먼저 확인한 뒤 읽도록 안내합니다.

**[LLM Music Lens](https://github.com/Song-Seng-Hun/llm_music_lens)** · AI가 근거를 들어 음악을 읽게 해 주는 분석 도구 (공개)

- AI 에이전트는 대부분 소리를 듣지 못해서, "이 곡 느낌으로 작곡해 줘" 같은 부탁을 받으면 제목이나 장르로 짐작합니다. 그 빈칸을 채우려고 만들었습니다.
- 곡을 넣으면 BPM과 박, 코드와 조성, 섹션, 멜로디·베이스·드럼 음표, 가사 단어의 타이밍을 시간과 함께 텍스트 악보로 정리합니다.
- 결과는 피아노 롤 그림과, 한쪽 귀에는 원음을 다른 쪽 귀에는 결과를 들려주는 확인용 소리로 원음과 맞춰 볼 수 있습니다.

</details>

<details>
<summary><b>05 AI 팀 본부</b> · 여러 AI가 함께 일하는 작업 환경</summary>

공유 기억 문서와 작업 일지를 두고 Claude, Codex, Gemini가 역할을 나눠 일합니다. 저는 그 역할과 작업 규칙을 설계하고 결과를 검토합니다. (비공개)

</details>

<details>
<summary><b>06 게임 마을</b> · 제작 중</summary>

AI 팀과 함께 만드는 작은 게임입니다. *To be continued.*

</details>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/header-inventory-dark.svg">
  <img src="assets/header-inventory-light.svg" alt="Inventory">
</picture>

| 분야 | 써 본 것 |
|---|---|
| 비전과 데이터 | PyTorch · YOLO · OpenCV · Streamlit · Label Studio · FastAPI |
| 로봇 | ROS · ROS2 · gRPC · Qt · Raspberry Pi Pico |
| 언어 | Python |
| AI 협업 | Claude Code · Codex · Gemini |

그림·모션·음악을 직접 만들어, AI가 만든 애셋을 판단하고 고칩니다.
<!-- creative GIF: add when the user picks one of their own animated illustrations -->

<sub>지도와 픽셀 제목은 Claude가 그렸습니다 ([tools/build_worldmap.py](tools/build_worldmap.py)).</sub>
