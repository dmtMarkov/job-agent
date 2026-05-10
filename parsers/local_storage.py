import json

from pathlib import Path
from exceptions import EmptyJson

def get_file_paths(path: Path) -> list[Path]:
    files = list(path.glob('*.json'))
    return files

def get_data(cfg) -> list[dict]:
    raw_path = Path(cfg['raw_output_dir'])

    files = get_file_paths(raw_path)
    result  = []
    for path in files:
        try:
            with open(path, 'r') as f:
                data = json.load(f)

                if not data:
                    raise EmptyJson

                result.append(data)

        except EmptyJson:
            print(f"Empty file {path}")
        except json.decoder.JSONDecodeError:
            print(f"Unvalid json file: {path}")

    return result


