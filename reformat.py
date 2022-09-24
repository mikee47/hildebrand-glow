import datetime


def reformat(filename):
    with open(filename, "r") as f:
        prevday = -1
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            date, time, value = line.split()
            t = datetime.datetime.fromisoformat(f"{date} {time}+00:00").astimezone()
            if t.day != prevday:
                print()
                print(t.strftime("%A %B %d %Y"))
                prevday = t.day
            print(t.time().strftime("%H:%M"), value)


reformat("electricity.txt")
