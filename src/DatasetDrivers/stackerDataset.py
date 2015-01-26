#!/usr/bin/env python

# ===============================================================================
# Copyright (c)  2014 Geoscience Australia
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither Geoscience Australia nor the names of its contributors may be
#       used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ===============================================================================

from __future__ import absolute_import
from __future__ import print_function
from os.path import join as pjoin
import datetime
import numpy
from osgeo import gdal
from EOtools.tiling import generate_tiles
from EOtools.stats.temporal_stats import temporal_stats


def pq_apply_dict():
    """
    Return a dictionary containing boolean values on whether or not
    to apply a PQ quality flag.
    """

    d = {'Saturation_1': True,
         'Saturation_2': True,
         'Saturation_3': True,
         'Saturation_4': True,
         'Saturation_5': True,
         'Saturation_61': True,
         'Saturation_62': True,
         'Saturation_7': True,
         'Contiguity': True,
         'Land_Sea': True,
         'ACCA': True,
         'Fmask': True,
         'CloudShadow_1': True,
         'CloudShadow_2': True,
         'Empty_1': False,
         'Empty_2': False
         }

    return d


def pq_apply_invert_dict():
    """
    Return a dictionary containing boolean values on whether or not
    to apply a PQ quality flag inversely.
    """

    d = {'Saturation_1': False,
         'Saturation_2': False,
         'Saturation_3': False,
         'Saturation_4': False,
         'Saturation_5': False,
         'Saturation_61': False,
         'Saturation_62': False,
         'Saturation_7': False,
         'Contiguity': False,
         'Land_Sea': False,
         'ACCA': False,
         'Fmask': False,
         'CloudShadow_1': False,
         'CloudShadow_2': False,
         'Empty_1': False,
         'Empty_2': False
         }

    return d


