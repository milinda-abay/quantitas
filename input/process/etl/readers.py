import io
import logging
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

import pandas as pd

logger = logging.getLogger(__name__)

# Explicit dtypes skip pandas type-inference on every row (big speedup for large files).
_KLINE_DTYPE = {
    0: "int64",
    1: "float64", 2: "float64", 3: "float64", 4: "float64", 5: "float64",
    6: "int64",
    7: "float64",
    8: "int64",
    9: "float64", 10: "float64",
    11: "int64",
}


class KlineReader(ABC):
    def __init__(self, col_names: Sequence[str]) -> None:
        self._col_names = list(col_names)

    @abstractmethod
    def can_handle(self, directory: Path) -> bool: ...

    @abstractmethod
    def read(self, directory: Path) -> list[pd.DataFrame]: ...

    def _parse_csv(self, data: bytes) -> pd.DataFrame:
        return pd.read_csv(
            io.BytesIO(data),
            names=self._col_names,
            header=None,
            dtype=_KLINE_DTYPE,
        )


class CsvKlineReader(KlineReader):
    def can_handle(self, directory: Path) -> bool:
        return directory is not None and directory.exists() and any(directory.glob("*.csv"))

    def read(self, directory: Path) -> list[pd.DataFrame]:
        if not self.can_handle(directory):
            return []
        zip_stems = {p.stem for p in directory.glob("*.zip")}
        frames = []
        for path in sorted(directory.glob("*.csv")):
            if path.stem in zip_stems:
                continue
            logger.info("Reading %s", path.name)
            try:
                frames.append(
                    pd.read_csv(
                        path,
                        names=self._col_names,
                        header=None,
                        dtype=_KLINE_DTYPE,
                    )
                )
            except Exception as exc:
                logger.warning("Skipping %s — %s", path.name, exc)
        return frames


class ZipKlineReader(KlineReader):
    def can_handle(self, directory: Path) -> bool:
        return directory is not None and directory.exists() and any(directory.glob("*.zip"))

    def read(self, directory: Path) -> list[pd.DataFrame]:
        if not self.can_handle(directory):
            return []
        frames = []
        for path in sorted(directory.glob("*.zip")):
            if "." in path.suffix[1:]:
                continue
            logger.info("Reading %s", path.name)
            try:
                with zipfile.ZipFile(path) as zf:
                    csv_members = [n for n in zf.namelist() if n.endswith(".csv")]
                    if not csv_members:
                        logger.warning("No CSV in %s, skipping", path.name)
                        continue
                    if len(csv_members) > 1:
                        logger.warning("%s has %d CSV members, using first", path.name, len(csv_members))
                    frames.append(self._parse_csv(zf.read(csv_members[0])))
            except zipfile.BadZipFile:
                logger.warning("Corrupted ZIP %s, skipping", path.name)
            except Exception as exc:
                logger.warning("Error reading %s — %s", path.name, exc)
        return frames


class CompositeKlineReader(KlineReader):
    def __init__(self, readers: list[KlineReader], col_names: Sequence[str]) -> None:
        super().__init__(col_names)
        self._readers = readers

    def can_handle(self, directory: Path) -> bool:
        return any(r.can_handle(directory) for r in self._readers)

    def read(self, directory: Path) -> list[pd.DataFrame]:
        frames: list[pd.DataFrame] = []
        for reader in self._readers:
            if reader.can_handle(directory):
                frames.extend(reader.read(directory))
        return frames
