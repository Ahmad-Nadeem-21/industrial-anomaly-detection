"""Streaming per-position/channel sample statistics and shared postprocessing."""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter


class PixelBaseline:
    def __init__(self, size=224, std_floor=.02, sigma=4.):
        if isinstance(size, (bool, np.bool_)) or not isinstance(size, (int, np.integer)) or size < 1 or not np.isfinite(std_floor) or std_floor <= 0 or not np.isfinite(sigma) or sigma < 0:
            raise ValueError('Invalid pixel configuration')
        self.size, self.std_floor, self.sigma = int(size), float(std_floor), float(sigma)

    def read(self, path):
        with Image.open(path) as image:
            original = image.size
            rgb = image.convert('RGB').resize((self.size, self.size), Image.Resampling.BILINEAR)
            return np.asarray(rgb, dtype=np.float64) / 255., original

    def fit(self, paths):
        n = 0
        mean = np.zeros((self.size, self.size, 3), dtype=np.float64)
        m2 = np.zeros_like(mean)
        for path in paths:
            x, _ = self.read(path)
            n += 1
            delta = x - mean
            mean += delta / n
            m2 += delta * (x - mean)
        if n < 2:
            raise ValueError('Sample standard deviation requires at least two images')
        self.mean, self.std = mean, np.maximum(np.sqrt(np.maximum(m2, 0) / (n - 1)), self.std_floor)
        self.n = n
        return self

    def predict(self, path):
        x, original = self.read(path)
        raw = np.sqrt(np.mean(((x - self.mean) / self.std) ** 2, axis=2))
        smooth = gaussian_filter(raw, sigma=self.sigma, mode='reflect', truncate=4.)
        result = np.asarray(Image.fromarray(smooth.astype(np.float32)).resize(original, Image.Resampling.BILINEAR))
        if not np.isfinite(result).all():
            raise ValueError('Nonfinite prediction')
        return result, float(result.max())

    def save(self, path):
        np.savez_compressed(path, mean=self.mean, std=self.std, n=self.n, size=self.size, std_floor=self.std_floor, sigma=self.sigma)

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as data:
            obj = cls(int(data['size']), float(data['std_floor']), float(data['sigma']))
            obj.mean, obj.std, obj.n = data['mean'], data['std'], int(data['n'])
        shape = (obj.size, obj.size, 3)
        if obj.mean.shape != shape or obj.std.shape != shape or obj.n < 2 or not np.isfinite(obj.mean).all() or not np.isfinite(obj.std).all() or (obj.std < obj.std_floor).any():
            raise ValueError('Invalid saved model')
        return obj