def extract_pq_flags(array, flags=None, invert=None, check_zero=False,
                     combine=False):
    """
    Extracts pixel quality flags from the pixel quality bit array.

    :param array:
        A NumPy 2D array containing the PQ bit array.

    :param flags:
        A dictionary containing each PQ flag and a boolean value
        determining if that flag is to be extracted.
        If None; then this routine will get the default PQ flags dictionary
        which is True for all flags.

    :param invert:
        A dictionary containing each PQ flag and a boolean value
        determining if that flag is to be inverted once extracted.
        Useful if you want to investigate that pheonomena.
        If None; then this routine will get the default invert flags dictionary
        which is False for all flags.

    :param check_zero:
        A boolean keyword as to whether or not the PQ bit array should
        be checked for instances of zero prior to bit extraction.
        Ideally this should be set when investigating specific
        pheonomena. Default is False.

    :param combine:
        A boolean keyword as to whether or not the extracted PQ masks
        should be combined into a single mask.

    :return:
        An n-D NumPy array of type bool where n is given by the number
        of flags present in the flags dictionary. If combine is set
        then a single 2D NumPy array of type bool is returned.

    :notes:
        If either the flags or invert dictionaries contain incorrect
        keys, then they will be reported and ignored during bit
        extraction.

    Example:

        >>> # This will automatically get the default PQ and inversion flags
        >>> # and combine the result into a single boolean array
        >>> pq = stackerDataset.extract_pq_flags(img, check_zero=True, combine=True)
        >>> # For this example, we'll only extract the cloud flags, invert them
        >>> # so we only have the cloud data, and combine them into a single
        >>> # boolean array
        >>> d = stackerDataset.pq_apply_invert_dict()
        >>> # The PQapplyInvertDict() returns False for every flag
        >>> d['ACCA'] = True
        >>> d['Fmask'] = True
        >>> pq = stackerDataset.extract_pq_flags(img, check_zero=True, combine=True, invert=d, flags=d)
    """

    # Check for existance of flags
    if flags is None:
        flags = pq_apply_dict()
    elif not isinstance(flags, dict):
        print("flags must be of type dict. Retrieving default PQ flags dict.")
        flags = pq_apply_dict()

    # Check for existance of invert
    if invert is None:
        invert = pq_apply_invert_dict()
    elif not isinstance(invert, dict):
        print("invert must be of type dict. Retrieving default PQ invert dict.")
        invert = pq_apply_invert_dict()

    # Check for correct dimensionality
    if array.ndim != 2:
        msg = 'Error. Array dimensions must be 2D, not {}'.format(array.ndim)
        raise Exception(msg)

    # image dimensions
    dims = array.shape
    samples = dims[1]
    lines = dims[0]

    # Initialise the PQ flag bit positions
    bit_shift = {'Saturation_1': {'value': 1, 'bit': 0},
                 'Saturation_2': {'value': 2, 'bit': 1},
                 'Saturation_3': {'value': 4, 'bit': 2},
                 'Saturation_4': {'value': 8, 'bit': 3},
                 'Saturation_5': {'value': 16, 'bit': 4},
                 'Saturation_61': {'value': 32, 'bit': 5},
                 'Saturation_62': {'value': 64, 'bit': 6},
                 'Saturation_7': {'value': 128, 'bit': 7},
                 'Contiguity': {'value': 256, 'bit': 8},
                 'Land_Sea': {'value': 512, 'bit': 9},
                 'ACCA': {'value': 1024, 'bit': 10},
                 'Fmask': {'value': 2048, 'bit': 11},
                 'CloudShadow_1': {'value': 4096, 'bit': 12},
                 'CloudShadow_2': {'value': 8192, 'bit': 13},
                 'Empty_1': {'value': 16384, 'bit': 14},
                 'Empty_2': {'value': 32768, 'bit': 15}
                 }

    bits = []
    values = []
    invs = []
    # Check for correct keys in dicts
    for k, v in flags.items():
        if (k in bit_shift) and (k in invert) and v:
            values.append(bit_shift[k]['value'])
            bits.append(bit_shift[k]['bit'])
            invs.append(invert[k])
        else:
            print("Skipping PQ flag {}".format(k))

    # sort via bits
    container = sorted(zip(bits, values, invs))

    nflags = len(container)

    # Extract PQ flags
    if check_zero:
        zero = array == 0
        if combine:
            # When combining we need to turn pixels to False, therefore
            # we initialise as True:
            #     True & True = True
            #     True & False =  False
            #     False & True = False
            #     False & False = False
            mask = numpy.ones(dims, dtype='bool')
            for b, v, i in container:
                if i:
                    mask &= ~((array & v) >> b).astype('bool')
                else:
                    mask &= (array & v) >> b
            # Account for zero during bit extraction
            mask[zero] = True
        else:
            mask = numpy.zeros((nflags, lines, samples), dtype='bool')
            for idx, [b, v, i] in enumerate(container):
                if i:
                    mask[idx] = ~((array & v) >> b).astype('bool')
                else:
                    mask[idx] = (array & v) >> b
            mask[:, zero] = True
    else:
        if combine:
            # When combining we need to turn pixels to False, therefore
            # we initialise as True:
            #     True & True = True
            #     True & False =  False
            #     False & True = False
            #     False & False = False
            mask = numpy.ones(dims, dtype='bool')
            for b, v, i in container:
                if i:
                    mask &= ~((array & v) >> b).astype('bool')
                else:
                    mask &= (array & v) >> b
        else:
            mask = numpy.zeros((nflags, lines, samples), dtype='bool')
            for idx, [b, v, i] in enumerate(container):
                if i:
                    mask[idx] = ~((array & v) >> b).astype('bool')
                else:
                    mask[idx] = (array & v) >> b

    return mask


