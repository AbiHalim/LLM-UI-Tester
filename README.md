# Team Asbujawa TikTok Tech Jam 2025

![Architecture Diagram](<img/Asbujawa TikTok Tech jam.jpg>)

## Requirements (Taken from android_world repo)

1. Set up the Android Emulator
   1. Download Android Studio [here](https://developer.android.com/studio?gad_source=1&gclid=Cj0KCQjw3ZayBhDRARIsAPWzx8oLcadBD0vAq8xmUutaunLGSzhgEtLz4xVZ_SpV4G0xJazS7LxQkDsaAuveEALw_wcB&gclsrc=aw.ds)
   2. Create an Android Virtual Device (AVD) by following these instructions. For hardware select **Pixel 6**, for System Image select **Tiramisu, API Level 33**, and choose AVD name as **AndroidWorldAvd**. [Watch the setup video.](https://github.com/google-research/android_world/assets/162379927/efc33980-8b36-44be-bb2b-a92d4c334a50)

1. Launch the Android Emulator from the command line

    Launch the emulator from the command line, not using the Android Studio UI,
    with the `-grpc 8554` flag which is needed communication with accessibility
    forwarding app.

    ```bash
    # Typically it's located in ~/Android/Sdk/emulator/emulator or
    # ~/Library/Android/sdk/emulator/emulator
    EMULATOR_NAME=AndroidWorldAvd # From previous step
    ~/Library/Android/sdk/emulator/emulator -avd $EMULATOR_NAME -no-snapshot -grpc 8554
    ```

1. Install AndroidWorld. *Note: Python 3.11 is required.*

    ```python
    git clone https://github.com/google-research/android_world.git
    cd ./android_world
    pip install -r requirements.txt
    python setup.py install
    ```

1. Enter venv3.11 and nstall package dependencies

    ```bash
    # inside venv3.11
    pip install requirements.txt
    ```

1. Install `ffmpeg`, if not already installed.

    ```bash
    # Linux (Ubuntu/Debian)
    # sudo apt update && sudo apt install ffmpeg

    # macOS
    brew install ffmpeg
    ```


1. Add model provider APIs as environment variables in .env

    ```bash
    # Add to .env
    export OPENAI_API_KEY=your-key
    export GCP_API_KEY=your-key
    ```


## Installation

**This repository makes heavy use of Google Deepmind's
[android_world](https://github.com/google-research/android_world)**

It is treated as a git submodule, as such, in order to **clone** this project,
one must run :

```git
git submodule update --init --recursive 
```

to initialize and fetch the submodule's contents


## Quickstart

Run the `minimal_task_runner.py` script inside android_world to see the basic
mechanics of AndroidWorld components. It initializes the environment, sets up a
task, and currently runs the default agent, M3A, on it.
```bash
python minimal_task_runner.py --task=ContactsAddContact
```
Current development is being made on a new agent

## Citation

This repository is heavily dependant on the contributions of this paper:

```
@misc{rawles2024androidworlddynamicbenchmarkingenvironment,
      title={AndroidWorld: A Dynamic Benchmarking Environment for Autonomous Agents},
      author={Christopher Rawles and Sarah Clinckemaillie and Yifan Chang and Jonathan Waltz and Gabrielle Lau and Marybeth Fair and Alice Li and William Bishop and Wei Li and Folawiyo Campbell-Ajala and Daniel Toyama and Robert Berry and Divya Tyamagundlu and Timothy Lillicrap and Oriana Riva},
      year={2024},
      eprint={2405.14573},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2405.14573},
}
```
