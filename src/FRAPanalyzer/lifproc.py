# -*- coding: utf-8 -*-
import javabridge
import bioformats
from collections import OrderedDict


class LIFContainer:
    def __init__(self, filename):
        self.filename = filename
        self.metadata_in_xml = bioformats.get_omexml_metadata(filename)
        self.metadata_in_xml = self.metadata_in_xml.replace(u'\xb5',' ')

    def get_image_data(self):
        data = OrderedDict()
        ome_metadata = bioformats.omexml.OMEXML(self.metadata_in_xml)

        for i in range(ome_metadata.image_count):
            image = ome_metadata.image(i)
            data[image.Name] = {
                "ID": image.ID,
                "X": image.Pixels.SizeX,
                "Y": image.Pixels.SizeY,
                "C": image.Pixels.SizeC,
                "Z": image.Pixels.SizeZ,
                "T": image.Pixels.SizeT,
            }
        # sa = ome_metadata.structured_annotations
        return data

    def get_image(self, c=0, t=0, z=0, series_id=0):
        with bioformats.ImageReader(self.filename) as reader:
            return reader.read(c=c, t=t, z=z, series=series_id)

def start_bioformats():
    javabridge.start_vm(class_path=bioformats.JARS)
    print('BioContainer started')

def stop_bioformats():
    javabridge.kill_vm()
    print('BioContainer closed')

    # def get_image_series(self, series_id):
    #     with bioformats.ImageReader(self.filename) as reader:
    #         return reader.read(series=series_id)


# path_to_lif = "../test_data/10.05 3T3 PDGFR-HP FRAP.lif"
# path_to_lif = "/Volumes/FLASH_16GB/tmp/lifs/02.18.2011 3T3 HP-Rac1 FRAP.lif"
# path_to_lif = "../test_data/Experiment.lif"
# path_to_lif = "../test_data/Experiment_001.lif"
# path_to_lif = "../test_data/07.22 HeLa-Kyoto HP-PTP1B FRAP after EGF.lif"
