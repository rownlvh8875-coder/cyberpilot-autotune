"""Raw frozen [x,1,y] SVD diagnostic. No clipping, filtering or bucket sampling."""

from .contracts import Point, RawFit, require


def fit_raw(points: tuple[Point, ...]) -> RawFit:
    """NumPy is an optional analysis dependency, not imported by package import."""
    import numpy as np

    require(
        type(points) is tuple and len(points) >= 3 and all(type(p) is Point for p in points),
        "INSUFFICIENT_POINTS",
    )
    matrix = np.array(
        [[p.normalized_command, 1.0, p.lateral_accel_mps2] for p in points], dtype=np.float64
    )
    with np.errstate(all="raise"):
        _, singular, vectors = np.linalg.svd(matrix, full_matrices=False)
        relative = np.finfo(np.float64).eps * max(matrix.shape)
        tolerance = relative * singular[0]
        require(
            bool(
                singular[1] > tolerance
                and singular[1] - singular[2] > tolerance
                and abs(vectors[2, 2]) > relative
            ),
            "DEGENERATE_TLS",
        )
        slope, offset = -vectors[2, :2] / vectors[2, 2]
        require(bool(np.isfinite(slope) and slope > 0), "NONPOSITIVE_FACTOR")
        sine = np.sqrt(slope**2 / (slope**2 + 1))
        cosine = np.sqrt(1 / (slope**2 + 1))
        _, spread = (matrix[:, [0, 2]] @ np.array([[cosine, -sine], [sine, cosine]])).T
        coefficient = np.std(spread) * 1.5
        residual = matrix[:, 2] - (slope * matrix[:, 0] + offset)
        rmse = np.sqrt(np.mean(residual**2))
        values = tuple(float(v) for v in (slope, offset, coefficient, rmse))
        require(all(np.isfinite(v) for v in values), "NONFINITE_TLS")
    return RawFit(values[0], values[1], values[2], values[3], len(points))
