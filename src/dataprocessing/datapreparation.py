import os

import numpy as np


class NodemapStructure:
    """Structure of nodemap files generated by Aramis."""
    def __init__(
            self,
            row_length=10,
            index_coor_x=1,
            index_coor_y=2,
            index_disp_x=4,
            index_disp_y=5,
            index_eps_x=7,
            index_eps_y=8,
            index_eps_xy=9
    ):
        self.row_length = row_length
        self.index_coor_x = index_coor_x
        self.index_coor_y = index_coor_y
        self.index_disp_x = index_disp_x
        self.index_disp_y = index_disp_y
        self.index_eps_x = index_eps_x
        self.index_eps_y = index_eps_y
        self.index_eps_xy = index_eps_xy


class InputData:
    """Class for the import and transformation of input data from DIC nodemaps.

    Methods
        * read_header - method to import metadata from header (if ``data_file`` is provided)
        * read_data_file - method to import input data from file (if ``data_file`` is provided)

        * set_data_manually - set physical data manually instead of from nodemap file
        * transform_data - with a coordinate shift and angle rotation

        * calc_eps_vm - calculate Von Mises strain (stored as attribute)
        * calc_stresses - calculate stresses using material law
        * calc_facet_size - calculate the face size of DIC data
    """
    def __init__(self, data_file: str = None, nodemap_structure: NodemapStructure = NodemapStructure()):
        """
        :param data_file: (str or None) nodemap file path (if provided the methods ``read_data_file``, ``read_header``,
                                        and ``calc_eps_vm``` are run upon initialization)
        :param nodemap_structure: (NodemapStructure) for the nodemap file import
        """
        self.data_file = data_file
        self.nodemap_structure = nodemap_structure

        # input data attributes
        self.coor_x = None
        self.coor_y = None
        self.disp_x = None
        self.disp_y = None
        self.eps_x = None
        self.eps_y = None
        self.eps_xy = None
        self.eps_vm = None

        # methods called when initialized
        if data_file is not None:
            self.read_data_file()
            self.calc_eps_vm()

    def read_data_file(self):
        """Read data from nodemap file."""
        df = np.genfromtxt(self.data_file, delimiter=";", encoding="windows-1252")
        np_df = np.asarray(df, dtype=np.float64)
        nodemap_data = self._cut_nans(np_df)

        self.coor_x = nodemap_data[:, self.nodemap_structure.index_coor_x]
        self.coor_y = nodemap_data[:, self.nodemap_structure.index_coor_y]
        self.disp_x = nodemap_data[:, self.nodemap_structure.index_disp_x]
        self.disp_y = nodemap_data[:, self.nodemap_structure.index_disp_y]
        self.eps_x = nodemap_data[:, self.nodemap_structure.index_eps_x] / 100.0
        self.eps_y = nodemap_data[:, self.nodemap_structure.index_eps_y] / 100.0
        self.eps_xy = nodemap_data[:, self.nodemap_structure.index_eps_xy]

    def calc_eps_vm(self):
        """Calculate Von Mises equivalent strain."""
        self.eps_vm = 2 / 3 * np.sqrt(3 / 2 * (self.eps_x ** 2 + self.eps_y ** 2) + 3 * self.eps_xy ** 2)
        return self.eps_vm

    @staticmethod
    def _cut_nans(df):
        """Reads an array and deletes each row containing any nan value"""
        cut_nans_array = df[~np.isnan(df).any(axis=1)]
        return cut_nans_array


def ground_truth_import(path, side):
    """
    Import of ground truth data.

    :param path: (string) path of ground truth data file.
                 Expected is a path ending with '.txt' without any header.
    :param side: (string) indicating left or right-hand side of specimen.
    :return: array2d (np.array)
    """
    with open(path[:-4] + '_' + side + '.txt', mode='r') as file:
        array2d = [[float(digit) for digit in line.split()] for line in file]
        array2d = np.asarray(array2d)
    if side == 'left':
        array2d = np.fliplr(array2d)
    return array2d


def import_data(nodemaps, data_path, side='', exists_target=True):
    """
    Create dictionaries for Nodemaps and ground truth data.

    :param nodemaps: (dict) of nodemaps by stage numbers
    :param data_path: (string) data folder must contain sub-folders 'Nodemaps', 'GroundTruth'
    :param side: (string) indicating left or right-hand side of specimen
    :param exists_target: (bool) indicates whether or not a target is available, default = True
    :param remove_nan: (bool) whether NaN's should be removed or not, default = True

    :return: inputs, ground_truths (dict)
    """
    print('Data will be imported for ' + side + ' side of the specimen...')

    inputs = {}
    ground_truths = {}

    for _, nodemap in sorted(nodemaps.items()):
        print(f'\r- {nodemap}. {len(inputs.keys()) + 1}/{len(nodemaps)} imported.', end='')

        input_by_nodemap = InputData(os.path.join(data_path, 'Nodemaps', nodemap))
        inputs.update({nodemap + '_' + side: input_by_nodemap})

        if exists_target:
            path = os.path.join(data_path, 'GroundTruth', nodemap)
            ground_truth_by_nodemap = ground_truth_import(path, side)
            ground_truths.update({nodemap + '_' + side: ground_truth_by_nodemap})
        else:
            ground_truths = None

    print('\n')

    return inputs, ground_truths
