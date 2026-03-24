from pathlib import Path
import json
import sys

import rasterio
from rasterio.transform import from_bounds
from rasterio.features import rasterize
import fiona


def main():
    layer1_path = Path(sys.argv[1])
    layer2_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])


    from shapely.geometry import shape

    with fiona.open(layer1_path, layer=fiona.listlayers(layer1_path)[0]) as src1:
        feat1 = next(iter(src1), None)
        if feat1 is None:
            print(json.dumps({"ok": False, "error": f"No features in {layer1_path}"}))
            sys.exit(1)
        geom1 = shape(feat1["geometry"])
        crs1 = src1.crs

    with fiona.open(layer2_path, layer=fiona.listlayers(layer2_path)[0]) as src2:
        feat2 = next(iter(src2), None)
        if feat2 is None:
            print(json.dumps({"ok": False, "error": f"No features in {layer2_path}"}))
            sys.exit(1)
        geom2 = shape(feat2["geometry"])

    diff_geom = geom1.difference(geom2)

    if diff_geom.is_empty:
        print(json.dumps({"ok": False, "error": "Difference geometry is empty"}))
        sys.exit(1)

    minx, miny, maxx, maxy = diff_geom.bounds

    width = 500
    height = 500

    transform = from_bounds(minx, miny, maxx, maxy, width, height)

    raster = rasterize(
        [(diff_geom, 1)],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype="uint8"
    )

    if output_path.exists():
        output_path.unlink()

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="uint8",
        crs=crs1,
        transform=transform,
        nodata=0,
    ) as dst:
        dst.write(raster, 1)

    print(json.dumps({
        "ok": True,
        "output": str(output_path),
        "width": width,
        "height": height,
        "bounds": [minx, miny, maxx, maxy]
    }))


if __name__ == "__main__":
    main()