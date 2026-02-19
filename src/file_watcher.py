import os
import time
import logging
from src.config import DATA_DIR, WATCH_INTERVAL

logger = logging.getLogger(__name__)


class FileWatcher:
    """
    Monitors the data/ folder for new CSV files.
    Triggers a callback function whenever a new file is detected.
    """

    def __init__(self, callback):
        """
        callback: function to call when a new CSV file is detected.
        It receives the full file path as argument.
        """
        self.callback       = callback
        self.processed_files = set()
        self.watch_dir      = DATA_DIR

        # Make sure the data folder exists
        os.makedirs(self.watch_dir, exist_ok=True)
        logger.info(f"Watching folder: {self.watch_dir}")

    def _get_csv_files(self) -> set:
        """Returns all CSV files currently in the watch directory."""
        try:
            return {
                f for f in os.listdir(self.watch_dir)
                if f.endswith('.csv')
            }
        except Exception as e:
            logger.error(f"Error reading watch directory: {e}")
            return set()

    def start(self):
        """
        Starts the continuous folder monitoring loop.
        Runs forever until manually stopped or process is killed.
        """
        logger.info(
            f"File watcher started. "
            f"Scanning every {WATCH_INTERVAL} seconds..."
        )

        while True:
            try:
                current_files = self._get_csv_files()
                new_files     = current_files - self.processed_files

                if new_files:
                    for filename in sorted(new_files):
                        filepath = os.path.join(self.watch_dir, filename)
                        logger.info(f"New file detected: {filename}")

                        try:
                            self.callback(filepath)
                            self.processed_files.add(filename)
                        except Exception as e:
                            logger.error(
                                f"Error processing file {filename}: {e}"
                            )
                            # Don't add to processed so it retries next scan
                else:
                    logger.debug("No new files detected.")

                time.sleep(WATCH_INTERVAL)

            except KeyboardInterrupt:
                logger.info("File watcher stopped by user.")
                break
            except Exception as e:
                logger.error(f"Unexpected watcher error: {e}")
                time.sleep(WATCH_INTERVAL)