#!/usr/bin/env python3
"""
Download every file the climate dashboard uses, organised by GCOS Essential Climate Variable.

    python3 retrieval/download_climate_data.py

This is the same code as retrieval/climate_dashboard_data.ipynb, without the
preview plots and the zip step. Files are saved exactly as published into the
repository's data/ folder, and a download is checked before it replaces a file,
so a broken reply never overwrites good data.

What it fetches (switch any file on or off with get=True/False in FILES below):
  - Greenhouse gases (NOAA GML): global monthly CO2, CH4, N2O; Mauna Loa CO2;
    the AGGI forcing table; optional annual means and growth rates
  - Surface temperature (NASA GISTEMP v4): global, hemispheric and zonal tables
  - Sea surface temperature (NOAA CPC): ONI and RONI, off by default
  - Ocean colour (NOAA CoastWatch ERDDAP): chlorophyll-a subsets as netCDF,
    plus monthly global and regional series (needs: pip install xarray netCDF4)

The chlorophyll grids are large-ish netCDF files and are git-ignored.
"""

from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "data"

GML = "https://gml.noaa.gov/webdata/ccgg/trends"
GML_FTP = "https://gml.noaa.gov/aftp/products/trends"
GISS = "https://data.giss.nasa.gov/gistemp/tabledata_v4"

FILES = [
    # ── Carbon dioxide, methane and other greenhouse gases (Atmosphere) ──
    dict(get=True,  name="co2_mm_gl.csv",  ecv="Greenhouse gases", what="Global CO2, monthly (ppm)",
         urls=[f"{GML}/co2/co2_mm_gl.csv", f"{GML_FTP}/co2/co2_mm_gl.csv"]),
    dict(get=True,  name="ch4_mm_gl.csv",  ecv="Greenhouse gases", what="Global methane, monthly (ppb)",
         urls=[f"{GML}/ch4/ch4_mm_gl.csv"]),
    dict(get=True,  name="n2o_mm_gl.csv",  ecv="Greenhouse gases", what="Global N2O, monthly (ppb)",
         urls=[f"{GML}/n2o/n2o_mm_gl.csv"]),
    dict(get=True,  name="co2_mm_mlo.csv", ecv="Greenhouse gases", what="Mauna Loa CO2, monthly, from 1958 (ppm)",
         urls=[f"{GML}/co2/co2_mm_mlo.csv"]),
    dict(get=True,  name="AGGI_Table.csv", ecv="Greenhouse gases", what="Radiative forcing by gas, annual (W m-2)",
         urls=["https://gml.noaa.gov/aggi/AGGI_Table.csv"]),
    dict(get=False, name="co2_annmean_gl.csv", ecv="Greenhouse gases", what="Global CO2, annual mean",
         urls=[f"{GML}/co2/co2_annmean_gl.csv", f"{GML_FTP}/co2/co2_annmean_gl.csv"]),
    dict(get=False, name="ch4_annmean_gl.csv", ecv="Greenhouse gases", what="Global methane, annual mean",
         urls=[f"{GML}/ch4/ch4_annmean_gl.csv"]),
    dict(get=False, name="n2o_annmean_gl.csv", ecv="Greenhouse gases", what="Global N2O, annual mean",
         urls=[f"{GML}/n2o/n2o_annmean_gl.csv"]),
    dict(get=False, name="co2_gr_gl.csv", ecv="Greenhouse gases", what="Global CO2, annual growth rate",
         urls=[f"{GML}/co2/co2_gr_gl.csv", f"{GML_FTP}/co2/co2_gr_gl.csv"]),
    dict(get=False, name="ch4_gr_gl.csv", ecv="Greenhouse gases", what="Global methane, annual growth rate",
         urls=[f"{GML}/ch4/ch4_gr_gl.csv"]),
    dict(get=False, name="n2o_gr_gl.csv", ecv="Greenhouse gases", what="Global N2O, annual growth rate",
         urls=[f"{GML}/n2o/n2o_gr_gl.csv"]),

    # ── Surface temperature (Atmosphere) ──
    dict(get=True, name="GLB.Ts+dSST.csv", ecv="Surface temperature", what="Global temperature anomaly, monthly (°C vs 1951-1980)",
         urls=[f"{GISS}/GLB.Ts+dSST.csv"]),
    dict(get=True, name="NH.Ts+dSST.csv", ecv="Surface temperature", what="Northern Hemisphere anomaly, monthly",
         urls=[f"{GISS}/NH.Ts+dSST.csv"]),
    dict(get=True, name="SH.Ts+dSST.csv", ecv="Surface temperature", what="Southern Hemisphere anomaly, monthly",
         urls=[f"{GISS}/SH.Ts+dSST.csv"]),
    dict(get=True, name="ZonAnn.Ts+dSST.csv", ecv="Surface temperature", what="Latitude-band anomalies, annual",
         urls=[f"{GISS}/ZonAnn.Ts+dSST.csv"]),

    # ── Sea surface temperature: ENSO (you already have these; switch on to keep them refreshed) ──
    dict(get=False, name="oni.ascii.txt", ecv="Sea surface temperature", what="Oceanic Niño Index (ONI)",
         urls=["https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"]),
    dict(get=False, name="RONI.ascii.txt", ecv="Sea surface temperature", what="Relative Oceanic Niño Index (RONI)",
         urls=["https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"]),
]

