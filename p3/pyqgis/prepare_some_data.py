import json
import sys
from pathlib import Path

import fiona



def main():

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    search_text = sys.argv[3].strip().lower()

    layers = fiona.listlayers(input_path)

    layer_name = layers[0]

    with fiona.open(input_path, layer=layer_name) as src:
        meta = src.meta

        religion_name = "religion"

        if output_path.exists():
            output_path.unlink()

        written = 0

        with fiona.open(output_path, "w", **meta) as dst:
            for feat in src:
                props = feat["properties"]
                value = props.get(religion_name)

                if not search_text:
                    dst.write(feat)
                    written += 1
                elif value is not None and search_text in str(value).lower():
                    dst.write(feat)
                    written += 1

    print(json.dumps({
        "ok": True,
        "input": str(input_path),
        "output": str(output_path),
        "layer": layer_name,
        "religion_name": religion_name,
        "written_features": written
    }))


if __name__ == "__main__":
    main()