from pathlib import Path


#
def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_path(output_dir: Path, input_file: Path) -> Path:
    return output_dir / f"{input_file.stem}_processed{input_file.suffix}"