# ── Ocean colour: chlorophyll-a from ERDDAP (subsets, so no huge downloads) ──
CHL = dict(
    get=True,
    sources=[  # tried in order: (ERDDAP server, dataset ID)
        ("https://coastwatch.noaa.gov/erddap", "noaacwNPPVIIRSSQchlaMonthly"),
        ("https://polarwatch.noaa.gov/erddap", "nesdisVHNSQchlaMonthly"),
    ],
    variable=None,          # None = find the chlorophyll variable automatically
    record_deg=2.0,         # whole record, global grid every ~2 degrees
    recent_deg=1.0,         # latest months, global grid every ~1 degree
    recent_months=12,
    region_name="Santa Barbara Channel",
    region_lat=(33.9, 34.5),       # south, north (degrees)
    region_lon=(-120.5, -119.3),   # west, east (degrees, -180 to 180)
    band_lat=(-50, 50),     # band for the "global" average; avoids polar-night gaps
)

from urllib.request import Request, urlopen
from urllib.error import HTTPError

HEADERS = {"User-Agent": "Mozilla/5.0 (personal climate dashboard; python urllib)"}

def http_get(url, timeout=120):
    """Fetch a URL and return its bytes (raises on failure)."""
    with urlopen(Request(url, headers=HEADERS), timeout=timeout) as resp:
        return resp.read()

def explain(err):
    text = str(getattr(err, "reason", err))
    if "CERTIFICATE_VERIFY_FAILED" in text:
        return ("SSL certificate error. On a Mac, open Finder > Applications > Python 3.x and "
                "double-click 'Install Certificates.command', then re-run.")
    if isinstance(err, HTTPError):
        return f"HTTP {err.code}"
    return text

def looks_like_data(data):
    head = data[:2000].lower()
    return len(data) > 200 and b"<html" not in head and b"<!doctype" not in head

def download(item):
    for url in item["urls"]:
        try:
            data = http_get(url)
        except Exception as e:
            print(f"  ✗ {item['name']}: {explain(e)} ({url})")
            continue
        if not looks_like_data(data):
            print(f"  ✗ {item['name']}: reply from {url} isn't data; kept any previous copy")
            continue
        (OUT_DIR / item["name"]).write_bytes(data)
        print(f"  ✓ {item['name']:<20} {len(data) / 1024:>6.0f} KB   {item['what']}")
        return True
    return False

