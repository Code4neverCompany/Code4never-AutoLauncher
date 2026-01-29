import shlex
test_str = r'-path "C:\My Folder\File.txt" -arg 2'
print(f"Original: {test_str}")
print(f"Posix=True (Default): {shlex.split(test_str)}")
print(f"Posix=False: {shlex.split(test_str, posix=False)}")
