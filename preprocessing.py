# coding: utf-8

from glob import glob

from FRAPanalyzer.lifproc import LIFContainer


class Preprocessing:
    def __init__(self, verbose=False):
        self.verbose = verbose
    
    def get_lsms(self):
        mask = './test_data/06.04.2014*.lsm'    
        lsms = glob(mask)
        if self.verbose:
            print(lsms)
            
        return lsms
    
    def prepare_img(self, lsm):
        if self.verbose:
            print(lsm)
        self.lif = LIFContainer(lsm)

        series_id = self.lif.lif_img_data.keys()[0]
        self.current_series_id = self.lif.lif_series_order.index(series_id)
        self.img = self.lif.get_full_array(series_id, progressbar=True)
        self.img = self.img[:,:,0,:]
    
        if self.verbose:
            print(self.lif.lif_img_data)
            print(self.lif.lif_img_data[series_id])
            print(self.img.shape)
            
    def prepare_rois(self):
        self.rois_struc = self.lif.get_rois_from_oemxml()
