"""
Processing of the imdb dataset.

URL:
http://ai.stanford.edu/~amaas/data/sentiment/    
REF:
Maas, A. L., Daly, R. E., Pham, P. T., Huang, D., Ng, A. Y., & Potts, C. (2011, June). 
Learning word vectors for sentiment analysis. 
In Proceedings of the 49th Annual Meeting of the Association for Computational Linguistics: Human Language Technologies-Volume 1 (pp. 142-150). Association for Computational Linguistics.
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
from glob import glob
from itertools import islice
from gsitk import config
from gsitk.datasets import utils
from gsitk.datasets.datasets import Dataset
from gsitk.preprocess import normalize

logger = logging.getLogger(__name__)

NAME = os.path.splitext(os.path.basename(__file__))[0]


class Imdb(Dataset):

    def __init__(self, info= None):
        if info is None:
            info = utils.load_info(NAME)
        super(Imdb, self).__init__(info)

    def _extract_metadata(self, file):
        '''
        Gets the metadata (id, rating) from filename
        '''                    
        filename = os.path.splitext(os.path.basename(file))[0]
        id_, rating = filename.split('_')
        id_ = int(id_)
        return id_, rating

    def _say_progress(self, subset, count):
        '''
        Just give me some sense of progress.
        '''
        logger.info('At {} in {}'.format(count, subset))
        sys.stdout.flush()

    def populate_data(self, path, dataframe, relative_path=None, unsup=False, progress=10000, limit=None):
        '''
        Read the train, test or train/unsup directories and puts the data in the passed dataframe.
        '''
        pols = ('pos','neg')
        count = 0
        if unsup:
            for file in islice(glob(os.path.join(path, '*')), limit):
                with open(file, 'r') as f:
                    text = f.read()
                    id_, rating = self._extract_metadata(file)
                    polarity = None
                    dataframe.loc[count, :] = [id_, text, polarity]
                    count += 1
                    if count % progress == 0:
                        self._say_progress('unsup', count)
            return dataframe
        
        for pol in pols:
            for file in islice(glob(os.path.join(path, '{}/{}/*'.format(relative_path, pol))),limit):
                with open(file, 'r') as f:
                    text = f.read()
                    id_, rating = self._extract_metadata(file)
                    polarity = None
                    fold = relative_path
                    if pol == 'pos':
                        polarity = 1
                    else:
                        polarity = -1
                    dataframe.loc[count, :] = [id_, fold, text, polarity, rating]
                    count += 1
                    if count % progress == 0:
                        self._say_progress(relative_path, count)       
        return dataframe

    def normalize_data(self):
        dataset_train = pd.DataFrame(columns=['id', 'fold', 'text', 'polarity', 'rating'])
        dataset_test = pd.DataFrame(columns=['id', 'fold', 'text', 'polarity', 'rating'])
        data_path = os.path.join(config.DATA_PATH, self.name)
        raw_data_path = os.path.join(data_path, self.info['properties']['data_file'])
        self.populate_data(raw_data_path, dataset_train, 'train')
        self.populate_data(raw_data_path, dataset_test, 'test')
        dataset = dataset_train.append(dataset_test, ignore_index=True)
        normalized_text = normalize.normalize_text(dataset)
        dataset['text'] = normalized_text
        
        return dataset

