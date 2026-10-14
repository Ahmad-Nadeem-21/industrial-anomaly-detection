import argparse
import importlib.metadata
import json
import platform
from pathlib import Path
import time
import numpy as np
from PIL import Image
from .data import make_manifest, verify_manifest
from .pixel import PixelBaseline
from .metrics import normal_threshold


def write_json(path, content):
    Path(path).write_text(json.dumps(content, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def pilot(root, category, output, config, synthetic=False, fraction=1., seed=17):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    manifest = make_manifest(root, category, config['split_seed'], config['subset_seeds'], config['fractions'])
    verify_manifest(root, manifest)
    write_json(output / 'manifest.json', manifest)
    write_json(output / 'config.json', {**config, 'fraction': fraction, 'subset_seed': seed, 'synthetic': synthetic})
    model = PixelBaseline(config['size'], config['std_floor'], config['sigma'])
    start = time.perf_counter()
    model.fit(Path(root) / p for p in manifest['subsets'][f'{seed}:{fraction:g}'])
    fit_seconds = time.perf_counter() - start
    model.save(output / 'pixel.npz')
    restored = PixelBaseline.load(output / 'pixel.npz')
    calibration = manifest['calibration']
    for _ in range(5):
        model.predict(Path(root) / calibration[0])
    rows, durations = [], []
    for i, relative in enumerate(calibration):
        start = time.perf_counter()
        heatmap, score = model.predict(Path(root) / relative)
        durations.append(time.perf_counter() - start)
        np.save(output / f'normal_map_{i:04d}.npy', heatmap)
        if i == 0:
            np.testing.assert_array_equal(restored.predict(Path(root) / relative)[0], heatmap)
        rows.append({'path': relative, 'normal_calibration_score': score})
    threshold = normal_threshold([r['normal_calibration_score'] for r in rows])
    summary = {'status': 'SYNTHETIC PIPELINE SMOKE; NOT RESEARCH RESULTS' if synthetic else 'NORMAL-ONLY DEVELOPMENT PILOT; NO TEST METRICS',
               'fit_count': model.n, 'calibration_count': len(rows), 'threshold': threshold,
               'decision_rule': 'score > threshold', 'fit_seconds': fit_seconds,
               'end_to_end_latency_seconds': {'median': float(np.median(durations)), 'p95': float(np.quantile(durations, .95)), 'count': len(durations), 'warmups': 5},
               'model_bytes': (output / 'pixel.npz').stat().st_size,
               'serialization_exact_parity': True, 'test_data_accessed': False,
               'python': platform.python_version(), 'platform': platform.platform(),
               'packages': {p: importlib.metadata.version(p) for p in ['numpy', 'scipy', 'Pillow', 'scikit-learn']}}
    write_json(output / 'calibration_scores.json', rows)
    write_json(output / 'summary.json', summary)
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description='Normal-only milestone tools; no final test evaluator enabled.')
    parser.add_argument('command', choices=['synthetic-smoke', 'audit', 'normal-pilot'])
    parser.add_argument('--root', type=Path, default=Path('data/mvtec_ad'))
    parser.add_argument('--category', default='bottle')
    parser.add_argument('--output', type=Path, required=True, help='New output directory; existing runs cannot be overwritten')
    parser.add_argument('--config', type=Path, default=Path('configs/pixel.json'))
    parser.add_argument('--fraction', type=float, choices=[.25, .5, 1.], default=1.)
    parser.add_argument('--seed', type=int, choices=[17, 29, 43], default=17)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    if args.output.exists():
        parser.error('Output already exists; choose a fresh directory')
    if args.command == 'synthetic-smoke':
        fixture = args.output / 'SYNTHETIC_DATA' / 'synthetic' / 'train' / 'good'
        fixture.mkdir(parents=True)
        rng = np.random.default_rng(415)
        for i in range(40):
            pixels = np.clip(rng.normal(128, 4, (48, 80, 3)), 0, 255).astype(np.uint8)
            Image.fromarray(pixels).save(fixture / f'{i:03d}.png')
        pilot(args.output / 'SYNTHETIC_DATA', 'synthetic', args.output / 'run', config, True, args.fraction, args.seed)
    elif args.command == 'audit':
        manifest = make_manifest(args.root, args.category, config['split_seed'], config['subset_seeds'], config['fractions'])
        verify_manifest(args.root, manifest)
        args.output.mkdir(parents=True)
        write_json(args.output / 'manifest.json', manifest)
        print('Normal-only audit passed; test images and masks were not read.')
    else:
        pilot(args.root, args.category, args.output, config, fraction=args.fraction, seed=args.seed)


if __name__ == '__main__':
    main()
