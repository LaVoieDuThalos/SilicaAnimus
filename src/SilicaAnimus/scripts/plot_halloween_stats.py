# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import pandas as pd
from matplotlib import pyplot as plt

# %matplotlib ipympl
plt.style.use("fivethirtyeight")

df = pd.read_csv("halloween_2026_messages.csv")
df["created_at"] = pd.to_datetime(df["created_at"])
df = df.set_index("created_at")
df = df.tz_convert("Europe/Paris")

# %%
counts_by_author = df["author"].value_counts().sort_values(ascending=True).to_dict()
fig, ax = plt.subplots()
ax.barh(counts_by_author.keys(), counts_by_author.values())
ax.set_xlabel("Nombre de messages")
plt.tight_layout()

# %%
import numpy as np

pd.plotting.register_matplotlib_converters()
counts, bin_edges = np.histogram(df.index.hour, bins=24, range=(0, 24))
theta = bin_edges[:-1] / 24 * 2 * np.pi
width = 2 * np.pi / 24

fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
ax.bar(theta, counts, width=width)

ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_xticks(np.arange(0, 2 * np.pi, 2 * np.pi / 24))
ax.set_xticklabels([f"{h}h" for h in range(24)])
ax.set_title("Répartition des messages par heure de la journée", pad=20)
ax.set_ylabel("Nombre de messages", labelpad=30)
plt.tight_layout()

# %%
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

FR_MONTHS = [
    "janv.",
    "févr.",
    "mars",
    "avr.",
    "mai",
    "juin",
    "juil.",
    "août",
    "sept.",
    "oct.",
    "nov.",
    "déc.",
]


def french_date_formatter(x, pos=None):
    date = mdates.num2date(x)
    return f"{date.day} {FR_MONTHS[date.month - 1]}"


day_counts = pd.Series(df.index.date).value_counts().sort_index()
day_counts.index = pd.to_datetime(day_counts.index)

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(day_counts.index, day_counts.values, width=0.8)

ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mticker.FuncFormatter(french_date_formatter))
fig.autofmt_xdate(rotation=45, ha="right")

ax.set_title("Nombre de messages par jour", fontsize=14, fontweight="bold", pad=12)
ax.set_xlabel("Jour")
ax.set_ylabel("Nombre de messages")

plt.tight_layout()


# %%
def french_datetime_formatter(x, pos=None):
    date = mdates.num2date(x)
    return f"{date.day} {FR_MONTHS[date.month - 1]} {date.hour:02d}h"


start = pd.Timestamp("2026-10-25", tz="Europe/Paris")
end = pd.Timestamp("2026-11-02", tz="Europe/Paris")

mask = (df.index >= start) & (df.index < end)
hourly_counts = df.loc[mask].resample("h").size()

fig, ax = plt.subplots(figsize=(14, 5))
ax.bar(hourly_counts.index, hourly_counts.values, width=0.03)

ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
ax.xaxis.set_major_formatter(mticker.FuncFormatter(french_datetime_formatter))
ax.xaxis.set_minor_locator(mdates.HourLocator(interval=3))
ax.tick_params(axis="x", which="major", length=7)
ax.tick_params(axis="x", which="minor", length=4)
ax.xaxis.grid(True, which="major", linestyle="--", linewidth=0.5)
fig.autofmt_xdate(rotation=45, ha="right")

ax.set_title(
    "Nombre de messages par heure (dimanche avant Halloween → 1er novembre)",
    fontsize=14,
    fontweight="bold",
    pad=12,
)
ax.set_xlabel("Heure")
ax.set_ylabel("Nombre de messages")

plt.tight_layout()

# %%
