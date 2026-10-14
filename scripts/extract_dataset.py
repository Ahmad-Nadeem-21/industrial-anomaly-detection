"""Safely extract the three study categories from a user-provided MVTec archive."""
import hashlib
import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import time

workspace = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--archive', type=Path, required=True, help='Original MVTec AD tar.xz archive (may be outside the project)')
args = parser.parse_args()
archive = args.archive.resolve(strict=True)
if not archive.is_file():
    raise SystemExit('Archive must be a regular file')
target = workspace / 'data' / 'mvtec_ad'
report = workspace / 'reports' / 'dataset_acquisition.json'
categories = {'bottle', 'carpet', 'screw'}
started = time.perf_counter()
if target.exists() or report.exists():
    raise SystemExit('Refusing to overwrite extraction directory or acquisition report')
target.mkdir(parents=True)
target = target.resolve()
target.relative_to(workspace)
digest = hashlib.sha256()
with archive.open('rb') as stream:
    while block := stream.read(8 * 1024 * 1024):
        digest.update(block)
print('Archive SHA256: ' + digest.hexdigest(), flush=True)
counts = {}
total_bytes = 0
entries = 0
notices = []
with tarfile.open(archive, mode='r|xz') as tar:
    for member in tar:
        entries += 1
        path = PurePosixPath(member.name)
        if path.is_absolute() or '..' in path.parts or '\\' in member.name or ':' in member.name:
            raise ValueError('Unsafe archive path: ' + member.name)
        if not (member.isfile() or member.isdir()):
            raise ValueError('Unsupported archive entry: ' + member.name)
        parts = tuple(p for p in path.parts if p != '.')
        if not parts:
            continue
        selected = parts[0] in categories
        notice = len(parts) == 1 and any(term in parts[0].lower() for term in ('license', 'readme', 'copyright', 'notice'))
        if not selected and not notice:
            continue
        destination = target.joinpath(*parts).resolve()
        destination.relative_to(target)
        if member.isdir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tar.extractfile(member) as source, destination.open('xb') as output:
            shutil.copyfileobj(source, output, 1024 * 1024)
        if destination.stat().st_size != member.size:
            raise ValueError('Extracted size mismatch: ' + member.name)
        total_bytes += member.size
        counts[parts[0]] = counts.get(parts[0], 0) + 1
        if notice:
            notices.append(member.name)
        if sum(counts.values()) % 200 == 0:
            print(f'Extracted {sum(counts.values())} files; scanned {entries} entries', flush=True)
if not all(counts.get(category, 0) > 0 for category in categories):
    raise ValueError('Archive did not contain all three selected categories')
result = dict(archive=archive.name, archive_bytes=archive.stat().st_size,
              sha256=digest.hexdigest(), source='User-provided archive described as official download; not independently authenticated',
              selected_categories=sorted(categories), extracted_file_counts=counts,
              extracted_bytes=total_bytes, scanned_entries=entries, preserved_notices=notices,
              elapsed_seconds=time.perf_counter()-started,
              extraction_checks='Paths confined to target; links and special entries rejected; exclusive file creation; file sizes checked',
              test_evaluation_performed=False)
with report.open('x', encoding='utf-8') as output:
    json.dump(result, output, indent=2)
print(json.dumps(result, indent=2), flush=True)
