#
# Based on https://github.com/cybermaggedon/pyglowmarkt
#

import requests
import json
import datetime
import time

PT1M = "PT1M"
PT30M = "PT30M"
PT1H = "PT1H"
P1D = "P1D"
P1W = "P1W"
P1M = "P1M"
P1Y = "P1Y"


class Rate:
    pass


class Pence:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%.2f p" % self.value

    def unit(self):
        return "p"


class KWH:
    def __init__(self, value):
        self.value = round(value * 1000)

    def __str__(self):
        return f"{self.value} Wh"

    def unit(self):
        return "Wh"


class Unknown:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % self.value

    def unit(self):
        return "unknown"


class Reading:
    def __init__(self, data: tuple, cls, offset):
        self.utc = data[0] + 60 * offset
        self.value = cls(data[1])

    def datetime(self):
        return datetime.datetime.fromtimestamp(self.utc).astimezone()


class Readings(list):
    def __init__(self, data, offset):
        self.data = data
        if data["units"] == "pence":
            cls = Pence
        elif data["units"] == "kWh":
            cls = KWH
        else:
            cls = Unknown
        for v in data["data"]:
            self.append(Reading(v, cls, offset))


class VirtualEntity:
    def __init__(self, client, data):
        self.client = client
        self.data = data
        self.application = data["applicationId"]
        self.type_id = data["veTypeId"]
        self.id = data["veId"]
        self.postal_code = data.get("postalCode")
        self.name = data.get("name")

    def get_resources(self):
        resp = self.client.api_get(f"virtualentity/{self.id}/resources")
        print(json.dumps(resp, indent=2))
        return dict((elt["name"], Resource(self, elt)) for elt in resp["resources"])


class Tariff:
    pass


class Resource:
    def __init__(self, ve, data):
        self.ve = ve
        self.client = ve.client
        self.data = data
        self.id = data["resourceId"]
        self.type_id = data["resourceTypeId"]
        self.name = data["name"]
        self.classifier = data["classifier"]
        self.description = data["description"]
        self.base_unit = data["baseUnit"]

    def get_readings(self, t_from, t_to, period="PT30M", func="sum"):
        return self.client.get_readings(self.id, t_from, t_to, period, func)

    def get_current(self):
        return self.client.get_current(self.id)

    def get_tariff(self):
        return self.client.get_tariff(self.id)

    def round(self, when, period):
        return self.client.round(when, period)

    def catchup(self):
        # Tried it against the API, no data is returned
        return self.client.api_get(f"resource/{resource}/catchup")


class BrightClient:
    def __init__(self):
        self.application = "b0f1b774-a586-4f72-9edd-27ead8aa7a8d"
        self.url = "https://api.glowmarkt.com/api/v0-1/"
        self.session = requests.Session()
        self.token = None

    def api_get(self, path, params={}):
        headers = {
            "Content-Type": "application/json",
            "applicationId": self.application,
            "token": self.token
        }

        print(f"GET {path}")

        resp = self.session.get(
            f"{self.url}/{path}", headers=headers, params=params)
        if resp.status_code != 200:
            print(resp.text)
            # raise RuntimeError("GET failed")

        return resp.json()

    def api_post(self, path, data):
        headers = {
            "Content-Type": "application/json",
            "applicationId": self.application,
            "token": self.token
        }

        resp = self.session.post(
            f"{self.url}/{path}", headers=headers, data=json.dumps(data))
        if resp.status_code != 200:
            raise RuntimeError("POST failed")

        return resp.json()

    def authenticate(self, username, password):
        data = {
            "username": self.username,
            "password": self.password
        }

        resp = self.api_post("auth", data=json.dumps(data))
        self.token = resp.get("token")
        if resp["valid"] != True or self.token is None:
            raise RuntimeError("Authentication failed")

    def get_virtual_entities(self):
        resp = self.api_get("virtualentity")
        return dict((elt["name"], VirtualEntity(self, elt)) for elt in resp)

    def round(self, when, period):
        # Work out a rounding value.  Readings seem to be more accurate if rounded to the near thing...
        if period == PT1M:
            when = when.replace(second=0, microsecond=0)
        elif period == PT30M:
            when = when.replace(minute=when.minute // 30,
                                second=0, microsecond=0)
        elif period == PT1H:
            when = when.replace(minute=0, second=0, microsecond=0)
        elif period == P1D:
            when = when.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == P1W:
            when = when.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == P1M:
            when = when.replace(day=1, hour=0, minute=0,
                                second=0, microsecond=0)
        else:
            raise RuntimeError("Period %s not known" % period)

        return when

    def get_readings(self, resource, t_from, t_to, period, func="sum"):
        def time_string(x):
            if not isinstance(x, datetime.datetime) and not isinstance(x, datetime.date):
                raise RuntimeError("to_from/t_to should be date/datetime")
            return self.round(x, period).replace(tzinfo=None).isoformat()

        offset = -t_from.utcoffset().seconds / 60  # Offset in minutes

        params = {
            "from": time_string(t_from),
            "to": time_string(t_to),
            "period": period,
            "offset": offset,
            "function": func,
        }

        print(params)

        resp = self.api_get(f"resource/{resource}/readings", params)
        return Readings(resp, offset)

    def get_current(self, resource):
        # Tried it against the API, no data is returned
        resp = self.api_get(f"resource/{resource}/current")

        return resp

        if len(resp["data"]) < 1:
            raise RuntimeError("Current reading not returned")

        if resp["units"] == "pence":
            cls = Pence
        elif resp["units"] == "kWh":
            cls = KWH
        else:
            cls = Unknown

        print(datetime.datetime.fromtimestamp(resp["data"][0][0]))

        return [
            datetime.datetime.fromtimestamp(resp["data"][0][0]).astimezone(),
            cls(resp["data"][0][1])
        ]

    def get_tariff(self, resource):
        resp = self.api_get(f"resource/{resource}/tariff")

        return resp

        ts = []

        for elt in resp["data"]:

            t = Tariff()
            t.name = elt["name"]
            t.commodity = elt["commodity"]
            t.cid = elt["cid"]
            t.type = elt["type"]

            rt = Rate()
            rt.rate = Pence(elt["currentRates"]["rate"])
            rt.standing_charge = Pence(elt["currentRates"]["standingCharge"])
            rt.tier = None

            t.current_rates = rt

            # rts = []
            # for elt2 in elt["structure"]:

            #     rt = Rate()
            #     rt.rate = elt2["planDetail"]["rate"]
            #     rt.standing_charge = elt2["planDetail"]["standing"]
            #     rt.tier = elt2["planDetail"]["tier"]
            #     rts.append(rt)

            # t.structure = rts

        return t
