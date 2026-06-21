import geopandas as gpd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
static_dir = ROOT / 'static'

buildings = gpd.read_file(static_dir / 'buildings.geojson')
print("Unique prop_style values:", buildings['prop_style'].unique())
print("Unique Floor values:", buildings['Floor'].unique())
