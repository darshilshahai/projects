from pathlib import Path

from app.ingestion.factory import LoaderFactory

ROOT = Path(__file__).resolve().parents[1]
sample_path = ROOT / "data" / "resume.pdf"

loader = LoaderFactory.get_loader(str(sample_path))
document = loader.load(str(sample_path))

print(document.source)
print(document.content[:300])
print(document.file_type)
print(document.metadata)
