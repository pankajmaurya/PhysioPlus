# Computer vision based exercise tracker
- Uses mediapipe and opencv-python
- Use python 3.10.18
- Why? https://www.python.org/downloads/release/python-31018/ is last release of 3.10 as of Aug 2025
- Will be supported till Oct 2026
- https://ai.google.dev/edge/mediapipe/solutions/setup_python says we can use upto 3.12 now, so I will soon upgrade 

# publish new version
```sh
PhysioPlus/physiocore $ pip install -e .
pip install build
rm -rf dist build src/physiocore.egg-info
python -m build
pip install twine
twine upload --repository testpypi dist/*
twine upload dist/*
```

## Development Installation

To install this package in editable mode for development:

```bash
pip install -e .
```

**What this does:**
- Installs the package by linking to the source code (rather than copying files)
- Changes to the source code are immediately available without reinstalling
- Perfect for active development and testing

**Requirements:**
- Package must have `setup.py`, `setup.cfg`, or `pyproject.toml`
- Use this when you're modifying the code frequently

**Alternative installations:**
```bash
pip install -e /path/to/package     # Install from different directory
pip install .                      # Regular installation (copies files)
pip install -e git+https://github.com/username/repo.git  # Install from GitHub in editable mode
pip install -e git+https://github.com/username/repo.git@branch-name  # Install specific branch
```

# installation
```sh
pip install physiocore
```

Only if we are trying to install from testpypi (bleeding edge releases will be done here)
```sh
python3.10 -m venv testinstall-0.2.2  ; source testinstall-0.2.2/bin/activate
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple physiocore
```

# upgrade from existing installation
```sh
pip install -U physiocore==0.3.0
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple physiocore==0.2.4
```

# Versioning
- last testing on Ankle toe movement done on Mac Sequoia 15.6, physiocore==0.2.2

# Usage Guide
```py
from physiocore.ankle_toe_movement import AnkleToeMovementTracker
tracker = AnkleToeMovementTracker()
tracker.start()

from physiocore.cobra_stretch import CobraStretchTracker
tracker = CobraStretchTracker()
tracker.start()

from physiocore.bridging import BridgingTracker
tracker = BridgingTracker()
tracker.start()

#Similar imports for Straight leg raise and prone straight leg raise
from physiocore.any_prone_straight_leg_raise import AnyProneSLRTracker

from physiocore.any_straight_leg_raise import AnySLRTracker
```
# Testing, Usage 
```
python demo.py --save_video bridging.avi --debug

Contents of demo.py below:
from physiocore.bridging import BridgingTracker
tracker = BridgingTracker()
tracker.start()


(testinstall-0.2.2) ➜  TestPhysioPlus python demo.py
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1754933487.157762 3414708 gl_context.cc:369] GL version: 2.1 (2.1 Metal - 89.4), renderer: Apple M4 Pro
Downloading model to /Users/pankaj/TechCareer/TestPhysioPlus/testinstall-0.2.2/lib/python3.10/site-packages/mediapipe/modules/pose_landmark/pose_landmark_heavy.tflite
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
W0000 00:00:1754933487.193762 3415496 inference_feedback_manager.cc:114] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
W0000 00:00:1754933487.201640 3415498 inference_feedback_manager.cc:114] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
I0000 00:00:1754933491.431292 3414708 gl_context.cc:369] GL version: 2.1 (2.1 Metal - 89.4), renderer: Apple M4 Pro
Settings are --debug False, --video None, --render_all False --save_video None --lenient_mode True --fps 30
W0000 00:00:1754933491.482758 3415548 inference_feedback_manager.cc:114] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
W0000 00:00:1754933491.508220 3415557 inference_feedback_manager.cc:114] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
W0000 00:00:1754933539.888523 3415552 landmark_projection_calculator.cc:186] Using NORM_RECT without IMAGE_DIMENSIONS is only supported for the square ROI. Provide IMAGE_DIMENSIONS or use PROJECTION_MATRIX.
time for raise 1754933545.1654909
time for raise 1754933546.743605
time for raise 1754933562.706252
time for raise 1754933565.942921
time for raise 1754933567.60865
time for raise 1754933574.3253388
time for raise 1754933575.041138
time for raise 1754933575.435921
time for raise 1754933576.240452
time for raise 1754933576.639755
time for raise 1754933603.21583
time for raise 1754933628.344631
time for raise 1754933629.984603
time for raise 1754933630.3845131
Final count: 3
```

See demo.py in tests
