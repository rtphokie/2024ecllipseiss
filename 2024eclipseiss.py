import unittest
from drawmap import plot_eclipse_paths
from skyfield.api import load, wgs84
import pandas as pd
import geopandas as gpd
from pprint import pprint
from EB.read import readfiles, get_bounds
import matplotlib.pyplot as plt
from shapely import Polygon, Point, geometry, LineString

stations_url = 'http://celestrak.org/NORAD/elements/stations.txt'
satellites = load.tle_file(stations_url)
print('Loaded', len(satellites), 'satellites')
by_name = {sat.name: sat for sat in satellites}
satellite = by_name['ISS (ZARYA)']
print(satellite)
ts = load.timescale()
newcrs = "EPSG:4326"
newcrs = "ESRI:102004"
dpi = 300
pathcolor = {'Total': 'grey', 'Annular': 'darkorange', 'Hybrid': 'red',
             'city_marker': 'lightgrey', 'city_marker_labeled': 'grey', 'city_label': 'grey',
             'world': '#809E7E', 'water': '#8AB4F8', 'coast': '#090eab',
             # 'state_domestic': '#fcfad7', 'state_foreign': '#FADBD8', 'state_highlight': '#FFF4DA',
             'state_domestic': '#F7F3E9', 'state_foreign': '#90A686', 'state_highlight': '#fcfad7',
             'state_domestic_edge': 'k', 'state_foreign_edge': 'k',
             'state_highlight_edge': 'k'
             }


def draw_map(gdf_iss):
    gdf_iss=gdf_iss.to_crs(newcrs)
    gdf_world, ca, us, us_counties, mx = readfiles()
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(12, 9), dpi=dpi)

    notlower48 = ['Hawaii', 'Commonwealth of the Northern Mariana Islands', 'Guam', 'Puerto Rico', 'Alaska',
                  'American Samoa', 'Northwest Territories', 'Nunavut', 'Yukon']

    na = pd.concat([ca, us, mx])
    na = na.to_crs(newcrs)
    na = na[~na.NAME.isin(notlower48)]
    xmin, xmax, ymin, ymax = get_bounds(na)
    xmin-=1000000
    xmax+=1000000
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    d = {'geometry': [Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax), ])]}
    gdf_water = gpd.GeoDataFrame(d, crs=na.crs)
    gdf_water.plot(ax=ax, color=pathcolor['water'], edgecolor='k', linewidth=2.5)
    na.plot(ax=ax, color=pathcolor['state_domestic'], edgecolor='k', linewidth=0.3)
    plot_eclipse_paths(ax, na, eclispe_list=['2024-04-08'], alpha_path=.3, label=None, path=True, center=False, outer=True)
    gdf_iss.plot(ax=ax, linewidth=1, edgecolor='dodgerblue')
    # gdf_iss.iloc[[0]].plot(ax=ax, linewidth=2, edgecolor='lightblue')
    # gdf_iss.iloc[[1]].plot(ax=ax, linewidth=2, edgecolor='lightblue')
    # gdf_iss.iloc[[2]].plot(ax=ax, linewidth=2, edgecolor='dodgerblue')
    fig.tight_layout()
    ax.axis('off')
    plt.savefig('myplot.png')


class MyTestCase(unittest.TestCase):
    def test_map(self):
        draw_map()

    def test_something(self):
        # You can instead use ts.now() for the current time
        times = ts.utc(2024, 4, 8, 15, range(47, 47 + (10 * 60)))
        times = ts.utc(2024, 4, 8, 19, range(60))

        geocentric = satellite.at(times)
        lats, lons = wgs84.latlon_of(geocentric)
        # print('Latitude:', lat)
        # print('Longitude:', lon)
        rows=[]
        prevlat=-90
        passno=0
        prevtime=times[0]

        for t, lat, lon in zip(times, lats.degrees, lons.degrees):
            if lon < 0 and lat >= 8:
                print(f"{t.utc_jpl()} {lat:8.2f}, {lon:8.2f}")
                if t-prevtime > (1/48):
                    passno+=1
                rows.append({'lat': lat, 'lon': lon, 'passno': passno})
                prevtime=t
        df=pd.DataFrame.from_records(rows)
        geometry = [Point(xy) for xy in zip(df['lon'], df['lat'])]
        geo_df = gpd.GeoDataFrame(df, geometry=geometry)
        geo_df2 = geo_df.groupby(['passno'])['geometry'].apply(lambda x: LineString(x.tolist()))
        geo_df2 = gpd.GeoDataFrame(geo_df2, geometry='geometry', crs={'init': 'epsg:4326'})

        print(geo_df2)
        draw_map(geo_df2)


if __name__ == '__main__':
    unittest.main()
