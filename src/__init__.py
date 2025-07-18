import importlib
import sys

# Ensure that modules can be imported with an additional "src." prefix.
# Some test suites patch objects via paths like "src.base.dependencies" while
# the actual source code imports them as "base.dependencies".  To make both
# paths resolve to the same modules we add aliases in ``sys.modules`` that
# point the "src." names to the original modules once they are imported.

_prefix = "src."
_top_level_packages = [
    "base",
    "products",
    "users",
    "pricing",
    "webui",
]

for pkg_name in _top_level_packages:
    try:
        module = importlib.import_module(pkg_name)
        # Register alias for the top-level package itself
        sys.modules[_prefix + pkg_name] = module

        # Propagate already imported sub-modules, e.g. ``base.dependencies``
        for name, mod in list(sys.modules.items()):
            if name.startswith(pkg_name + "."):
                alias = _prefix + name
                if alias not in sys.modules:
                    sys.modules[alias] = mod
    except ModuleNotFoundError:
        # Package might not exist in the current project layout; skip it.
        continue
