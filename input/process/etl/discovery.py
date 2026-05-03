from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KlineSource:
    ticker: str
    interval: str
    daily_path: Path | None
    monthly_path: Path | None


class KlineDiscovery:
    def __init__(self, daily_root: Path, monthly_root: Path) -> None:
        self._daily_root = daily_root
        self._monthly_root = monthly_root

    def discover(self) -> list[KlineSource]:
        daily_combos = self._scan_root(self._daily_root)
        monthly_combos = self._scan_root(self._monthly_root)
        all_combos = daily_combos | monthly_combos

        return [
            KlineSource(
                ticker=ticker,
                interval=interval,
                daily_path=self._daily_root / ticker / interval if (ticker, interval) in daily_combos else None,
                monthly_path=self._monthly_root / ticker / interval if (ticker, interval) in monthly_combos else None,
            )
            for ticker, interval in sorted(all_combos)
        ]

    def _scan_root(self, root: Path) -> set[tuple[str, str]]:
        if not root.exists():
            return set()
        return {
            (ticker_dir.name, interval_dir.name)
            for ticker_dir in root.iterdir()
            if ticker_dir.is_dir()
            for interval_dir in ticker_dir.iterdir()
            if interval_dir.is_dir()
        }
