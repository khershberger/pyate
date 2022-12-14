import logging

def basicConfig(filename=None, level=logging.WARNING, level_file=None, level_console=None):
    if level_file is None:
        level_file = level
    if level_console is None:
        level_console = level

    '%Y-%m-%d %H:%M:%S'

    logger_root = logging.getLogger("")
    logger_root.setLevel(min([level, level_file, level_console]))

    # Blow away existing handlers
    logger_root.handlers = []

    # Setup file logging if filename specified
    if filename is not None:
        handler = logging.FileHandler(filename, mode="a")
        handler.setLevel(level_file)
        handler.setFormatter(logging.Formatter("%(asctime)s: %(levelname)-7s %(name)-30s: %(message)s", datefmt=None))
        logger_root.addHandler(handler)

    # Setup console logging (stderr)
    handler = logging.StreamHandler()
    handler.setLevel(level_console)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s: %(message)s"))
    logger_root.addHandler(handler)
