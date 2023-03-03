from typing import Optional, Dict, Any
import os.path as osp
import numpy as np
import pandas as pd


from tgb.info import PROJ_DIR
from tgb.utils.pre_process import _to_pd_data, reindex


class EdgeRegressionDataset(object):
    def __init__(
        self, 
        name: str, 
        root: Optional[str] = 'datasets', 
        meta_dict: Optional[dict] = None,
        preprocess: Optional[bool] = True,

        ):
        r"""Dataset class for edge regression tasks. Stores meta information about each dataset such as evaluation metrics etc.
        also automatically pre-processes the dataset.
        Args:
            name: name of the dataset
            root: root directory to store the dataset folder
            meta_dict: dictionary containing meta information about the dataset, should contain key 'dir_name' which is the name of the dataset folder
            preprocess: whether to pre-process the dataset
        """
        self.name = name ## original name
        root = PROJ_DIR + root

        if meta_dict is None:
            self.dir_name = '_'.join(name.split('-')) ## replace hyphen with underline
            meta_dict = {'dir_name': self.dir_name}
        else:
            self.dir_name = meta_dict['dir_name']
        self.root = osp.join(root, self.dir_name)
        self.meta_dict = meta_dict
        if ("fname" not in self.meta_dict):
            self.meta_dict["fname"] = self.root + "/" + self.name + ".csv"

        #check if the root directory exists, if not create it
        if osp.isdir(self.root):
            print("Dataset directory is ", self.root)
        else:
            raise FileNotFoundError(f"Directory not found at {self.root}")
        
        #initialize
        self._node_feat = None
        self._edge_feat = None
        self._full_data = None
        self._train_data = None
        self._val_data = None
        self._test_data = None

        #TODO Andy: add url logic here from info.py to manage the urls in a centralized file

        if preprocess:
            self.pre_process()

    def output_ml_files(self):
        r"""Turns raw data .csv file into TG learning ready format such as for TGN, stores the processed file locally for faster access later
        'ml_<network>.csv': source, destination, timestamp, state_label, index 	# 'index' is the index of the line in the edgelist
        'ml_<network>.npy': contains the edge features; this is a numpy array where each element corresponds to the features of the corresponding line specifying one edge. If there are no features, should be initialized by zeros
        'ml_<network>_node.npy': contains the node features; this is a numpy array that each element specify the features of one node where the node-id is equal to the element index.
        """
        #check if path to file is valid 
        if not osp.exists(self.meta_dict['fname']):
            raise FileNotFoundError(f"File not found at {self.meta_dict['fname']}")
        
        #output file names 
        OUT_DF = self.root + '/' + 'ml_{}.csv'.format(self.name)
        OUT_FEAT = self.root + '/' + 'ml_{}.npy'.format(self.name)
        OUT_NODE_FEAT =  self.root + '/' + 'ml_{}_node.npy'.format(self.name)

        #check if the output files already exist, if so, skip the pre-processing
        if osp.exists(OUT_DF) and osp.exists(OUT_FEAT) and osp.exists(OUT_NODE_FEAT):
            print ("pre-processed files found, skipping file generation")
        else:
            df, feat = _to_pd_data(self.meta_dict['fname'])
            df = reindex(df, bipartite=False)
            empty = np.zeros(feat.shape[1])[np.newaxis, :]
            feat = np.vstack([empty, feat])

            max_idx = max(df.u.max(), df.i.max())
            rand_feat = np.zeros((max_idx + 1, 172))

            df.to_csv(OUT_DF)
            np.save(OUT_FEAT, feat)
            np.save(OUT_NODE_FEAT, rand_feat)

    def pre_process(self, 
                    feat_dim=172):
        '''
        Pre-process the dataset and generates the splits, must be run before dataset properties can be accessed
        Parameters:
            feat_dim: dimension for feature vectors, padded to 172 with zeros
        '''
        #check if path to file is valid 
        if not osp.exists(self.meta_dict['fname']):
            raise FileNotFoundError(f"File not found at {self.meta_dict['fname']}")
        
        #TODO Andy write better panda dataloading code, currently the feat is empty
        df, feat = _to_pd_data(self.meta_dict['fname'])  
        df = reindex(df, bipartite=False)

        #self.node_feat = feat
        self._node_feat = np.zeros((df.shape[0], feat_dim))
        self._edge_feat = np.zeros((df.shape[0], feat_dim))
        sources = np.array(df['u'])
        destinations = np.array(df['i'])
        timestamps = np.array(df['ts'])
        edge_idxs = np.array(df['idx'])
        y = np.array(df['w'])

        full_data = {
            'sources': sources,
            'destinations': destinations,
            'timestamps': timestamps,
            'edge_idxs': edge_idxs,
            'y': y
        }
        self._full_data = full_data


    def generate_splits(self,
                        full_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        r"""Generates train, validation, and test splits from the full dataset
        Args:
            full_data: dictionary containing the full dataset
        Returns:
            train_data: dictionary containing the training dataset
            val_data: dictionary containing the validation dataset
            test_data: dictionary containing the test dataset
        """
        print ("hi")

    @property
    def node_feat(self) -> Optional[np.ndarray]:
        r"""
        Returns the node features of the dataset with dim [N, feat_dim]
        Returns:
            node_feat: np.ndarray, [N, feat_dim] or None if there is no node feature
        """
        return self._node_feat
    

    @property
    def edge_feat(self) -> Optional[np.ndarray]:
        r"""
        Returns the edge features of the dataset with dim [E, feat_dim]
        Returns:
            edge_feat: np.ndarray, [E, feat_dim] or None if there is no edge feature
        """
        return self._edge_feat
    

    @property
    def full_data(self) -> Dict[str, Any]:
        r"""
        Returns the full data of the dataset as a dictionary with keys:
            sources, destinations, timestamps, edge_idxs, y (edge weight)
        Returns:
            full_data: Dict[str, Any]
        """
        if (self._full_data is None):
            raise ValueError("dataset has not been processed yet, please call pre_process() first")
        return self._full_data
    

    @property
    def train_data(self) -> Dict[str, Any]:
        r"""
        Returns the train data of the dataset as a dictionary with keys:
            sources, destinations, timestamps, edge_idxs, y (edge weight)
        Returns:
            train_data: Dict[str, Any]
        """
        if (self._train_data is None):
            raise ValueError("dataset has not been processed yet, please call pre_process() first")
        return self._train_data
    
    @property
    def val_data(self) -> Dict[str, Any]:
        r"""
        Returns the validation data of the dataset as a dictionary with keys:
            sources, destinations, timestamps, edge_idxs, y (edge weight)
        Returns:
            val_data: Dict[str, Any]
        """
        if (self._val_data is None):
            raise ValueError("dataset has not been processed yet, please call pre_process() first")
        return self._val_data
    
    @property
    def test_data(self) -> Dict[str, Any]:
        r"""
        Returns the test data of the dataset as a dictionary with keys:
            sources, destinations, timestamps, edge_idxs, y (edge weight)
        Returns:
            test_data: Dict[str, Any]
        """
        if (self._test_data is None):
            raise ValueError("dataset has not been processed yet, please call pre_process() first")
        return self._test_data
    


    

    

    # def get_data(self,
    #         feat_dim: int,
    #         node_features: np.ndarray,
    #         edge_features: np.ndarray,
    #         full_data: Dict,
    #         train_data: Dict,
    #         val_data: Dict,
    #         test_data: Dict,
    #         new_node_val_data: Dict,
    #         new_node_test_data: Dict,
    #         ):
    #     r'''
    #     full_data, train_data, val_data, test_data, new_node_val_data, new_node_test_data
    #     function specifying the output to tgn
    #     Parameters:
    #         feat_dim: pad to this dimension must be same as the memory dimension, can be enforced in config file
    #         node_features: node features, [N, feat_dim]
    #         edge_features: edge features  [E, feat_dim]
    #         full_data: dictionary containing full data, must have sources, destinations, timestamps, edge_idxs, edge_labels

    #     '''
    #     full_data = {
    #         sources: np.ndarray, #int numpy array, [E,1]
    #         destinations: np.ndarray, #int numpy array, [E,1]
    #         timestamps: np.ndarray, #float numpy array, converted from int, [E,1]
    #         edge_idxs: np.ndarray, #int numpy array, [E,1]
    #         y: np.ndarray, #edge weight, here used as target for edge regresssion
    #     }


    # @property new_node_val_data
    # @property new_node_test_data



def main():
    dataset = EdgeRegressionDataset(name="un_trade", root="datasets", preprocess=True)
    
    dataset.node_feat
    dataset.edge_feat #not the edge weights
    dataset.full_data
    dataset.train_data
    dataset.val_data
    dataset.test_data
    dataset.full_data["y"] 

if __name__ == "__main__":
    main()