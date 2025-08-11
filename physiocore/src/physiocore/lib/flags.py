import sys


# TODO: Deduplicate code with parse_flags
def parse_more_flags():
    # Check debug mode
    debug = False
    # Poor man's way to specify video file
    video = None
    render_all = False
    save_video = None
    lenient_mode = True
    fps = 30
    out_fps = 30

    # Parsing command line flags, consider upgrade to argparse.
    if len(sys.argv) > 1:
        print("Arguments len is ", len(sys.argv))
        for index in range(1, len(sys.argv)):
            print("Argument ", index, " is ", sys.argv[index])
            if sys.argv[index] == '--debug':
                debug = True
            elif sys.argv[index] == '--video':
                video = sys.argv[index + 1]
            elif sys.argv[index] == '--render_all':
                render_all = True
            elif sys.argv[index] == '--save_video':
                save_video = sys.argv[index + 1]
            elif sys.argv[index] == '--lenient_mode':
                lenient_mode  = False
            elif sys.argv[index] == '--fps':
                fps = int(sys.argv[index + 1])
            elif sys.argv[index] == '--out_fps':
                out_fps = int(sys.argv[index + 1])

    print(f"Settings are --debug {debug}, --video {video}, --render_all {render_all} --save_video {save_video} --lenient_mode {lenient_mode} --fps {fps} --out_fps {out_fps}")

    return debug, video, render_all, save_video , lenient_mode, fps, out_fps

# TODO: Upgrade all usages to parse_more_flags
def parse_flags():
    # Default values
    debug = False
    video = None
    render_all = False
    save_video = None
    lenient_mode = True
    fps = 30

    # Parsing command line flags, consider upgrade to argparse.
    if len(sys.argv) > 1:
        print("Arguments len is ", len(sys.argv))
        index = 1
        while index < len(sys.argv):
            print("Argument ", index, " is ", sys.argv[index])
            if sys.argv[index] == '--debug':
                debug = True
                index += 1
            elif sys.argv[index] == '--video':
                if index + 1 < len(sys.argv):
                    video = sys.argv[index + 1]
                    index += 2
                else:
                    print("Warning: --video flag needs a value")
                    index += 1
            elif sys.argv[index] == '--render_all':
                render_all = True
                index += 1
            elif sys.argv[index] == '--save_video':
                if index + 1 < len(sys.argv):
                    save_video = sys.argv[index + 1]
                    index += 2
                else:
                    print("Warning: --save_video flag needs a value")
                    index += 1
            elif sys.argv[index] == '--lenient_mode':
                lenient_mode  = False if sys.argv[index + 1] == "False" else True
                index += 2
            else:
                print(f"Warning: found unrecognized flag!!! {sys.argv[index]}")
                index += 1

    print(f"Settings are --debug {debug}, --video {video}, --render_all {render_all} --save_video {save_video} --lenient_mode {lenient_mode} --fps {fps}")

    return debug, video, render_all, save_video , lenient_mode

# TODO: Upgrade all usages to parse_more_flags
def parse_cobra_flags():
    # Default values
    debug = False
    video = None
    render_all = False
    save_video = None
    more_cobra_checks = False
    fps = 30

    # Parsing command line flags, consider upgrade to argparse.
    if len(sys.argv) > 1:
        print("Arguments len is ", len(sys.argv))
        index = 1
        while index < len(sys.argv):
            print("Argument ", index, " is ", sys.argv[index])
            if sys.argv[index] == '--debug':
                debug = True
                index += 1
            elif sys.argv[index] == '--video':
                if index + 1 < len(sys.argv):
                    video = sys.argv[index + 1]
                    index += 2
                else:
                    print("Warning: --video flag needs a value")
                    index += 1
            elif sys.argv[index] == '--render_all':
                render_all = True
                index += 1
            elif sys.argv[index] == '--save_video':
                if index + 1 < len(sys.argv):
                    save_video = sys.argv[index + 1]
                    index += 2
                else:
                    print("Warning: --save_video flag needs a value")
                    index += 1
            elif sys.argv[index] == '--more_cobra_checks':
                more_cobra_checks  = True
                index += 1
            else:
                print(f"Warning: found unrecognized flag!!! {sys.argv[index]}")
                index += 1

    print(f"Settings are --debug {debug}, --video {video}, --render_all {render_all} --save_video {save_video} --more_cobra_checks {more_cobra_checks} --fps {fps}")

    return debug, video, render_all, save_video , more_cobra_checks  