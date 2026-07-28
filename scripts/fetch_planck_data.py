"""Download the Planck 2018 binned power spectra (TT, EE, TE; a few KB each).

Source: Planck Legacy Archive, via the IRSA/IPAC mirror.
TT is product version R3.01. EE and TE are R3.02 -- see the comment above
PLANCK_EE_BINNED in config.py: Planck's R3.01 EE and TE files have their
contents swapped, so R3.01 is not an option for those two.
"""

import sys
import urllib.request

from cmbpeaks.config import (
    PLANCK_EE_BINNED,
    PLANCK_EE_BINNED_URL,
    PLANCK_TE_BINNED,
    PLANCK_TE_BINNED_URL,
    PLANCK_TT_BINNED,
    PLANCK_TT_BINNED_URL,
)

FILES = [
    ("TT", PLANCK_TT_BINNED, PLANCK_TT_BINNED_URL),
    ("EE", PLANCK_EE_BINNED, PLANCK_EE_BINNED_URL),
    ("TE", PLANCK_TE_BINNED, PLANCK_TE_BINNED_URL),
]


def _fetch_one(label: str, path, url: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        print(f"already present: {path}")
        return 0

    print(f"downloading {label}: {url}")
    try:
        urllib.request.urlretrieve(url, path)
    except Exception as exc:  # noqa: BLE001
        print(f"download failed: {exc}")
        print(f"Download manually from the URL above and place it in data/.")
        return 1

    with open(path) as f:
        head = [next(f) for _ in range(3)]
    print(f"wrote {path}")
    print("".join(head), end="")
    return 0


def main() -> int:
    status = 0
    for label, path, url in FILES:
        status |= _fetch_one(label, path, url)
    return status


if __name__ == "__main__":
    sys.exit(main())