OUT_DIR.mkdir(exist_ok=True)
print(f"Saving to: {OUT_DIR.resolve()}\n")
wanted = [f for f in FILES if f["get"]]
failed = [f["name"] for f in wanted if not download(f)]
print(f"\n{len(wanted) - len(failed)} of {len(wanted)} files downloaded.")
if failed:
    print("Not downloaded:", ", ".join(failed), "\nYou can open those links in a browser and save the page instead.")

import re
from urllib.parse import quote

def erddap_url(server, dataset, ext, query=""):
    return f"{server}/griddap/{dataset}.{ext}" + (f"?{quote(query, safe='(),')}" if query else "")

def erddap_grids(server, dataset):
    """Read the dataset structure (.dds): {variable: [(dimension, size), ...]}."""
    dds = http_get(erddap_url(server, dataset, "dds")).decode()
    grids = {}
    for m in re.finditer(r"ARRAY:\s+\w+\s+(\w+)((?:\[[^\]]+\])+);", dds):
        grids[m.group(1)] = [(d, int(n)) for d, n in re.findall(r"\[\s*(\w+)\s*=\s*(\d+)\s*\]", m.group(2))]
    if not grids:
        raise ValueError("no gridded variables found")
    return grids

def erddap_axis(server, dataset, axis):
    """All values of one axis (first two CSV rows are the name and the units)."""
    lines = http_get(erddap_url(server, dataset, "csv", axis)).decode().strip().splitlines()
    return [v.strip() for v in lines[2:]]

def stride_for(values, degrees):
    return max(1, round(degrees / abs(values[1] - values[0])))

def index_range(values, lo, hi):
    idx = [i for i, v in enumerate(values) if lo <= v <= hi]
    if not idx:
        raise ValueError(f"no grid points between {lo} and {hi}")
    return min(idx), max(idx)

def grid_query(var, dims, sel):
    return var + "".join("[{}:{}:{}]".format(*sel.get(d, (0, 1, n - 1))) for d, n in dims)

def get_chlorophyll():
    for server, dataset in CHL["sources"]:
        try:
            grids = erddap_grids(server, dataset)
            break
        except Exception as e:
            print(f"  ✗ {dataset} at {server}: {explain(e)}")
    else:
        print("No chlorophyll server reachable; skipping this step.")
        return None

    var = CHL["variable"] or ("chlor_a" if "chlor_a" in grids else next(v for v in grids if "chl" in v.lower()))
    dims = grids[var]
    size = dict(dims)
    t = next(d for d in size if d.lower() == "time")
    la = next(d for d in size if d.lower().startswith("lat"))
    lo = next(d for d in size if d.lower().startswith("lon"))
    lat = [float(v) for v in erddap_axis(server, dataset, la)]
    lon = [float(v) for v in erddap_axis(server, dataset, lo)]
    times = erddap_axis(server, dataset, t)
    nt = size[t]
    print(f"  {dataset}: '{var}', {nt} months ({times[0][:7]} to {times[-1][:7]}), {size[la]} x {size[lo]} grid\n")

    west, east = CHL["region_lon"]
    if max(lon) > 180:                       # this server uses 0-360 longitudes
        west, east = west % 360, east % 360
    r_lat, r_lon = index_range(lat, *CHL["region_lat"]), index_range(lon, west, east)
    s2, s1 = stride_for(lat, CHL["record_deg"]), stride_for(lat, CHL["recent_deg"])
    k = min(CHL["recent_months"], nt)
    jobs = [
        (f"chl_global_{CHL['record_deg']:g}deg_all.nc",
         {t: (0, 1, nt - 1), la: (0, s2, size[la] - 1), lo: (0, s2, size[lo] - 1)}, "whole record, coarse global grid"),
        (f"chl_global_{CHL['recent_deg']:g}deg_last{k}.nc",
         {t: (nt - k, 1, nt - 1), la: (0, s1, size[la] - 1), lo: (0, s1, size[lo] - 1)}, f"last {k} months, finer global grid"),
        ("chl_region.nc",
         {t: (0, 1, nt - 1), la: (r_lat[0], 1, r_lat[1]), lo: (r_lon[0], 1, r_lon[1])}, f"{CHL['region_name']}, full resolution"),
    ]
    saved = []
    for fname, sel, what in jobs:
        try:
            data = http_get(erddap_url(server, dataset, "nc", grid_query(var, dims, sel)), timeout=900)
        except Exception as e:
            print(f"  ✗ {fname}: {explain(e)}")
            continue
        if not (data[:3] == b"CDF" or data[:4] == b"\x89HDF"):
            print(f"  ✗ {fname}: reply isn't a netCDF file; kept any previous copy")
            continue
        (OUT_DIR / fname).write_bytes(data)
        print(f"  ✓ {fname:<28} {len(data) / 1024**2:>5.1f} MB   {what}")
        saved.append(fname)
    return dict(server=server, dataset=dataset, var=var, files=saved)

