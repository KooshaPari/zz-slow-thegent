"""Use offset/limit for targeted file reading."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class EfficientFileReader:
    """Efficient file reading with offset/limit."""

    def read_chunk(self, file_path: Path, offset: int = 0, limit: int = 1000) -> str:
        """Read a chunk of file.

        Args:
            file_path: File to read
            offset: Byte offset
            limit: Maximum bytes to read

        Returns:
            File chunk content
        """
        with open(file_path, "rb") as f:
            f.seek(offset)
            chunk = f.read(limit)
            return chunk.decode("utf-8", errors="ignore")

    def read_lines(self, file_path: Path, start_line: int = 0, num_lines: int = 100) -> list[str]:
        """Read specific lines from file.

        Args:
            file_path: File to read
            start_line: Starting line number
            num_lines: Number of lines to read

        Returns:
            List of lines
        """
        lines = []
        with open(file_path) as f:
            for i, line in enumerate(f):
                if i < start_line:
                    continue
                if i >= start_line + num_lines:
                    break
                lines.append(line.rstrip())
        return lines
