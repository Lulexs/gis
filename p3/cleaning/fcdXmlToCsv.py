import gzip
import xml.etree.ElementTree as ET
import csv

input_file = "fcd.xml.gz"
output_file = "fcd.csv"

with gzip.open(input_file, "rt") as f_in, open(output_file, "w", newline="") as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["time", "vehicle_id", "x", "y", "speed", "vehicle_type", "angle"])

    context = ET.iterparse(f_in, events=("end",))
    for event, elem in context:
        if elem.tag == "timestep":
            time = elem.attrib["time"]

            for veh in elem.findall("vehicle"):
                writer.writerow([
                    time,
                    veh.attrib.get("id"),
                    veh.attrib.get("x"),
                    veh.attrib.get("y"),
                    veh.attrib.get("speed"),
                    veh.attrib.get("type"),
                    veh.attrib.get("angle")
                ])

            elem.clear()


