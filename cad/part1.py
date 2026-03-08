from dataclasses import dataclass
from pathlib import Path

import build123d as bd
import build123d_ease as bde
from build123d_ease import show
from loguru import logger


@dataclass
class Spec:
    """Specification for part1."""

    bolt_hole_d: float = 5.5

    bolt_center_to_edge: float = 9.0

    nominal_gap_between_panels: float = 3.0

    panel_thickness: float = 2.5

    thickness_on_top_of_panel: float = 1.5

    length_along_gap: float = 30.0
    length_out_from_gap: float = 10

    def __post_init__(self) -> None:
        """Post initialization checks."""
        assert True


def part1(spec: Spec) -> bd.Part | bd.Compound:
    """Create a CAD model of part1."""
    p = bd.Part(None)

    # Fill the gap.
    p += bd.Box(
        spec.length_along_gap,
        spec.nominal_gap_between_panels,
        spec.panel_thickness,
        align=bde.align.ANCHOR_BOTTOM,
    )

    # Top part.
    b = bd.Part() + bd.Box(
        spec.length_along_gap,
        2 * spec.length_out_from_gap,
        spec.thickness_on_top_of_panel,
        align=bde.align.ANCHOR_BOTTOM,
    )
    p += bd.Pos(Z=spec.panel_thickness) * b.fillet(
        radius=3, edge_list=b.edges().filter_by(bd.Axis.Z)
    )

    p -= bd.Pos(
        X=(spec.length_along_gap / 2 - spec.bolt_center_to_edge)
    ) * bd.Cylinder(
        radius=spec.bolt_hole_d / 2,
        height=20,
    )

    return p


if __name__ == "__main__":
    parts = {
        "part1": show(part1(Spec())),
    }

    logger.info("Showing CAD model(s)")

    (export_folder := Path(__file__).parent.with_name("build")).mkdir(
        exist_ok=True
    )
    for name, part in parts.items():
        assert isinstance(part, bd.Part | bd.Solid | bd.Compound), (
            f"{name} is not an expected type ({type(part)})"
        )
        if not part.is_manifold:
            logger.warning(f'Part "{name}" is not manifold')

        bd.export_stl(part, str(export_folder / f"{name}.stl"))
        bd.export_step(part, str(export_folder / f"{name}.step"))
