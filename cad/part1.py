from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import build123d as bd
import build123d_ease as bde
from build123d_ease import show
from loguru import logger


@dataclass
class Spec:
    """Specification for clip."""

    bolt_hole_d: float = 5.5

    bolt_center_to_clip_edge: float = 14.0
    bolt_center_to_panel_edge: float = 10.0  # 8mm measured.

    nominal_gap_between_panels: float = 3.0

    panel_thickness: float = 1.8

    thickness_on_top_of_panel: float = 1.5

    length_along_gap: float = 40.0
    length_out_from_gap: float = 10  # In Y. Clip dimension.

    panels_enabled: frozenset[Literal["neg_y", "pos_y"]] = frozenset(
        ["neg_y", "pos_y"]
    )

    def total_x(self) -> float:
        """Size of clip in X direction."""
        return self.length_along_gap

    def __post_init__(self) -> None:
        """Post initialization checks."""
        assert True


def make_clip(spec: Spec) -> bd.Part | bd.Compound:
    """Create a CAD model of part1."""
    p = bd.Part(None)

    # Draw the main body.
    top_box = bd.Part() + bd.Box(
        spec.length_along_gap,
        2 * spec.length_out_from_gap,
        spec.thickness_on_top_of_panel + spec.panel_thickness,
        align=bde.align.ANCHOR_BOTTOM,
    )
    top_box = top_box.fillet(
        radius=3, edge_list=top_box.edges().filter_by(bd.Axis.Z)
    )
    p += top_box

    # Remove the screw hole.
    p -= bd.Pos(
        X=(spec.length_along_gap / 2 - spec.bolt_center_to_clip_edge)
    ) * bd.Cylinder(
        radius=spec.bolt_hole_d / 2,
        height=20,
    )

    # Remove the panels.
    neg_y_panel = bd.Pos(
        X=(
            # Find the bolt center:
            (spec.total_x() / 2 - spec.bolt_center_to_clip_edge)
            # Then move to the panel edge:
            + spec.bolt_center_to_panel_edge
        ),
        Y=-spec.nominal_gap_between_panels / 2,
    ) * bd.Box(
        100,
        100,
        spec.panel_thickness,
        align=(bd.Align.MAX, bd.Align.MAX, bd.Align.MIN),
    )

    if "neg_y" in spec.panels_enabled:
        p -= neg_y_panel
    if "pos_y" in spec.panels_enabled:
        p -= neg_y_panel.mirror(bd.Plane.XZ)

    return p


if __name__ == "__main__":
    parts = {
        "middle_clip": show(make_clip(Spec())),
        "edge_clip_1": show(
            make_clip(Spec(panels_enabled=frozenset(["neg_y"])))
        ),
        "edge_clip_2": show(
            make_clip(Spec(panels_enabled=frozenset(["pos_y"])))
        ),
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
