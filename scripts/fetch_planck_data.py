"""Download the Planck 2018 binned TT power spectrum (~7 KB).

Source: Planck Legacy Archive, via the IRSA/IPAC mirror.
Product version R3.01.
"""

import sys
import urllib.request

from cmbpeaks.config import PLANCK_TT_BINNED, PLANCK_TT_BINNED_URL


def main() -> int:
    PLANCK_TT_BINNED.parent.mkdir(parents=True, exist_ok=True)

    if PLANCK_TT_BINNED.exists():
        print(f"already present: {PLANCK_TT_BINNED}")
        return 0

    print(f"downloading {PLANCK_TT_BINNED_URL}")
    try:
        urllib.request.urlretrieve(PLANCK_TT_BINNED_URL, PLANCK_TT_BINNED)
    except Exception as exc:  # noqa: BLE001
        print(f"download failed: {exc}")
        print("Download manually from the URL above and place it in data/.")
        return 1

    with open(PLANCK_TT_BINNED) as f:
        head = [next(f) for _ in range(3)]
    print(f"wrote {PLANCK_TT_BINNED}")
    print("".join(head), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
