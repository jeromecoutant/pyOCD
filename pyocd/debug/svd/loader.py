# pyOCD debugger
# Copyright (c) 2015-2019 Arm Limited
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import threading
import logging
import pkg_resources
from zipfile import ZipFile

from .parser import SVDParser

## Path within the pyocd package to the generated zip containing builting SVD files.
BUILTIN_SVD_DATA_PATH = "debug/svd/svd_data.zip"

class SVDFile(object):
    @classmethod
    def from_builtin(cls, svd_name):
        zip_stream = pkg_resources.resource_stream("pyocd", BUILTIN_SVD_DATA_PATH)
        zip = ZipFile(zip_stream, 'r')
        return SVDFile(zip.open(svd_name))
    
    def __init__(self, filename=None):
        self.filename = filename
        self.device = None

    def load(self):
        self.device = SVDParser.for_xml_file(self.filename).get_device()

## @brief Thread to read an SVD file in the background.
class SVDLoader(threading.Thread):
    def __init__(self, svdFile, completionCallback):
        super(SVDLoader, self).__init__(name='load-svd')
        self.daemon = True
        self._svd_location = svdFile
        self._svd_device = None
        self._callback = completionCallback

    @property
    def device(self):
        if not self._svd_device:
            self.join()
        return self._svd_device

    def load(self):
        if not self._svd_device and self._svd_location:
            self.start()

    def run(self):
        try:
            self._svd_location.load()
            self._svd_device = self._svd_location.device
            if self._callback:
                self._callback(self._svd_device)
        except IOError:
            logging.warning("Failed to load SVD file %s", self._svd_location.filename)
