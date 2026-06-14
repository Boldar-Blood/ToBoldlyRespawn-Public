import sys
import argparse
from panda3d.core import loadPrcFileData


def main():
    parser = argparse.ArgumentParser(description="To Boldly Respawn - A Co-Op Space Disaster")
    parser.add_argument("--headless", action="store_true", help="Run in windowless/headless mode for automated dry-runs and tests.")
    args = parser.parse_args()

    if args.headless:
        print("[System] Initializing in headless mode...")
        loadPrcFileData("", "window-type none")
        loadPrcFileData("", "audio-active #f")
        loadPrcFileData("", "notify-level-glgsg fatal")
        loadPrcFileData("", "notify-level-windisplay fatal")

    # Import and run the app after loading configuration data
    try:
        from space_demo.core.procedural_audio import generate_all_audio
        generate_all_audio()

        from space_demo.app import SpaceDisasterApp
        app = SpaceDisasterApp(headless=args.headless)
        if args.headless:
            print("[System] Headless bootstrap successful. Running single tick dry-run...")
            # Tick the simulation once to verify bootstrap stability
            app.step_simulation(0.016)
            print("[System] Headless dry-run completed successfully.")
            sys.exit(0)
        else:
            app.run()
    except Exception as e:
        print(f"[Error] Application failed to launch: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
