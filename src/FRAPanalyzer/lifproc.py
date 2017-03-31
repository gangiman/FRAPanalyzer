# -*- coding: utf-8 -*-
import javabridge
import bioformats
from collections import OrderedDict
import numpy as np
from tqdm import tqdm
from xml.etree import cElementTree as etree


class LIFContainer:
    def __init__(self, filename):
        self.filename = filename
        self.metadata_in_xml = bioformats.get_omexml_metadata(filename)
        self.metadata_in_xml = self.metadata_in_xml.replace(u'\xb5', ' ')
        self.xml = etree.fromstring(self.metadata_in_xml)
        self.lif_img_data = self.get_image_data()
        self.lif_series_order = list(self.lif_img_data.keys())

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

    def get_full_array(self, series_name, progressbar=False):
        shape = self.lif_img_data[series_name]
        img = np.zeros(tuple(map(shape.get, ['X', 'Y', 'C', 'T'])))
        current_series_id = self.lif_series_order.index(series_name)
        if progressbar:
            _time = tqdm(range(shape['T']))
        else:
            _time = range(shape['T'])
        for t in _time:
            for c in range(shape['C']):
                img[:, :, c, t] = self.get_image(t=t, c=c,
                                                 series_id=current_series_id)
        return img

    def get_rois_from_oemxml(self):
        result = {}
        for elem in self.xml:
            if elem.tag.endswith('ROI'):
                roi = elem
                result[roi.attrib['ID']] = []
                for shape in roi[0]:
                    if shape[0].tag.endswith('Label'):
                        attribs = shape[0].attrib
                        result[roi.attrib['ID']].append(
                            {'X': float(attribs['X']),
                             'Y': float(attribs['Y'])})
                    elif shape[0].tag.endswith('Polygon'):
                        points_txt = shape[0].attrib['Points']
                        points = np.array(
                            [map(float, pair.split(',')) for pair in
                             points_txt.split(' ')])
                        result[roi.attrib['ID']].append({'Polygon': points})
                    elif shape[0].tag.endswith('Ellipse'):
                        result[roi.attrib['ID']].append(
                            {
                                k: float(shape[0].attrib[k])
                                for k in ('RadiusX', 'RadiusY', 'X', 'Y')
                            }
                        )
                        result[roi.attrib['ID']][0].update({'type': 'Ellipse'})

        return result

    def _get_structured_annotations(self):
        ordered_structure = OrderedDict()
        structured_annotations = next(
            sa for sa in self.xml
            if sa.tag.endswith('StructuredAnnotations'))
        for sa in structured_annotations:
            cur = ordered_structure
            key, value = sa[0][0]
            keys = key.text.split('|')
            for _key in keys[:-1]:
                if _key not in cur:
                    cur[_key] = OrderedDict()
                cur = cur[_key]
            cur[keys[-1]] = value.text
        return ordered_structure

    def get_structured_annotations(self):
        full_structured_annotation = OrderedDict()
        original_structured_annotation = self._get_structured_annotations()
        for series_name in self.lif_series_order:
            full_structured_annotation[series_name] = OrderedDict()
            metadata_to_remove = []
            for metadata, sub_dict in original_structured_annotation.items():
                if metadata.startswith(series_name):
                    full_structured_annotation[series_name][
                        metadata[len(series_name) + 1:]] = sub_dict
                    metadata_to_remove.append(metadata)
            for metadata in metadata_to_remove:
                original_structured_annotation.pop(metadata, None)
        if original_structured_annotation:
            full_structured_annotation['other'] = \
                original_structured_annotation
        return full_structured_annotation




def start_bioformats():
    javabridge.start_vm(class_path=bioformats.JARS)
    print('BioContainer started')


def stop_bioformats():
    javabridge.kill_vm()
    print('BioContainer closed')
