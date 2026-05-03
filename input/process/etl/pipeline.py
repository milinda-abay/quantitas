import logging
from pathlib import Path

from settings import DAILY_KLINES, MONTHLY_KLINES, DATA_PATH, KLINE_COL_NAMES
from utils.functions import lower_underscore

from input.process.etl.discovery import KlineDiscovery, KlineSource
from input.process.etl.readers import (
    CsvKlineReader,
    ZipKlineReader,
    CompositeKlineReader,
)
from input.process.etl.transformer import KlineTransformer
from input.process.etl.writer import KlineWriter

logger = logging.getLogger(__name__)


def _purge_partial_downloads(roots: list[Path]) -> None:
    for root in roots:
        for f in root.rglob("*.zip.*"):
            f.unlink()
            logger.info("Removed partial download: %s", f)


def build_pipeline(
    daily_root: Path = DAILY_KLINES,
    monthly_root: Path = MONTHLY_KLINES,
    output_dir: Path = DATA_PATH / "output",
) -> tuple[KlineDiscovery, CompositeKlineReader, KlineTransformer, KlineWriter]:
    col_names = lower_underscore(KLINE_COL_NAMES)
    reader = CompositeKlineReader(
        readers=[CsvKlineReader(col_names), ZipKlineReader(col_names)],
        col_names=col_names,
    )
    discovery = KlineDiscovery(daily_root, monthly_root)
    transformer = KlineTransformer(dedup_col=col_names[0])
    writer = KlineWriter(output_dir)
    return discovery, reader, transformer, writer


def run(
    daily_root: Path = DAILY_KLINES,
    monthly_root: Path = MONTHLY_KLINES,
    output_dir: Path = DATA_PATH / "output",
) -> None:
    _purge_partial_downloads([daily_root, monthly_root])

    discovery, reader, transformer, writer = build_pipeline(
        daily_root, monthly_root, output_dir
    )

    sources: list[KlineSource] = discovery.discover()
    logger.info("Discovered %d (ticker, interval) combinations", len(sources))

    for source in sources:
        try:
            frames = []
            if source.daily_path is not None:
                frames.extend(reader.read(source.daily_path))
            if source.monthly_path is not None:
                frames.extend(reader.read(source.monthly_path))

            df = transformer.transform(frames)
            out = writer.write(df, source.ticker, source.interval)
            logger.info("Wrote %s (%d rows)", out.name, len(df))

        except ValueError as exc:
            logger.warning("Skipping %s/%s — %s", source.ticker, source.interval, exc)
        except Exception as exc:
            logger.error(
                "Failed %s/%s — %s", source.ticker, source.interval, exc, exc_info=True
            )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    run()


if __name__ == "__main__":
    main()
