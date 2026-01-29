import shlex
test_str = r'-path "C:\tools\new_test.txt"'
print(f"Original: {test_str}")
print(f"Posix=True: {shlex.split(test_str)}")
print(f"Posix=False: {shlex.split(test_str, posix=False)}")
