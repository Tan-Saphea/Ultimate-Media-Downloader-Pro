import os
import subprocess
import sys

def main():
    print("=" * 60)
    print(" Ultimate Media Downloader Pro - Cross-Platform Build ")
    print("=" * 60)
    
    current_os = sys.platform
    print(f"Detected Operating System: {current_os}")

    # 1. Check dependencies and install if missing
    print("\n[1/3] Checking required tools...")
    try:
        import PyInstaller
        print("✅ PyInstaller is found.")
    except ImportError:
        print("⚠️ PyInstaller not found. Automatically installing it now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed successfully.")

    try:
        import yt_dlp
        import PyQt5
    except ImportError:
        print("⚠️ Missing application dependencies. Installing PyQt5 and yt-dlp...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5", "yt-dlp"])

    # 2. Prepare the PyInstaller command
    print("\n[2/3] Preparing PyInstaller command...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--onefile",
        "--name", "UltimateMediaDownloader",
        "--hidden-import", "yt_dlp",
        "--hidden-import", "PyQt5",
    ]

    # Handle assets safely: Windows separator is ';', Mac/Linux is ':'
    sep = ";" if current_os == "win32" else ":"
    
    # Bundle critical UI data
    assets = ["me.jpg", "settings.json", "history.json"]
    for asset in assets:
        # Create empty files if they temporarily don't exist for the build
        if not os.path.exists(asset) and asset.endswith('.json'):
            with open(asset, 'w') as f:
                f.write('{}' if asset == 'settings.json' else '[]')
                
        if os.path.exists(asset):
            cmd.extend(["--add-data", f"{asset}{sep}."])
            print(f"✅ Bundling asset/config: {asset}")

    # Bundle FFmpeg executables (Windows only)
    if current_os == "win32":
        win_binaries = ["ffmpeg.exe", "ffprobe.exe"]
        for binary in win_binaries:
            if os.path.exists(binary):
                cmd.extend(["--add-binary", f"{binary}{sep}."])
                print(f"✅ Bundling Windows binary: {binary}")

    # Set Application Icon
    if current_os == "win32" and os.path.exists("icon.ico"):
        cmd.extend(["--icon", "icon.ico"])
        print("✅ Found application icon: icon.ico")
    elif current_os == "darwin" and os.path.exists("icon.icns"):
        cmd.extend(["--icon", "icon.icns"])
        print("✅ Found application icon: icon.icns")

    # Add the main app script to execute
    cmd.append("main.py")

    cmd_string = " ".join(cmd)
    print(f"\nCommand:\n{cmd_string}\n")

    # 3. Run PyInstaller
    print(f"[3/3] Building the standalone application for [{current_os}]...")
    try:
        subprocess.check_call(cmd)
        print("\n✅ PyInstaller build complete!")
        if current_os == "win32":
            print("📁 Your Standalone Application: dist\\UltimateMediaDownloader.exe")
        elif current_os == "darwin":
            print("📁 Your Standalone Application: dist/UltimateMediaDownloader.app")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with PyInstaller error: {e}")
        return

if __name__ == "__main__":
    main()
