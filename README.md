# PhysioCore — Computer Vision Based Exercise Tracker

PhysioCore is a Python package for tracking physical therapy and fitness exercises using **MediaPipe** and **OpenCV**. It provides real-time tracking for exercises like ankle-toe movement, cobra stretch, bridging, and straight leg raises.

## Features

- **Computer vision-based tracking** for multiple physiotherapy exercises
- Built with [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/setup_python) and [OpenCV](https://opencv.org/)
- Real-time exercise counting and form analysis
- Support for multiple exercise types with extensible tracker architecture
- Cross-platform compatibility

## Requirements

- **Python 3.10.18** (recommended)
  - Last release of Python 3.10 as of August 2025
  - Supported until October 2026
  - MediaPipe supports up to Python 3.12, upgrade planned soon

## Installation

### Stable Release (PyPI)

```sh
pip install physiocore
```

### Development Release (TestPyPI)

For bleeding-edge features and testing:

```sh
python3.10 -m venv testinstall-0.2.2
source testinstall-0.2.2/bin/activate
pip install --index-url https://test.pypi.org/simple/ \
           --extra-index-url https://pypi.org/simple physiocore
```

### Upgrade Existing Installation

```sh
pip install --index-url https://test.pypi.org/simple/ \
           --extra-index-url https://pypi.org/simple physiocore==0.2.4
```

## Quick Start

### 📺 Video Demos

Watch our [YouTube demo playlist](https://www.youtube.com/watch?v=VtKXyhypv7E&list=PL7eJwmV22aNAKIna10t7gCtlGDB4jcrvG) to see PhysioCore in action with real exercise tracking examples.

### Basic Usage

```python
from physiocore.ankle_toe_movement import AnkleToeMovementTracker

tracker = AnkleToeMovementTracker()
tracker.start()
```

### Available Trackers

```python
# Ankle Toe Movement
from physiocore.ankle_toe_movement import AnkleToeMovementTracker
tracker = AnkleToeMovementTracker()
tracker.start()

# Cobra Stretch
from physiocore.cobra_stretch import CobraStretchTracker
tracker = CobraStretchTracker()
tracker.start()

# Bridging Exercise
from physiocore.bridging import BridgingTracker
tracker = BridgingTracker()
tracker.start()

# Straight Leg Raises
from physiocore.any_straight_leg_raise import AnySLRTracker
from physiocore.any_prone_straight_leg_raise import AnyProneSLRTracker
```

## Demo & Testing

Create a demo file (`demo.py`):

```python
from physiocore.bridging import BridgingTracker

tracker = BridgingTracker()
tracker.start()
```

Run with options:

```sh
python demo.py --save_video bridging.avi --debug
```

### Command Line Options

- `--debug`: Enable debug mode for detailed logging
- `--save_video <filename>`: Save tracking session to video file
- `--render_all`: Render all tracking visualizations
- `--lenient_mode`: Enable lenient tracking mode
- `--fps <number>`: Set frames per second (default: 30)

### Sample Output

```
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1754933487.157762 3414708 gl_context.cc:369] GL version: 2.1 (2.1 Metal - 89.4), renderer: Apple M4 Pro
Downloading model to .../pose_landmark_heavy.tflite
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
Settings are --debug False, --video None, --render_all False --save_video None --lenient_mode True --fps 30

time for raise 1754933545.1654909
time for raise 1754933546.743605
time for raise 1754933562.706252
Final count: 3
```

## Development
### Unit tests

```sh
python -m unittest discover physiocore/tests
```

### Publishing New Version

```sh
rm -rf dist build src/physiocore.egg-info
python -m build
twine upload --repository testpypi dist/*
```

### Version History

- **v0.2.2**: Last tested Ankle Toe Movement on macOS Sequoia 15.6
- **v0.2.4**: Current development version

## Platform Support

- **Tested on**: macOS Sequoia 15.6 with Apple M4 Pro
- **Supported**: Windows, macOS, Linux
- **Requirements**: Python 3.10+ with webcam access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new exercise trackers
4. Submit a pull request

## License

This project is licensed under the **Apache License 2.0** — see LICENSE for details.

## Support

For issues, feature requests, or questions:
- Create an issue on the GitHub repository
- Check the documentation for troubleshooting
- Ensure your camera permissions are enabled

---

**Made with ❤️ for physiotherapy and fitness tracking**
