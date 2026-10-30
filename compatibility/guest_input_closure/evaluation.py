"""Pure current-state checks; missing historical/immutable proof stays BLOCKED."""

import hashlib

from .archive import guest_dependencies, parse_image
from .contracts import ClosureReport, InputSnapshot
from .inventory import compare_snapshots


def evaluate_closure(
    expected: InputSnapshot, actual: InputSnapshot, images: tuple[bytes, ...]
) -> ClosureReport:
    differences = compare_snapshots(expected, actual)
    images = tuple(images)
    if len(images) > 24 or any(type(image) is not bytes for image in images):
        raise ValueError("invalid fixed image selection")
    issues = list(differences)
    edges: set[tuple[str, str, str]] = set()
    image_errors = not images
    if not images:
        issues.append("IMAGE_MISSING")
    for index, image in enumerate(images):
        try:
            edges.update(guest_dependencies(parse_image(image)))
        except ValueError as error:
            issues.append(f"IMAGE_REJECTED:{index}:{error}")
            image_errors = True
    return ClosureReport(
        not differences,
        not image_errors,
        len(actual.entries),
        len(images),
        tuple(hashlib.sha256(image).hexdigest() for image in images),
        tuple(sorted(edges)),
        tuple(issues),
    )
