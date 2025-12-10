import numpy as np
import xarray as xr

def grid_from_latlon(lat_coord, lon_coord):
    bathy = xr.open_dataset('/home/sallen/MEOPAR/grid/bathymetry_202108.nc')

    lat_diff = np.abs(bathy.nav_lat - lat_coord)
    lon_diff  = np.abs(bathy.nav_lon - lon_coord)
    sum_of_diff = lat_diff + lon_diff
    intersect_idx = np.unravel_index(np.nanargmin(np.ma.masked_array(sum_of_diff, mask=tmask[5]).filled(np.nan)), sum_of_diff.shape)

    # fig, ax = plt.subplots(1,2)
    # cb = ax[0].pcolormesh(sum_of_diff)
    # ax[0].set_ylabel('GridY')
    # ax[0].set_xlabel('GridX')
    # viz_tools.set_aspect(ax[0]);
    
    # cb2 = ax[1].pcolormesh(np.ma.masked_array(sum_of_diff, mask=tmask[5]))
    # ax[1].set_ylabel('GridY')
    # ax[1].set_xlabel('GridX')
    # viz_tools.set_aspect(ax[1]);
    # ax[1].plot(intersect_idx[1], intersect_idx[0], 'r*')

    # fig.colorbar(cb, ax=ax[:], label='Lat Diff + Lon Diff')

    print('(y, x): {}'.format(intersect_idx))
    print('Bathy: {} m'.format(bathy['Bathymetry'].isel(y=intersect_idx[0], x=intersect_idx[1]).values))