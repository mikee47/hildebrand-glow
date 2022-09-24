from glowmarkt import *
import json

with open("config.json") as f:
    config = json.load(f)

client = BrightClient()
client.token = config["token"]
virtualEntities = client.get_virtual_entities()

for ve in virtualEntities.values():
    print(f"Virtual Entity '{ve.name}'")
    print(json.dumps(ve.data, indent=2))
    resources = ve.get_resources()
    print("Resources: ")
    for res in resources.values():
        print(f"Resource '{res.name}'")
        print(json.dumps(res.data, indent=2))
        tariff = res.get_tariff()
        print(json.dumps(tariff, indent=2))
        current = res.get_current()
        print(json.dumps(current, indent=2))
    print("====")

    # t_from = datetime.datetime.now().replace(hour=0, minute=0, second=0)
    # t_to = t_from + datetime.timedelta(hours=23, minutes=59)

    # t_to = datetime.datetime.now().replace(hour=23, minute=59, second=0)
    t_to = datetime.datetime(2022, 1, 1)
    t_from = t_to - datetime.timedelta(days=10)

    readings = resources["electricity consumption"].get_readings(t_from, t_to)
    for reading in readings:
        print(reading)
    readings = resources["gas consumption"].get_readings(t_from, t_to)
    for reading in readings:
        print(reading)
