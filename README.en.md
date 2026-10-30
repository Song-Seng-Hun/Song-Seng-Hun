<p align="center"><a href="README.md">한국어</a> · <b>English</b> · <a href="README.ja.md">日本語</a></p>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/worldmap-dark.svg">
  <img src="assets/worldmap-light.svg" width="100%" alt="Pixel-art world map: a traveler sets out from the physics lab, passes the robot workshop and the vision data factory; Claude joins at the sense lab, and Codex and Gemini at the AI team HQ; then the four head together towards a fog-covered game village.">
</picture>

<h3 align="center">I put together a team of AIs to build tools, and now I'm making a game with that team</h3>
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

- **Running an AI team** · I run a workspace where Claude, Codex and Gemini share memory and work together. I design the team's roles and rules, set the direction and review the results.
- **Giving AI eyes and ears** · With the team, I build analysis tools that turn the scenes and motion in video, and the beat, chords and lyrics in music, into something AI can read.
- **A small game** · The first game I'm making with this team. When it's finished, the fog on the map lifts.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/header-quest-log-dark.svg">
  <img src="assets/header-quest-log-light.svg" alt="Quest log">
</picture>

<details>
<summary><b>01 Physics Lab</b> · BSc in physics, left a master's program in quantum optics</summary>

In graduate school I studied temperature sensing with NV-center diamond through simulation.

</details>

<details>
<summary><b>02 Robot Workshop</b> · Robot integration and bring-up, under a year</summary>

- Sent movement commands from an external system to a ROS-based AMR over sockets
- Tested gRPC communication for robot-arm control and connected the robot arm's camera feed
- Before the hardware arrived, simulated FK/IK in Qt and tested PID drive on a Pico
- Chained voice commands through STT → LLM → ROS to move the robot
- [dobot](https://github.com/Song-Seng-Hun/dobot) · A robot-arm project that recognizes block colors and shapes with YOLO
- [my_custom_stt_train](https://github.com/Song-Seng-Hun/my_custom_stt_train) · A training setup for Korean speech recognition (KoSpeech)

</details>

<details>
<summary><b>03 Vision Data Factory</b> · Training and running image classification models, about 2 years</summary>

- Trained EfficientNet-based classifiers on customer data and analyzed misclassified samples
- Ran repeated rounds of data review and cleaning, and split the work among the reviewers
- A Streamlit review tool, and a Label Studio prototype for model-assisted labeling (Jetson inference server + FastAPI)
- A labeling pipeline that uses YOLO predictions as first-pass labels
- What I learned: in the data I worked with, checking the samples and the shooting conditions mattered as much as the model architecture.

</details>

<details>
<summary><b>04 Sense Lab</b> · Eyes and ears for AI</summary>

Tools that sort video into scene changes and motion, and music into beat, chords and lyrics, as reports AI can read. Both are being refined by testing them on real videos and songs. (private)

</details>

<details>
<summary><b>05 AI Team HQ</b> · A workspace where several AIs work together</summary>

With shared memory documents and work logs, Claude, Codex and Gemini split the roles and work together. I design those roles and the working rules, and review the results. (private)

</details>

<details>
<summary><b>06 Game Village</b> · In progress</summary>

A small game I'm making with the AI team. *To be continued.*

</details>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/header-inventory-dark.svg">
  <img src="assets/header-inventory-light.svg" alt="Inventory">
</picture>

| Area | Used |
|---|---|
| Vision and data | PyTorch · EfficientNet · YOLO · OpenCV · Streamlit · Label Studio · FastAPI |
| Robotics | ROS · ROS2 · gRPC · Qt · Raspberry Pi Pico |
| Languages | Python · C++ · C |
| AI collaboration | Claude Code · Codex · Gemini |

I make drawings, motion and music myself, so I can judge and fix the assets AI makes.
<!-- creative GIF: add when the user picks one of their own animated illustrations -->

<sub>The map and the pixel titles were drawn by Claude ([tools/build_worldmap.py](tools/build_worldmap.py)).</sub>
