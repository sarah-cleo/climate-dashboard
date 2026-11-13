#!/usr/bin/env python3
"""
Download the raw climate data files for the dashboard.

    Run:   python3 retrieval/get_climate_data.py   (or: python retrieval\\get_climate_data.py on Windows)

The files are saved exactly as published (no cleanup) into the repository's
data/ folder. Re-run any time to refresh them;
NASA updates around the 10th of each month, NOAA roughly monthly.

Only Python's standard library is used, so there is nothing to install.
"""

from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import ssl
import sys

# name to save as  ->  list of URLs to try, in order
FILES = {
    "co2_mm_gl.csv": [
        "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_gl.csv",
        "https://gml.noaa.gov/aftp/products/trends/co2/co2_mm_gl.csv",
    ],
    "ch4_mm_gl.csv": [
        "https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_mm_gl.csv",
    ],
    "n2o_mm_gl.csv": [
        "https://gml.noaa.gov/webdata/ccgg/trends/n2o/n2o_mm_gl.csv",
    ],
    "GLB.Ts+dSST.csv": [
        "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
    ],
    # Optional extras: remove the "#" at the start of a line to include it.
    # "co2_mm_mlo.csv": ["https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv"],  # Mauna Loa, back to 1958
    # "co2_gr_gl.csv":  ["https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_gr_gl.csv"],   # CO2 growth rate
    # "ch4_gr_gl.csv":  ["https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_gr_gl.csv"],   # CH4 growth rate
    # "n2o_gr_gl.csv":  ["https://gml.noaa.gov/webdata/ccgg/trends/n2o/n2o_gr_gl.csv"],   # N2O growth rate
}

OUT_DIR = Path(__file__).resolve().parent.parent / "data"
HEADERS = {"User-Agent": "Mozilla/5.0 (personal climate dashboard; python urllib)"}


def last_data_line(text: str) -> str:
    """Last non-empty line that isn't a '#' comment, to show how current the file is."""
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return "(no data lines found)"


def download(name: str, urls: list[str], out_dir: Path) -> bool:
    for url in urls:
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=60) as resp:
                data = resp.read()
        except HTTPError as e:
            print(f"   {name}: HTTP {e.code} from {url}")
            continue
        except URLError as e:
            reason = e.reason
            if isinstance(reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(reason):
                print(f"   {name}: SSL certificate error.\n"
                      "   On a Mac, open Finder > Applications > Python 3.x and double-click\n"
                      "   'Install Certificates.command', then run this script again.")
                return False
            print(f"   {name}: could not connect to {url} ({reason})")
            continue

        path = out_dir / name
        path.write_bytes(data)
        text = data.decode("utf-8", errors="replace")
        print(f"OK {name}: {len(data)/1024:.0f} KB")
        print(f"     latest row: {last_data_line(text)[:90]}")
        return True
    return False


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    print(f"Saving to: {OUT_DIR}\n")
    failed = [n for n, urls in FILES.items() if not download(n, urls, OUT_DIR)]
    print()
    if failed:
        print("Not downloaded: " + ", ".join(failed))
        print("You can grab those by opening the link in a browser and saving the page.")
        return 1
    print("All done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