class StackerDataset:

    """
    A class designed for dealing with datasets returned by stacker.py.
    The reason for only handling data returned by stacker.py are due to
    specific metadata references such as start_datetime and tile_pathname.

    File access to the image dataset is acquired upon request, for example
    when reading the image data.  Once the request has been made the file
    is closed.

    Example:

        >>> fname = 'FC_144_-035_BS.vrt'
        >>> ds = StackerDataset(fname)
        >>> # Get the number of bands associated with the dataset
        >>> ds.bands
        22
        >>> # Get the number of samples associated with the dataset
        >>> ds.samples
        4000
        >>> # Get the number of lines associated with the dataset
        >>> ds.lines
        4000
        >>> # Get the geotransform associated with the dataset
        >>> ds.geotransform
        (144.0, 0.00025000000000000017, 0.0, -34.0, 0.0, -0.00025000000000000017)
        >>> # Get the projection associated with the dataset
        >>> ds.projection
        'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,
        AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],
        UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]'
        >>> # Initialise the yearly iterator
        >>> ds.init_yearly_iterator()
        >>> # Get the yearly iterator dictionary
        >>> ds.get_yearly_iterator()
        {1995: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            1996: [16, 17, 18, 19, 20, 21, 22]}
        >>> # Get the datetime of the first raster band
        >>> ds.get_raster_band_datetime()
        datetime.datetime(1995, 7, 2, 23, 19, 48, 452050)
        >>> # Get the metadata of the first raster band
        >>> ds.get_raster_band_metadata()
        {'start_datetime': '1995-07-02 23:19:48.452050', 'sensor_name': 'TM',
         'start_row': '83', 'end_row': '83', 'band_name': 'Bare Soil',
         'satellite_tag': 'LS5', 'cloud_cover': 'None', 'tile_layer': '3',
         'end_datetime': '1995-07-02 23:20:12.452050',
         'tile_pathname':
         '/g/data1/rs0/tiles/EPSG4326_1deg_0.00025pixel/LS5_TM/144_-035/1995/
          LS5_TM_FC_144_-035_1995-07-02T23-19-48.452050.tif',
         'gcp_count': '52', 'band_tag': 'BS', 'path': '94', 'level_name': 'FC',
         'y_index': '-35', 'x_index': '144', 'nodata_value': '-999'}
        >>> # Initialise the x & y block tiling sequence, using a block size
        >>> # of 400x by 400y
        >>> ds.init_tiling(400,400)
        >>> # Number of tiles
        >>> ds.n_tiles
        100
        >>> # Get the 11th tile (zero based index)
        >>> ds.get_tile(10)
        (400, 800, 0, 400)
        >>> # Read a single raster band. The 10th raster band (one based index)
        >>> img = ds.read_raster_band(10)
        >>> img.shape
        (4000, 4000)
        >>> # Read only a tile of a single raster band
        >>> # First tile, 10th raster band
        >>> img = ds.read_tile(ds.get_tile(0), 10)
        >>> img.shape
        (400, 400)
        >>> # Read all raster bands for the 24th tile
        >>> img = ds.read_tile_all_rasters(ds.get_tile(23))
        >>> img.shape
        (22, 400, 400)
    """

    def __init__(self, filename):
        """
        Initialise the class structure.

        :param file:
            A string containing the full filepath of a GDAL compliant
            dataset created by stacker.py.
        """

        self.fname = filename

        # Open the dataset
        ds = gdal.Open(filename)

        self.bands = ds.RasterCount
        self.samples = ds.RasterXSize
        self.lines = ds.RasterYSize

        self.projection = ds.GetProjection()
        self.geotransform = ds.GetGeoTransform()

        # Initialise the tile variables
        self.tiles = [None]
        self.n_tiles = 0
        self.init_tiling()

        # Get the no data value (assume the same value for all bands)
        band = ds.GetRasterBand(1)
        self.no_data = band.GetNoDataValue()

        # Close the dataset
        band = None
        ds = None

    def get_raster_band_metadata(self, raster_band=1):
        """
        Retrives the metadata for a given band_index.
        (Default is the first band).

        :param raster_band:
            The band index of interest. Default is the first band.

        :return:
            A dictionary containing band level metadata.
        """

        # Open the dataset
        ds = gdal.Open(self.fname)

        # Retrieve the band of interest
        band = ds.GetRasterBand(raster_band)

        # Retrieve the metadata
        metadata = band.GetMetadata()

        # Close the dataset
        band = None
        ds = None

        return metadata

    def get_raster_band_datetime(self, raster_band=1):
        """
        Retrieves the datetime for a given raster band index.

        :param raster_band:
            The raster band interest. Default is the first raster band.

        :return:
            A Python datetime object.
        """

        metadata = self.get_raster_band_metadata(raster_band)
        if 'start_datetime' in metadata:
            dt_item = metadata['start_datetime']
            start_dt = datetime.datetime.strptime(dt_item,
                                                  "%Y-%m-%d %H:%M:%S.%f")

            return start_dt
        else:
            return None

    def init_yearly_iterator(self):
        """
        Creates an interative dictionary containing all the band
        indices available for each year.
        """

        self.yearly_iterator = {}

        band_list = [1]  # Initialise to the first band
        dt_one = self.get_raster_band_datetime()
        if dt_one is not None:
            year_one = dt_one.year
            self.yearly_iterator[year_one] = band_list

            for i in range(2, self.bands + 1):
                year = self.get_raster_band_datetime(raster_band=i).year
                if year == year_one:
                    band_list.append(i)
                    self.yearly_iterator[year_one] = band_list
                else:
                    self.yearly_iterator[year_one] = band_list
                    year_one = year
                    band_list = [i]
        else:
            self.yearly_iterator[0] = range(1, self.bands + 1)

    def get_yearly_iterator(self):
        """
        Returns the yearly iterator dictionary created by init_yearly_iterator.
        """

        return self.yearly_iterator

    def init_tiling(self, xsize=None, ysize=None):
        """
        Sets the tile indices for a 2D array.

        :param xsize:
            Define the number of samples/columns to be included in a
            single tile.
            Default is the number of samples/columns.

        :param ysize:
            Define the number of lines/rows to be included in a single
            tile.
            Default is 10.

        :return:
            A list containing a series of tuples defining the
            individual 2D tiles/chunks to be indexed.
            Each tuple contains ((ystart, yend), (xstart, xend)).
        """
        if xsize is None:
            xsize = self.samples
        if ysize is None:
            ysize = 10
        self.tiles = generate_tiles(self.samples, self.lines, xtile=xsize,
                                    ytile=ysize, Generator=False)
        self.n_tiles = len(self.tiles)

    def get_tile(self, index=0):
        """
        Retrieves a tile given an index.

        :param index:
            An integer containing the location of the tile to be used
            for array indexing.
            Defaults to the first tile.

        :return:
            A tuple containing the start and end array indices, of the
            form ((ystart, yend), (xstart, xend)).
        """

        tile = self.tiles[index]

        return tile

    def read_tile(self, tile, raster_band=1):
        """
        Read an x & y block specified by tile for a given raster band
        using GDAL.

        :param tile:
            A tuple containing the start and end array indices, of the
            form ((ystart, yend), (xstart,xend)).

        :param raster_band:
            If reading from a single band, provide which raster band
            to read from.
            Default is raster band 1.
        """

        ystart = int(tile[0][0])
        yend = int(tile[0][1])
        xstart = int(tile[1][0])
        xend = int(tile[1][1])
        xsize = int(xend - xstart)
        ysize = int(yend - ystart)

        # Open the dataset.
        ds = gdal.Open(self.fname)

        band = ds.GetRasterBand(raster_band)

        # Read the block and flush the cache (potentianl GDAL memory leak)
        subset = band.ReadAsArray(xstart, ystart, xsize, ysize)
        band.FlushCache()

        # Close the dataset
        band = None
        ds = None

        return subset

    def read_tile_all_rasters(self, tile):
        """
        Read an x & y block specified by tile from all raster bands
        using GDAL.

        :param tile:
            A tuple containing the start and end array indices, of the
            form ((ystart, yend), (xstart, xend)).
        """

        ystart = int(tile[0][0])
        yend = int(tile[0][1])
        xstart = int(tile[1][0])
        xend = int(tile[1][1])
        xsize = int(xend - xstart)
        ysize = int(yend - ystart)

        # Open the dataset.
        ds = gdal.Open(self.fname)

        # Read the array and flush the cache (potentianl GDAL memory leak)
        subset = ds.ReadAsArray(xstart, ystart, xsize, ysize)
        ds.FlushCache()

        # Close the dataset
        band = None
        ds = None

        return subset

    def read_raster_band(self, raster_band=1):
        """
        Read the entire 2D block for a given raster band.
        By default the first raster band is read into memory.

        :param raster_band:
            The band index of interest. Default is the first band.

        :return:
            A NumPy 2D array of the same dimensions and datatype of
            the band of interest.
        """

        # Open the dataset.
        ds = gdal.Open(self.fname)

        band = ds.GetRasterBand(raster_band)
        array = band.ReadAsArray()

        # Flush the cache to prevent leakage
        band.FlushCache()

        # Close the dataset
        band = None
        ds = None

        return array

    def write_band_tile(self, array, band_ds, tile=None):
        """
        Given a gdal.band object and optionally a tile index, write the
        x & y tile/block to disk.

        :param array:
            A 2D NumPy array.

        :param band_ds:
            An instance of a gdal.band object suitable for writing to
            disk.

        :param tile:
            (Optional) If array is a subset of a larger array then tile
            is a tuple containing the subsets locations in the form
            ((ystart, yend), (xstart, xend)).
        """
        # Check if we have a GDAL band object
        if isinstance(band_ds, gdal.band):
            if tile is None:
                band_ds.WriteArray(array)
                band_ds.FlushCache()
            else:
                xstart = int(tile[1][0])
                ystart = int(tile[0][0])
                band_ds.WriteArray(array, xstart, ystart)
        else:
            msg = 'band_ds is not of type gdal.band. band_ds is of type {}'
            msg = msg.format(type(band_ds))
            raise TypeError(msg)

    def z_axis_stats(self, out_fname=None):
        """
        Compute statistics over the z-axis of the StackerDataset.
        An image containing 14 raster bands, each describing a
        statistical measure:

            * 1. Sum
            * 2. Valid Observations
            * 3. Mean
            * 4. Variance
            * 5. Standard Deviation
            * 6. Skewness
            * 7. Kurtosis
            * 8. Max
            * 9. Min
            * 10. Median (non-interpolated value)
            * 11. Median Index (zero based index)
            * 12. 1st Quantile (non-interpolated value)
            * 13. 3rd Quantile (non-interpolated value)
            * 14. Geometric Mean

        :param out_fname:
            A string containing the full file system path name of the
            image containing the statistical outputs.

        :return:
            An instance of StackerDataset referencing the stats file.
        """
        # Check if the image tiling has been initialised
        if self.n_tiles == 0:
            self.init_tiling()

        # Get the band names for the stats file
        band_names = ['Sum',
                      'Valid Observations',
                      'Mean', 'Variance',
                      'Standard Deviation',
                      'Skewness',
                      'Kurtosis',
                      'Max',
                      'Min',
                      'Median (non-interpolated value)',
                      'Median Index (zero based index)',
                      '1st Quantile (non-interpolated value)',
                      '3rd Quantile (non-interpolated value)',
                      'Geometric Mean']

        # out number of bands
        out_nb = 14

        # Construct the output image file to contain the result
        if out_fname is None:
            out_fname = pjoin(self.fname, '_z_axis_stats')
        driver = gdal.GetDriverByName("ENVI")
        outds = driver.Create(outfile, samples, lines, out_nb,
                              gdal.GDT_Float32)

        # Setup the geotransform and projection
        outds.SetGeoTransform(self.geotransform())
        outds.SetProjection(self.projection())

        # Construct a list of out band objects
        out_band = []
        for i in range(1, out_nb + 1):
            out_band.append(outds.GetRasterBand(i))
            out_band[i].SetNoDataValue(numpy.nan)
            out_band[i].SetDescription(band_names[i])

        # Loop over every tile
        for tile_n in range(self.n_tiles):
            subset = read_tile_all_rasters(tile_n)
            stats = temporal_stats(subset, no_data=self.no_data)
            for i in range(out_nb):
                write_band_tile(stats[0], out_band[i], tile=tile_n)

        out_band = None
        outds = None

        return StackerDataset(out_fname)
