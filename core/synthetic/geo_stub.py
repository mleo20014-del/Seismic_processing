"""Заглушка геологической модели: 4 горизонтальных слоя."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import mkdtemp
from uuid import uuid4
import numpy as np


@dataclass
class GeologicalModel:
    velocity: np.memmap
    density: np.memmap
    dx: float
    dz: float
    layer_boundaries: list[int]
    velocity_path: Path
    density_path: Path
    metadata: dict = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, int, int]:
        return self.velocity.shape

    @property
    def ram_mb(self) -> float:
        return (self.velocity.nbytes + self.density.nbytes) / 1e6

    def xline_slice(self, x: int) -> tuple[np.ndarray, np.ndarray]:
        """Вертикальный срез вдоль X для предпросмотра в виджете."""
        return self.velocity[x, :, :], self.density[x, :, :]

    def iline_slice(self, y: int) -> tuple[np.ndarray, np.ndarray]:
        """Вертикальный срез вдоль Y."""
        return self.velocity[:, y, :], self.density[:, y, :]

    def depth_slice(self, z: int) -> tuple[np.ndarray, np.ndarray]:
        """Горизонтальный срез на глубине z."""
        return self.velocity[:, :, z], self.density[:, :, z]


# Плотности по петрофизическим справочникам (г/см³)
_LAYER_PARAMS = [
    # name,                      vp_ms,  rho_gcm3
    ("Вода / мягкий осадок",     1500.0, 1.00),
    ("Слабый песчаник",          3000.0, 2.10),
    ("Плотный песчаник",         4000.0, 2.55),
    ("Плотные глины / аргиллит", 5000.0, 2.75),
]


def create_stub_model(
    nx: int = 500,
    ny: int = 500,
    nz: int = 500,
    dx: float = 10.0,
    dz: float = 10.0,
    memmap_dir: Path | None = None,
) -> GeologicalModel:
    """
    Создаёт заглушку: 4 равных горизонтальных слоя.
    Размер куба: nx*dx × ny*dx × nz*dz метров.
    Данные пишутся напрямую в memmap без полного RAM-массива.
    """
    if memmap_dir is None:
        memmap_dir = Path(mkdtemp())
    else:
        memmap_dir.mkdir(parents=True, exist_ok=True)

    velocity_path = memmap_dir / f"geology_velocity_{uuid4().hex}.dat"
    density_path = memmap_dir / f"geology_density_{uuid4().hex}.dat"
    shape = (nx, ny, nz)

    velocity = np.memmap(
        velocity_path,
        dtype=np.float32,
        mode="w+",
        shape=shape,
    )
    density = np.memmap(
        density_path,
        dtype=np.float32,
        mode="w+",
        shape=shape,
    )

    n_layers = len(_LAYER_PARAMS)
    boundaries = [int(round(i * nz / n_layers)) for i in range(n_layers + 1)]

    layers_meta = []
    for i, (name, vp, rho) in enumerate(_LAYER_PARAMS):
        za, zb = boundaries[i], boundaries[i + 1]
        velocity[:, :, za:zb] = vp
        density[:, :, za:zb] = rho
        layers_meta.append({
            "name":     name,
            "vp_ms":    vp,
            "rho_gcm3": rho,
            "z_idx":    [za, zb],
            "depth_m":  [za * dz, zb * dz],
        })

    velocity.flush()
    density.flush()

    metadata = {
        "model_type": "stub_4layer",
        "shape":      (nx, ny, nz),
        "dx_m":       dx,
        "dz_m":       dz,
        "extent_km":  (nx * dx / 1000, ny * dx / 1000, nz * dz / 1000),
        "storage":    "memmap",
        "velocity_memmap_path": str(velocity_path),
        "density_memmap_path":  str(density_path),
        "layers":     layers_meta,
    }

    return GeologicalModel(
        velocity=velocity,
        density=density,
        dx=dx,
        dz=dz,
        layer_boundaries=boundaries,
        velocity_path=velocity_path,
        density_path=density_path,
        metadata=metadata,
    )