from glowmarkt import *
import json

with open("config.json") as f:
    config = json.load(f)

client = BrightClient()
client.token = config["token"]
virtualEntities = client.get_virtual_entities()

electricity_data = open("electricity.txt", "a")
gas_data = open("gas.txt", "a")

for ve in virtualEntities.values():
    print(f"Virtual Entity '{ve.name}'")
    print(json.dumps(ve.data, indent=2))
    print()
    resources = ve.get_resources()
    for res in resources.values():
        print(f"Resource '{res.name}'")
        print(json.dumps(res.data, indent=2))
        print()
        if not res.classifier.endswith('.consumption'):
            continue
        for tariff in res.get_tariff():
            print(json.dumps(tariff.data, indent=2))
            print(str(tariff))
        print()
        # current = res.get_current()
        # print(json.dumps(current, indent=2))
        # print()
    print("====")

    # t_from = datetime.datetime.now().replace(hour=0, minute=0, second=0)
    # t_to = t_from + datetime.timedelta(hours=23, minutes=59)

    # t_to = datetime.datetime.now().replace(hour=23, minute=59, second=0)
    t_from = datetime.datetime(2021, 8, 1)
    t_end = datetime.datetime(2022, 9, 25)

    while t_from < t_end:
        t_to = t_from + datetime.timedelta(days=7) - datetime.timedelta(seconds=1)

        readings = resources["electricity consumption"].get_readings(t_from, t_to)
        for reading in readings:
            print(reading, file=electricity_data)
        readings = resources["gas consumption"].get_readings(t_from, t_to)
        for reading in readings:
            print(reading, file=gas_data)

        t_from += datetime.timedelta(days=7)
