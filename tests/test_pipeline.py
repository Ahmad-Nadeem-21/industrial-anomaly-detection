import json
import numpy as np
import pytest
from PIL import Image
from defect_detection.data import make_manifest, verify_manifest, test_records as discover_test
from defect_detection.pixel import PixelBaseline
from defect_detection.metrics import ranking_metrics, normal_threshold


@pytest.fixture
def normal_data(tmp_path):
    folder = tmp_path / 'fixture/train/good'
    folder.mkdir(parents=True)
    for i in range(40):
        Image.fromarray(np.full((12, 19, 3), 100 + i, np.uint8)).save(folder / f'{i:03d}.png')
    return tmp_path


def test_split_determinism_nested_disjoint_and_tamper(normal_data):
    a = make_manifest(normal_data, 'fixture')
    assert a == make_manifest(normal_data, 'fixture')
    assert len(a['calibration']) == 8
    assert not set(a['calibration']) & set(a['fitting_pool'])
    for seed in [17, 29, 43]:
        assert set(a['subsets'][f'{seed}:0.25']) < set(a['subsets'][f'{seed}:0.5']) < set(a['subsets'][f'{seed}:1'])
    assert a['subsets']['17:1'] == a['subsets']['29:1']
    verify_manifest(normal_data, a)
    (normal_data / a['calibration'][0]).write_bytes(b'changed')
    with pytest.raises(ValueError, match='changed'):
        verify_manifest(normal_data, a)


def test_variance_floor_nonsquare_serialization(tmp_path):
    p = tmp_path / 'constant.png'
    Image.fromarray(np.full((12, 19, 3), 100, np.uint8)).save(p)
    model = PixelBaseline(size=8).fit([p, p])
    assert np.all(model.std == .02)
    heatmap, score = model.predict(p)
    assert heatmap.shape == (12, 19) and score == 0
    model.save(tmp_path / 'model.npz')
    np.testing.assert_array_equal(PixelBaseline.load(tmp_path / 'model.npz').predict(p)[0], heatmap)


@pytest.mark.parametrize('scores,auc,ap', [([0, 1], 1, 1), ([1, 0], 0, .5), ([1, 1], .5, .5)])
def test_hand_metrics(scores, auc, ap):
    result = ranking_metrics([0, 1], scores)
    assert result['auroc'] == auc and result['average_precision'] == ap


def test_invalid_and_single_class_metrics():
    assert ranking_metrics([0, 0], [0., 1.])['auroc'] is None
    assert ranking_metrics([1, 1], [0., 1.])['average_precision'] is None
    with pytest.raises(ValueError):
        ranking_metrics([0, 1], [0, np.nan])
    assert normal_threshold([1, 2, 3, 4]) == 4


def test_mask_pairing_and_missing_mask(tmp_path):
    for kind in ['good', 'crack']:
        folder = tmp_path / 'fixture/test' / kind
        folder.mkdir(parents=True)
        Image.fromarray(np.zeros((12, 19, 3), np.uint8)).save(folder / '001.png')
    with pytest.raises(ValueError, match='Missing anomalous mask'):
        discover_test(tmp_path, 'fixture')
    folder = tmp_path / 'fixture/ground_truth/crack'
    folder.mkdir(parents=True)
    mask = np.zeros((12, 19), np.uint8)
    mask[2:4, 3:6] = 255
    Image.fromarray(mask).save(folder / '001_mask.png')
    records = discover_test(tmp_path, 'fixture')
    assert records[0]['label'] == 1 and records[1]['mask'] is None
    Image.fromarray(mask.T).save(folder / '001_mask.png')
    with pytest.raises(ValueError, match='Invalid binary mask'):
        discover_test(tmp_path, 'fixture')

def test_sample_variance_and_localized_nonsquare_defect(tmp_path):
    paths = []
    for i, value in enumerate([100, 120]):
        path = tmp_path / f'{i}.png'
        Image.fromarray(np.full((8, 8, 3), value, np.uint8)).save(path)
        paths.append(path)
    model = PixelBaseline(size=8, sigma=0).fit(paths)
    np.testing.assert_allclose(model.mean, 110 / 255)
    np.testing.assert_allclose(model.std, np.sqrt(200) / 255)
    pixels = np.full((8, 16, 3), 110, np.uint8)
    pixels[2:6, 12:] = 255
    defect = tmp_path / 'defect.png'
    Image.fromarray(pixels).save(defect)
    heatmap, score = model.predict(defect)
    assert heatmap.shape == (8, 16)
    assert np.unravel_index(heatmap.argmax(), heatmap.shape)[1] >= 12
    assert score == heatmap.max() and score > 5


@pytest.mark.parametrize('size', [True, 8.5, 0, -1, float('nan')])
def test_invalid_image_size(size):
    with pytest.raises(ValueError):
        PixelBaseline(size=size)


def test_manifest_rejects_duplicates_empty_and_test_paths(normal_data):
    import copy
    from defect_detection.data import sha256
    original = make_manifest(normal_data, 'fixture')
    duplicate = copy.deepcopy(original)
    duplicate['fitting_pool'].append(duplicate['fitting_pool'][0])
    with pytest.raises(ValueError):
        verify_manifest(normal_data, duplicate)
    empty = copy.deepcopy(original)
    empty['subsets']['17:1'] = []
    with pytest.raises(ValueError):
        verify_manifest(normal_data, empty)
    changed = copy.deepcopy(original)
    source = changed['calibration'].pop()
    foreign = 'fixture/test/good/foreign.png'
    target = normal_data / foreign
    target.parent.mkdir(parents=True)
    target.write_bytes((normal_data / source).read_bytes())
    changed['calibration'].append(foreign)
    changed['sha256'][foreign] = sha256(target)
    with pytest.raises(ValueError, match='training normal'):
        verify_manifest(normal_data, changed)


def test_redirected_training_directory_rejected(normal_data, monkeypatch):
    from pathlib import Path
    from defect_detection.data import normal_paths
    original = Path.resolve
    training = normal_data / 'fixture/train/good'
    def redirected(path, *args, **kwargs):
        resolved = original(path, *args, **kwargs)
        return normal_data / 'fixture/test/good' if resolved == training else resolved
    # Portable simulation: Windows may forbid creation of actual directory symlinks.
    monkeypatch.setattr(Path, 'resolve', redirected)
    with pytest.raises(ValueError, match='redirect'):
        normal_paths(normal_data, 'fixture')
