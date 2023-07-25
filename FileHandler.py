from pathlib import Path
import json


class FileHandler:
    def __init__(self, path):
        self.file_path = Path(path)
        self.data = []
        if self.file_path.is_file():
            with open(self.file_path, 'r') as f:
                self.data = json.load(f)

    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f)

    def add(self, item):
        self.data.append(item)

    def delete(self, item):
        self.data.remove(item)


class DirFileHandler(FileHandler):
    def __init__(self, path):
        super().__init__(path)

    def get_directories(self):
        return self.data

    def add_directory(self, directory):
        self.add(directory)
        self.save()

    def delete_directory(self, directory):
        self.delete(directory)
        self.save()
