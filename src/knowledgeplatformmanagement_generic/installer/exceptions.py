from pathlib import Path


class DirectoryHomeNotFoundError(FileNotFoundError):
    def __init__(self) -> None:
        super().__init__("Home directory does not exist. Cannot install.")


class DirectoryNotFoundError(FileNotFoundError):
    def __init__(self, *, path_dir: Path) -> None:
        super().__init__(f"Directory '{path_dir}' does not exist. Please run the installer first.")
