import json
from pathlib import Path
from utils import get_yaml
from exceptions import EmptyJson


class LocalStorage:
    def __init__(self):
        cfg = get_yaml('config.yaml')
        self.raw_dir = Path(cfg['raw_output_dir'])
        self.raw_dir.mkdir(exist_ok=True)
        self.processed_dir = Path(cfg['processed_output_dir'])
        self.processed_dir.mkdir(exist_ok=True)

    def _get_raw_file_paths(self):
        return list(self.raw_dir.glob('*.json'))

    def read(self):
        files = self._get_raw_file_paths()

        result = []
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

    def write_raw_data(self, vacancies):
        for vacancy in vacancies:
            job_id = vacancy["job_id"]
            filepath = self.raw_dir / f"{job_id}.json"

            with open(filepath, 'w', encoding="utf-8") as outfile:
                json.dump(vacancy, outfile, ensure_ascii=False, indent=4)

            print(f"Save raw vacancy {job_id}")

        print(f"Сохранено {len(vacancies)} вакансий в папку '{self.raw_dir}'")

    def write_processed(self, vacancy: dict, extracted: dict, embedding: list):
        job_id = vacancy.get("job_id")
        data = {
            "job_id": job_id,
            "title": vacancy.get("job_title"),
            "company": vacancy.get("employer_name"),
            "country": vacancy.get("job_country"),
            "remote": vacancy.get("job_is_remote"),
            "url": vacancy.get("job_apply_link"),
            "date_published": vacancy.get("job_posted_at"),
            "extracted": extracted,
            "embedding": embedding  # ← добавили
        }

        filepath = self.processed_dir / f"{job_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"Save processed vacancy {job_id}")

