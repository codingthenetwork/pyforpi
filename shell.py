import subprocess

print(subprocess.run(["vcgencmd","measure_temp"],capture_output=True, text=True, check=True).stdout.strip())
