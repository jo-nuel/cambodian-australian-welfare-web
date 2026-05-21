"""
Dev runner — starts Django runserver and Tailwind CSS watcher in parallel.

Usage:
    python main.py

Stop both with Ctrl+C.
"""

import os
import signal
import subprocess
import sys


def main():
    base = os.path.dirname(os.path.abspath(__file__))

    tailwind_exe = os.path.join(base, 'static', 'css', 'tailwindcss.exe')
    css_in = os.path.join(base, 'static', 'css', 'input.css')
    css_out = os.path.join(base, 'static', 'css', 'output.css')

    print("Starting Tailwind CSS watcher...")
    tailwind = subprocess.Popen(
        [tailwind_exe, '-i', css_in, '-o', css_out, '--watch'],
        cwd=base,
    )

    print("Starting Django dev server  →  http://127.0.0.1:8000/")
    print("Press Ctrl+C to stop both.\n")
    django = subprocess.Popen(
        [sys.executable, 'manage.py', 'runserver'],
        cwd=base,
    )

    def shutdown(sig, frame):
        print("\nShutting down...")
        tailwind.terminate()
        django.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Block until Django exits; Tailwind keeps running alongside it
    django.wait()
    tailwind.terminate()


if __name__ == '__main__':
    main()
