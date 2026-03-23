import gzip
import xml.etree.ElementTree as ET
import csv

input_file = "emissions.xml.gz"
output_file = "emissions.csv"

with gzip.open(input_file, "rt") as f_in, open(output_file, "w", newline="") as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["time", "vehicle_id", "CO2", "NOx", "fuel"])

    context = ET.iterparse(f_in, events=("end",))

    for event, elem in context:
        if elem.tag == "timestep":
            time = elem.attrib["time"]

            for veh in elem.findall("vehicle"):
                writer.writerow([
                    time,
                    veh.attrib.get("id"),
                    veh.attrib.get("CO2"),
                    veh.attrib.get("NOx"),
                    veh.attrib.get("fuel")
                ])

            elem.clear()


            