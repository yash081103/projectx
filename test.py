import os

file_paths = [
    r"E:\project x\6230811349543292597.webp",
    r"E:\project x\6230811349999533710.jpg"
]

for file_path in file_paths:
    if os.path.exists(file_path):
        print(f"File found: {file_path}")
    else:
        print(f"File not found: {file_path}")
