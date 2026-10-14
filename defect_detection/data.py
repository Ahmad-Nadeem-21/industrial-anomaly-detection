"""Strict MVTec file pairing; normal-only discovery never traverses test/."""
from pathlib import Path
import hashlib
import math
import numpy as np
from PIL import Image


def sha256(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def category_path(root, category):
    if not category or Path(category).name != category or category in {'.', '..'}:
        raise ValueError('Category must be a single directory name')
    base = Path(root).resolve()
    result = (base / category).resolve()
    if not result.is_relative_to(base):
        raise ValueError('Category escapes dataset root')
    return result


def normal_paths(root, category):
    folder = category_path(root, category) / 'train' / 'good'
    if folder.resolve() != folder:
        raise ValueError('Training directory must not redirect through links')
    paths = sorted(folder.glob('*.png'))
    if len(paths) < 3:
        raise ValueError(f'Need at least 3 normal PNG images: {folder}')
    for path in paths:
        if path.resolve() != path:
            raise ValueError('Training image must not redirect through links')
        with Image.open(path) as image:
            image.load()
    return paths


def test_records(root, category):
    """Explicit final-evaluation helper; not called by normal pilot."""
    folder = category_path(root, category)
    records = []
    for path in sorted((folder / 'test').glob('*/*.png')):
        defect = path.parent.name
        mask = None if defect == 'good' else folder / 'ground_truth' / defect / (path.stem + '_mask.png')
        for source in (path, mask):
            if source is not None and not source.resolve().is_relative_to(folder):
                raise ValueError('Test image or mask escapes category')
        with Image.open(path) as image:
            size = image.size
            image.verify()
        if mask is not None:
            if not mask.is_file():
                raise ValueError(f'Missing anomalous mask: {mask}')
            with Image.open(mask) as image:
                values = np.asarray(image)
                if image.size != size or values.ndim != 2 or not np.isin(values, [0, 255]).all() or not values.any():
                    raise ValueError(f'Invalid binary mask: {mask}')
        records.append({'path': path, 'mask': mask, 'label': int(defect != 'good'), 'defect': defect})
    if not records:
        raise ValueError('No test images found')
    return records


def make_manifest(root, category, split_seed=415, subset_seeds=(17, 29, 43), fractions=(.25, .5, 1.)):
    root = Path(root).resolve()
    paths = normal_paths(root, category)
    relative = [p.relative_to(root).as_posix() for p in paths]
    shuffled = np.random.default_rng(split_seed).permutation(len(paths))
    count = math.ceil(.2 * len(paths))
    calibration = sorted(relative[i] for i in shuffled[:count])
    pool = sorted(relative[i] for i in shuffled[count:])
    subsets = {}
    for seed in subset_seeds:
        order = np.random.default_rng(seed).permutation(len(pool))
        for fraction in fractions:
            n = math.floor(fraction * len(pool))
            if not 0 < fraction <= 1 or n < 2:
                raise ValueError('Every fitting subset must contain at least two images')
            subsets[f'{seed}:{fraction:g}'] = sorted(pool[i] for i in order[:n])
    return {'category': category, 'split_seed': split_seed, 'calibration': calibration, 'fitting_pool': pool,
            'subsets': subsets, 'sha256': {r: sha256(p) for r, p in zip(relative, paths)}}


def verify_manifest(root, manifest):
    base = Path(root).resolve()
    normal_folder = category_path(base, manifest['category']) / 'train' / 'good'
    if normal_folder.resolve() != normal_folder:
        raise ValueError('Training directory must not redirect through links')
    calibration, pool = set(manifest['calibration']), set(manifest['fitting_pool'])
    if (not calibration or len(pool) < 2 or
            len(calibration) != len(manifest['calibration']) or
            len(pool) != len(manifest['fitting_pool']) or not manifest['subsets']):
        raise ValueError('Invalid calibration or fitting pool')
    if calibration & pool:
        raise ValueError('Calibration leakage')
    for subset in manifest['subsets'].values():
        if len(subset) < 2 or len(set(subset)) != len(subset) or not set(subset) <= pool:
            raise ValueError('Invalid fitting subset')
    for relative in calibration | pool:
        path = (base / relative).resolve()
        if Path(relative).is_absolute() or path != base / relative or path.parent != normal_folder or path.suffix != '.png':
            raise ValueError(f'Manifest path is not a training normal: {relative}')
        if not path.is_relative_to(base) or sha256(path) != manifest['sha256'][relative]:
            raise ValueError(f'Manifest content changed: {relative}')