chl_info = get_chlorophyll() if CHL["get"] else None

# Monthly chlorophyll series from the grids: area-weighted geometric means
# (chlorophyll is roughly log-normal, so averages are taken in log space).
import numpy as np
import pandas as pd
try:
    import xarray as xr
except ImportError:
    xr = None

def chl_monthly(path, var, lat_band=None):
    with xr.open_dataset(path) as ds:
        da = ds[var]
        extra = [d for d in da.dims if da.sizes[d] == 1 and d != "time" and not d.lower().startswith(("lat", "lon"))]
        da = da.squeeze(extra, drop=True)
        da = da.where((da > 0) & (da < 100))                 # land, cloud and fill values -> NaN
        la = next(d for d in da.dims if d.lower().startswith("lat"))
        lo = next(d for d in da.dims if d.lower().startswith("lon"))
        if lat_band:
            da = da.where((da[la] >= lat_band[0]) & (da[la] <= lat_band[1]), drop=True)
        w = (np.cos(np.deg2rad(da[la])) * xr.ones_like(da)).where(da.notnull())
        mean_log = (np.log10(da) * w).sum((la, lo)) / w.sum((la, lo))
        return pd.DataFrame({
            "date": pd.to_datetime(da["time"].values).strftime("%Y-%m"),
            "chl_mg_m3": (10 ** mean_log).values.round(4),
            "valid_share": da.notnull().mean((la, lo)).values.round(3),
        })

def latest(s):
    ok = s.dropna(subset=["chl_mg_m3"])
    if ok.empty:
        return "(no valid pixels: is the box over land, or always cloudy?)"
    return f"{ok['date'].iloc[-1]}: {ok['chl_mg_m3'].iloc[-1]:.3f} mg m-3"

if chl_info and xr is None:
    print("Install xarray to build the chlorophyll series:  pip install xarray netCDF4")
elif chl_info:
    var = chl_info["var"]
    g = OUT_DIR / f"chl_global_{CHL['record_deg']:g}deg_all.nc"
    if g.exists():
        s = chl_monthly(g, var, CHL["band_lat"])
        s.insert(1, "band", f"{CHL['band_lat'][0]} to {CHL['band_lat'][1]} lat")
        s.to_csv(OUT_DIR / "chl_global_monthly.csv", index=False)
        print(f"  ✓ chl_global_monthly.csv   {len(s)} months, latest {latest(s)}")
    r = OUT_DIR / "chl_region.nc"
    if r.exists():
        s = chl_monthly(r, var)
        s.insert(1, "region", CHL["region_name"])
        s.to_csv(OUT_DIR / "chl_region_monthly.csv", index=False)
        print(f"  ✓ chl_region_monthly.csv   {len(s)} months, latest {latest(s)}")

print("\nDone. Files are in", OUT_DIR)
