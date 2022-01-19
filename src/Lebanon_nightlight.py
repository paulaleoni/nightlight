## reading GeoTiff file

import geopandas as gpd
from rasterio.transform import xy
import rioxarray as rxr
from shapely.geometry.multipolygon import MultiPolygon
from shapely import wkt
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.mask import mask
import matplotlib.colors as colors
from adjustText import adjust_text


# load shapefile in geopandas dataframe
# source: https://maps.princeton.edu/catalog/stanford-cp683xh3648
Lebanon_regions = gpd.read_file('data/stanford-cp683xh3648-shapefile.zip')

#Lebanon_regions.plot()

years = ['2012','2015', '2020']
############### using VIIRS
# need to put /vsigzip/ in front of path with .gz
raster20 = rasterio.open('/vsigzip/data/VNL_v2_npp_2020_global_vcmslcfg_c202102150000.median_masked.tif.gz')
raster12 = rasterio.open('/vsigzip/data/VNL_v2_npp_201204-201303_global_vcmcfg_c202102150000.median_masked.tif.gz')
raster15 = rasterio.open('/vsigzip/data/VNL_v2_npp_2015_global_vcmslcfg_c202102150000.median_masked.tif.gz')


#raster.meta

def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]


raster_dic = {years[0] :raster12, years[1]: raster15,years[2]:raster20}
Lebanon_regions[f'light{years[0]}'] = 0.0
Lebanon_regions[f'light{years[2]}'] = 0.0
for y in years:
    raster = raster_dic[f'{y}']
    for i in range(1,len(Lebanon_regions)+1):
        coords = getFeatures(Lebanon_regions.iloc[i-1:i,:])
        out_img, out_transform = mask(raster, shapes=coords, crop=True)
        light = np.average(out_img)
        Lebanon_regions.loc[i-1,f'light{y}'] = light

# get difference
for y in years[0:2]:
    Lebanon_regions[f'light_diff_{y}_20'] = Lebanon_regions.light2020 - Lebanon_regions.loc[:,f'light{y}']
    Lebanon_regions[f'light_reldiff_{y}_20'] = Lebanon_regions.loc[:,f'light_diff_{y}_20'] / Lebanon_regions.loc[:,f'light{y}']


# 
minx, miny, maxx, maxy = Lebanon_regions.geometry.total_bounds

# plot in levels
columns = [f'light{y}' for y in years]
vmin = Lebanon_regions[columns].min().min()
vmax = Lebanon_regions[columns].max().max()

for y in years:
    fig, ax = plt.subplots()
    Lebanon_regions.plot(column = f'light{y}', legend=True, cmap='PRGn', ax = ax, vmin=vmin, vmax=vmax, alpha=.7)
    texts = []
    for i in range(len(Lebanon_regions)):
        point = Lebanon_regions.geometry[i].centroid
        lab = np.round(Lebanon_regions.loc[i,f'light{y}'],1)
        txt = ax.annotate(lab, xy=(point.x, point.y), xytext=(-3, 8), textcoords="offset points", size = 8, fontweight = 'bold', arrowprops={'arrowstyle':'-'})
        texts.append(txt)
    adjust_text(texts)
    ax.set_title(f'average light in {y}')
    ax.text(x= maxx, y = miny, s='unit: nW/cm2/sr', fontsize=8, ha='right')
    ax.axis('off')    
    fig.savefig(f'out/Lebanon_nightlight_{y}.png')


# plot relative difference
columns = [f'light_reldiff_{y}_20' for y in years[0:2]]
vmin = Lebanon_regions[columns].min().min()
vmax = Lebanon_regions[columns].max().max()

for y in years[0:2]:
    fig, ax = plt.subplots()
    divnorm = colors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
    Lebanon_regions.plot(column = f'light_reldiff_{y}_20', legend=True, cmap='PiYG', norm=divnorm, vmin=vmin, vmax=vmax, ax= ax, alpha=.8)
    texts = []
    for i in range(len(Lebanon_regions)):
        point = Lebanon_regions.geometry[i].centroid
        lab = np.round(Lebanon_regions.loc[i,f'light_reldiff_{y}_20'],1)
        txt = ax.annotate(lab, xy=(point.x, point.y), xytext=(-3, 8), textcoords="offset points", size = 8, fontweight = 'bold', arrowprops={'arrowstyle':'-'})
        texts.append(txt)
    adjust_text(texts)
    ax.set_title(f'relative change in average light from {y}-2020')
    ax.axis('off')
    fig.savefig(f'out/Lebanon_nightlight_diff{y}.png')


