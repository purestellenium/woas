import os, sys, time

from compile import compile_game_from_file

POLL_INTERVAL_SECONDS = 0.5

def find_woas_files(path):
    if os.path.isfile(path):
        return [path] if path.endswith(".woas") else []

    found = []
    for root, _, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith(".woas"):
                found.append(os.path.join(root, filename))
    return found

def compile_and_track(filepath, mtimes):
    mtimes[filepath] = os.path.getmtime(filepath)
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] compiling {filepath}")
    compile_game_from_file(filepath)

def watch(path):
    mtimes = {}

    for filepath in find_woas_files(path):
        compile_and_track(filepath, mtimes)

    if not mtimes:
        print(f"No .woas files found at {path}")
        return

    print("Watching for changes... (Ctrl+C to stop)")

    try:
        while True:
            time.sleep(POLL_INTERVAL_SECONDS)

            for filepath in find_woas_files(path):
                if filepath not in mtimes or os.path.getmtime(filepath) != mtimes[filepath]:
                    compile_and_track(filepath, mtimes)
    except KeyboardInterrupt:
        print("\nStopped watching.")

if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)

    target = sys.argv[1].strip() if len(sys.argv) > 1 else "."

    if not os.path.exists(target):
        print(f"Error: {target} does not exist!")
    else:
        watch(target)
