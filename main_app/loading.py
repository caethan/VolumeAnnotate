import tifffile
import zarr
import struct
import json
import requests
from bs4 import BeautifulSoup
import os
import numpy as np
import time
import copy

from collections import defaultdict
import re

# class RemoteZarr:
# 	def __init__(self, url, username, password, path, max_storage_gb=10, chunk_type="zstack"):
# 		self.url = url
# 		self.username = username
# 		self.password = password
# 		self.path = path
# 		file_list = np.array(list_files(url, username, password))
# 		if chunk_type == "zstack":
# 			self.file_list = tifffile.TiffSequence(file_list, pattern=r"(\d+).tif")
# 		else:
# 			self.file_list = tifffile.TiffSequence(file_list, pattern=r"cell_yxz_(\d+)_(\d+)_(\d+)")
		
# 		self.shape0 = self.file_list.shape

# 		self.file_indices = self.file_list.indices
# 		self.file_list = np.array(self.file_list.files)
# 		self.indexFileDict = {index:filename for index, filename in zip(self.file_indices, self.file_list)}
# 		self.downloaded = {}
# 		self.filesNeeded = [os.path.join(self.path, filename) for filename in self.file_list[:1]]

# 		self.chunk_type = chunk_type

# 		self.max_storage_gb = max_storage_gb
# 		#download first file to get shape and dtype
# 		self._download_file([self.file_list[0]])
# 		f = tifffile.imread(os.path.join(self.path, self.file_list[0]))
# 		self.fileshape = f.shape
# 		if chunk_type == "cuboid":
# 			self.fileshape = np.array([1, self.fileshape[0], self.fileshape[1]])
# 		self.filesize = f.nbytes
# 		self.dtype = f.dtype
# 		if chunk_type == "zstack":
# 			self.shape = np.array([self.shape0[0],self.fileshape[1], self.fileshape[0]])
# 		else:
# 			self.shape = np.array(self.fileshape)*np.array([self.shape0[2], self.shape0[0], self.shape0[1]])
# 		self.maxfiles = int(self.max_storage_gb*1e9/self.filesize)

# 		self.store = None

# 		self._shape = None #current shape of store

# 		self.chunks = None

# 		#self.bounds = [0,0,0,0,0,0] #zstart, zstop, ystart, ystop, xstart, xstop
# 		self.offset = [0,0,0] #z, y, x

# 		tiffs = [filename for filename in os.listdir(self.path) if filename.endswith(".tif")]
# 		if len(tiffs) > 0:
# 			self.update_store()
# 		else:
# 			firstSlice = self[0:1,:,:]


# 	def update_store(self, currfileindex=None):
# 		'''
# 		delete files if necessary (outside bounds)
# 		update store with new files
# 		and recomputes offset and bounds
# 		'''
# 		store, tiffs, indices = load_tif(self.path, self.filesNeeded, returnFormat=1)
# 		if self.chunks is None:
# 			self.chunks = store._chunks

# 		if len(tiffs) > self.maxfiles:
# 			#delete files ordered by use time
# 			#delete files until we are below maxfiles
# 			tiffsByTime = sorted(tiffs, key=lambda f: os.path.getatime(os.path.join(self.path, f)))
# 			#reverse list so we delete oldest first
# 			tiffsByTime.reverse()
# 			filesToDelete = tiffsByTime[self.maxfiles:] 
# 			if currfileindex is not None:
# 				for f in filesToDelete:
# 					if f in currfileindex:
# 						continue
# 					os.remove(os.path.join(self.path, f))
# 			store, tiffs, indices = load_tif(self.path, self.filesNeeded, returnFormat=1)
# 			if len(tiffs) > self.maxfiles:
# 				raise Exception("Not enough storage allocated for this dataset")
		
# 		#update offset
# 		if self.chunk_type == "zstack":
# 			self.offset = [indices[0]]
# 		else:
# 			self.offset = [self.fileshape[0]*indices[0][0], self.fileshape[1]*indices[0][1], self.fileshape[2]*indices[0][2]]
# 			print(f"offset in update_store: {self.offset}")
# 			print(f"indices: {indices}")


			

# 		#downloaded is tiff:index pairs
# 		self.downloaded = {tiff:i for tiff,i in zip(tiffs, indices)}
# 		self.store = store
# 		self._shape = self.store._shape
# 		#get offset and curr pos
	
# 	def _get_store_index(self, og_key):
# 		'''
# 		subtracts offset from all elements of key
# 		then checks if key is in store (i.e. in downloaded list)
# 		if not, downloads required files and updates store
# 		returns key with offset subtracted
# 		'''
		
# 		key = self.shiftedKey(og_key)

# 		#check if key is in store
# 		toDownload = []
# 		filesNeeded, indices = self.filesFromKey(key)
# 		self.filesNeeded = [os.path.join(self.path, i.split("/")[-1]) for i in filesNeeded]

# 		for f in filesNeeded:
# 			if f not in self.downloaded.keys():
# 				toDownload.append(f)
# 		if len(toDownload) > 0:
# 			self._download_file(toDownload)
# 			self.update_store(filesNeeded)
# 			key = self.shiftedKey(og_key)
			
# 		return key
				
# 	def shiftedKey(self, key):
# 		shifted = [[i.start, i.stop] for i in key]
# 		for index, i in enumerate(shifted):
# 			if i[0] is None or i[1] is None or (self.chunk_type == "zstack" and index>0):
# 				continue
# 			shifted[index][0] = i[0] - self.offset[index]
# 			shifted[index][1] = i[1] - self.offset[index]
# 		return np.array([slice(*i) for i in shifted])

# 	def filesFromKey(self, key):#TODO
# 		'''
# 		converts key into list of files
# 		'''
# 		if self.chunk_type == "cuboid":
# 			normed = [[i.start, i.stop] for i in key]
# 			for index, i in enumerate(normed):
# 				if i[0] is None or i[1] is None:
# 					continue
# 				if index == 0:
# 					continue
# 				normed[index][0] = i[0]//self.fileshape[index]
# 				normed[index][1] = i[1]//self.fileshape[index]
# 			#get array of indices from slice
# 			indices = indices_from_slice([slice(*i) for i in normed])
# 		else:

# 			indices = [(i*10,) for i in range(key[0].start, key[0].stop)]

# 		#convert indices to filenames by using file_indices
# 		files = [self.indexFileDict[index] for index in indices]
# 		return files, indices
		

# 	def __getitem__(self, key):
# 		print(f"initial key: {key}")
# 		key = self._get_store_index(key)
# 		print(f"final key: {key}")
# 		data = self.store[*key]
# 		print(f"shape: {data.shape}")
# 		print(f"store shape: {self.store.shape}")
# 		return data

# 	def _download_file(self, filename):
# 		download_file(self.url, filename, self.username, self.password, self.path)

					
import numpy as np
import tifffile
import os

class RemoteZarr:
	def __init__(self, url, username, password, path, max_storage_gb=10, chunk_type="zstack"):
		self.url = url
		self.username = username
		self.password = password
		self.path = path
		file_list = np.array(list_files(url, username, password))
		if chunk_type == "zstack":
			self.file_list = tifffile.TiffSequence(file_list, pattern=r"(\d+).tif")
		else:
			self.file_list = tifffile.TiffSequence(file_list, pattern=r"cell_yxz_(\d+)_(\d+)_(\d+)")
		
		self.shape0 = self.file_list.shape

		self.file_indices = self.file_list.indices
		self.file_list = np.array(self.file_list.files)
		self.indexFileDict = {index:filename for index, filename in zip(self.file_indices, self.file_list)}
		self.downloaded = {}
		self.filesNeeded = [os.path.join(self.path, filename) for filename in self.file_list[:1]]

		self.chunk_type = chunk_type

		self.max_storage_gb = max_storage_gb
		#download first file to get shape and dtype
		self._download_file([self.file_list[0]])
		f = tifffile.imread(os.path.join(self.path, self.file_list[0]))
		self.fileshape = f.shape
		if chunk_type == "cuboid":
			self.fileshape = np.array([1, self.fileshape[0], self.fileshape[1]])
		self.filesize = f.nbytes
		self.dtype = f.dtype
		if chunk_type == "zstack":
			self.shape = np.array([self.shape0[0],self.fileshape[1], self.fileshape[0]])
		else:
			self.shape = np.array(self.fileshape)*np.array([self.shape0[2], self.shape0[0], self.shape0[1]])
		self.maxfiles = int(self.max_storage_gb*1e9/self.filesize)

		self.store = None

		self._shape = None #current shape of store

		self.chunks = None

		tiffs = [filename for filename in os.listdir(self.path) if filename.endswith(".tif")]
		# if len(tiffs) > 0:
		# 	self.update_store()
		# else:
		# 	firstSlice = self[0:1,:,:]


	def _get_store_index(self, og_key):
		'''
		subtracts offset from all elements of key
		then checks if key is in store (i.e. in downloaded list)
		if not, downloads required files and updates store
		returns key with offset subtracted
		'''
		keyArr = [[i.start, i.stop] for i in og_key]
		#key = self.shiftedKey(og_key)
		filesNeeded = []
		offsets = []
		if self.chunk_type == "cuboid":
			keyArr[1] = [keyArr[1][0]//500, keyArr[1][1]//500]
			keyArr[2] = [keyArr[2][0]//500, keyArr[2][1]//500]
			for i in range(keyArr[0][0], keyArr[0][1]+1):
				for j in range(keyArr[1][0], keyArr[1][1]+2):
					for k in range(keyArr[2][0], keyArr[2][1]+2):
						#pad with zeros
						ip = str(i+1).zfill(5)
						jp = str(j+1).zfill(3)
						kp = str(k+1).zfill(3)
						fname = f"cell_yxz_{jp}_{kp}_{ip}.tif"
						filesNeeded.append(fname)
						offsets.append([i,j, k])
		else:
			for i in range(keyArr[0][0], keyArr[0][1]+1):
				ip = str(i*10).zfill(5)
				fname = f"{ip}.tif"
				filesNeeded.append(fname)
				offsets.append(i)
		localFiles = [os.path.join(self.path, i) for i in filesNeeded]

		#check if files exist
		toDownload = []
		for findex,f in enumerate(localFiles):
			if not os.path.exists(f):
				toDownload.append(filesNeeded[findex])
		print(f"toDownload: {toDownload}")
		if len(toDownload) > 0:
			self._download_file(toDownload)
		
		store, tiffs, indices = load_tif(self.path, filesNeeded, returnFormat=1)
		self.store = store
		#find min of offsets in all dimensions
		#print(offsets)
		offset = np.min(np.array(offsets), axis=0)
		print(offset, "offset")
		#update og_key
		shifted = [[i.start, i.stop] for i in og_key]
		if self.chunk_type == "zstack":
			shifted[0] = [shifted[0][0] - offset, shifted[0][1] - offset]
			shifted_key = np.array([slice(*shifted[0])])
		else:
			shifted[0] = [shifted[0][0] - offset[0], shifted[0][1] - offset[0]]
			shifted[1] = [shifted[1][0] - offset[1]*500, shifted[1][1] - offset[1]*500]
			shifted[2] = [shifted[2][0] - offset[2]*500, shifted[2][1] - offset[2]*500]
			shifted_key = np.array([slice(*shifted[1]), slice(*shifted[2]), slice(*shifted[0])])
		return shifted_key






	def __getitem__(self, key):
		print(f"initial key: {key}")
		key = self._get_store_index(key)
		print(f"final key: {key}")
		data = self.store[*key]
		print(f"shape: {data.shape}")
		print(f"store shape: {self.store.shape}")
		#swap axes 0 and 2
		if self.chunk_type == "cuboid":
			data = np.swapaxes(data, 0, 2)
			data = np.swapaxes(data, 1, 2)
			data = data[::-1]
		return data

	def _download_file(self, filename):
		download_file(self.url, filename, self.username, self.password, self.path)

					




		


def load_tif(path, tiffs, returnFormat=0):
	"""This function will take a path to a folder that contains a stack of .tif
	files and returns a concatenated 3D zarr array that will allow access to an
	arbitrary region of the stack.

	We support two different styles of .tif stacks.  The first are simply
	numbered filenames, e.g., 00.tif, 01.tif, 02.tif, etc.  In this case, the
	numbers are taken as the index into the zstack, and we assume that the zslices
	are fully continuous.

	The second follows @spelufo's reprocessing, and are not 2D images but 3D cells
	of the data.  These should be labeled

	cell_yxz_YINDEX_XINDEX_ZINDEX

	where these provide the position in the Y, X, and Z grid of cuboids that make
	up the image data.
	"""
	# Get a list of .tif files
	
	if all([filename[:-4].isnumeric() for filename in tiffs]):
		# This looks like a set of z-level images
		tiffs.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))
		tiffs = [os.path.join(path, filename) for filename in tiffs]
		store = tifffile.imread(tiffs, aszarr=True)
		indices = range(len(tiffs))
		stack_array = zarr.open(store, mode="r")

	elif all([filename.startswith("cell_yxz_") for filename in tiffs]):
		# This looks like a set of cell cuboid images
		flist = [os.path.join(path, filename) for filename in tiffs]
		#flist = [os.path.join(path, filename) for filename in flist if filename.endswith(".tif")]
		stack_array, tiffs, indices = load_zarr(flist)
		print(f"stack_array shape: {stack_array.shape}", indices)
		
	
	if returnFormat == 0:
		return stack_array, tiffs
	elif returnFormat == 1:
		#strip path from tiffs
		tiffs = [os.path.basename(tiff) for tiff in tiffs]
		return stack_array, tiffs, indices

# def load_zarr(flist):
# 	# Use a defaultdict to store 2D arrays by their Z values
# 	groups = defaultdict(list)

# 	# Parse the filenames to get the indices and group by Z value
# 	for fname in flist:
# 		x, y, z = map(int, re.findall(r"cell_yxz_(\d+)_(\d+)_(\d+)", fname)[0])
# 		img = tifffile.imread(fname)
# 		groups[z].append((x, y, img, fname))


# 	# For each Z value, assemble the 2D image

# 	imgs_2d = []
# 	max_rows = max_cols = 0
# 	for z in sorted(groups.keys()):
# 		# Get list of (x, y, img) tuples and sort by x (col) and then y (row) values
# 		imgs = sorted(groups[z], key=lambda tup: (tup[0], tup[1]))
# 		print(f"imgs: {[img[3] for img in imgs]}")

# 		# Use np.hstack and np.vstack to assemble 2D image
# 		cols = []
# 		while imgs:
# 			# Collect all the images with the same x index
# 			current_x = imgs[0][0]
# 			same_col_imgs = [img for img in imgs if img[0] == current_x]
			
# 			# Remove the collected images from imgs list
# 			imgs = [img for img in imgs if img[0] != current_x]
			
# 			# Extract only the image data and vertically stack
# 			col = np.vstack([img[2] for img in same_col_imgs])
# 			cols.append(col)

# 		# Horizontally stack all the columns to form the 2D image
# 		img_2d = np.hstack(cols)
# 		max_rows = max(max_rows, img_2d.shape[0])
# 		max_cols = max(max_cols, img_2d.shape[1])
# 		imgs_2d.append(img_2d)



# 	# Pad the 2D images to have the same dimensions and stack to create 3D array
# 	padded_imgs = [np.pad(img, ((0, max_rows - img.shape[0]), (0, max_cols - img.shape[1]))) for img in imgs_2d]
# 	stack_array = np.dstack(padded_imgs)

# 	# Convert to Zarr array
# 	zarr_array = zarr.array(stack_array, chunks=True)

# 	# an ordered list of file names 
# 	tiffs = sorted(flist)

# 	# a corresponding list of indices
# 	indices = [tuple(map(lambda x: int(x) - 1, re.findall(r"cell_yxz_(\d+)_(\d+)_(\d+)", fname)[0])) for fname in tiffs]

# 	return zarr_array, tiffs, indices
def load_zarr(flist):
    groups = defaultdict(list)
    for fname in flist:
        y, x, z = map(int, re.findall(r"cell_yxz_(\d+)_(\d+)_(\d+)", fname)[0])
        img = tifffile.imread(fname)
        groups[z].append((x, y, img, fname))

    imgs_2d = []
    for z in sorted(groups.keys()):
        imgs = sorted(groups[z], key=lambda tup: (tup[0], tup[1]))
        cols = defaultdict(list)  # changed 'rows' to 'cols' here
        for x, y, img, _ in imgs:
            cols[x].append(img)  # changed 'rows' to 'cols' here

        for x in sorted(cols.keys()):
            cols[x] = np.concatenate(cols[x], axis=0)  # concatenate along y-axis
        
        img_2d = np.concatenate(list(cols.values()), axis=1)  # concatenate along x-axis
        imgs_2d.append(img_2d)

    stack_array = np.stack(imgs_2d, axis=2)
    zarr_array = zarr.array(stack_array, chunks=True)
    tiffs = sorted(flist)
    indices = [tuple(map(lambda x: int(x) - 1, re.findall(r"cell_yxz_(\d+)_(\d+)_(\d+)", fname)[0])) for fname in tiffs]

    return zarr_array, tiffs, indices




class Loader:
	"""Provides a cached interface to the data.
	
	When provided with z, x, and y slices, queries whether that
	data is available from any previously cached data.  If it
	is, returns the subslice of that cached data that contains
	the data we need.  
	
	If it isn't, then we:
	- clear out the oldest cached data if we need space
	- load the data we need, plus some padding
		- padding depends on the chunking of the zarr array and the
		  size of the data loaded
	- store that data in our cache, along with the access time.

	The cache is a dictionary, indexed by a namedtuple of
	slice objects (zslice, xslice, yslice), that provides a
	dict of 
	{"accesstime": last access time, "array": numpy array with data}
	"""

	def __init__(self, zarr_array, STREAM, chunk_type="zstack", max_mem_gb=5):
		self.shape = zarr_array.shape
		self.cache = {}
		self.zarr_array = zarr_array
		self.STREAM = STREAM
		self.max_mem_gb = max_mem_gb

		chunk_shape = self.zarr_array.chunks
		# if chunk_shape[0] == 1:
		# 	self.chunk_type = "zstack"
		# else:
		# 	self.chunk_type = "cuboid"
		self.chunk_type = chunk_type


	def _check_slices(self, cache_slice, new_slice, length):
		"""Queries whether a new slice's data is contained
		within an older slice.
		
		Note we don't handle strided slices.
		"""
		if isinstance(new_slice, int):
			new_start = new_slice
			new_stop = new_slice + 1
		else:
			new_start = 0 if new_slice.start is None else max(0, new_slice.start)
			new_stop = length if new_slice.stop is None else min(length, new_slice.stop)
		if isinstance(cache_slice, int):
			cache_start = cache_slice
			cache_stop = cache_slice + 1
		else:
			cache_start = 0 if cache_slice.start is None else cache_slice.start
			cache_stop = length if cache_slice.stop is None else cache_slice.stop
		if (new_start >= cache_start) and (new_stop <= cache_stop):
			# New slice should be the slice in the cached data that gives the request
			if isinstance(new_slice, int):
				return new_start - cache_start
			else:
				return slice(
					new_start - cache_start,
					new_stop - cache_start,
					None
				)
		else:
			return None

	def check_cache(self, zslice, xslice, yslice):
		"""Looks through the cache to see if any cached data
		can provide the data we need.
		"""
		for key in self.cache.keys():
			cache_zslice = hashable_to_slice(key[0])
			cache_xslice = hashable_to_slice(key[1])
			cache_yslice = hashable_to_slice(key[2])
			sub_zslice = self._check_slices(cache_zslice, zslice, self.shape[0])
			sub_xslice = self._check_slices(cache_xslice, xslice, self.shape[1])
			sub_yslice = self._check_slices(cache_yslice, yslice, self.shape[2])
			if sub_zslice is None or sub_xslice is None or sub_yslice is None:
				continue
			# At this point we have a valid slice to index into this subarray.
			# Update the access time and return the array.
			self.cache[key]["accesstime"] = time.time()
			return self.cache[key]["array"][sub_zslice, sub_xslice, sub_yslice]
		return None
	
	@property
	def cache_size(self):
		total_mem_gb = 0
		for _, data in self.cache.items():
			total_mem_gb += data["array"].nbytes / 1e9
		return total_mem_gb
	
	def empty_cache(self):
		"""Removes the oldest item in the cache to free up memory.
		"""
		if not self.cache:
			return
		oldest_time = None
		oldest_key = None
		for key, value in self.cache.items():
			if oldest_time is None or value["accesstime"] < oldest_time:
				oldest_time = value["accesstime"]
				oldest_key = key
		del self.cache[oldest_key]
	
	def estimate_slice_size(self, zslice, xslice, yslice):
		def slice_size(s, l):
			if isinstance(s, int):
				return 1
			elif isinstance(s, slice):
				s_start = 0 if s.start is None else s.start
				s_stop = l if s.stop is None else s.stop
				return s_stop - s_start
			raise ValueError("Invalid index")
		return (
			self.zarr_array.dtype.itemsize * 
			slice_size(zslice, self.shape[0]) *
			slice_size(xslice, self.shape[1]) * 
			slice_size(yslice, self.shape[2])
		) / 1e9

	def pad_request(self, zslice, xslice, yslice):
		"""Takes a requested slice that is not loaded in memory
		and pads it somewhat so that small movements around the
		requested area can be served from memory without hitting
		disk again.

		For zstack data, prefers padding in xy, while for cuboid
		data, prefers padding in z.
		"""
		def pad_slice(old_slice, length, int_add=1):
			
			if isinstance(old_slice, int):
				if length == 1:
					return old_slice
				return slice(
					max(0, old_slice - int_add),
					min(length,old_slice + int_add + 1),
					None
				)
			start = old_slice.start if old_slice.start is not None else 0
			stop = old_slice.stop if old_slice.stop is not None else length
			adj_width = (stop - start) // 2 + 1
			return slice(
				max(0, start - adj_width),
				min(length, stop + adj_width),
				None
			)
		est_size = self.estimate_slice_size(zslice, xslice, yslice)
		if (3 * est_size) >= self.max_mem_gb:
			# No padding; the array's already larger than the cache.
			return zslice, xslice, yslice
		if self.chunk_type == "zstack":
			# First pad in X and Y, then Z
			xslice = pad_slice(xslice, self.shape[1])
			est_size = self.estimate_slice_size(zslice, xslice, yslice)
			if (3 * est_size) >= self.max_mem_gb:
				return zslice, xslice, yslice
			yslice = pad_slice(yslice, self.shape[2])
			est_size = self.estimate_slice_size(zslice, xslice, yslice)
			if (3 * est_size) >= self.max_mem_gb:
				return zslice, xslice, yslice
			zslice = pad_slice(zslice, self.shape[0])
		elif self.chunk_type == "cuboid":
			# First pad in Z by 5 in each direction if we have space, then in XY
			zslice = pad_slice(
				zslice, 
				self.shape[0], 
				int_add=min(5, self.max_mem_gb // (2 * est_size))
			)
			est_size = self.estimate_slice_size(zslice, xslice, yslice)
			if (3 * est_size) >= self.max_mem_gb:
				return zslice, xslice, yslice
			xslice = pad_slice(xslice, self.shape[1])
			est_size = self.estimate_slice_size(zslice, xslice, yslice)
			if (3 * est_size) >= self.max_mem_gb:
				return zslice, xslice, yslice
			yslice = pad_slice(yslice, self.shape[2])
		return zslice, xslice, yslice

	def __getitem__(self, key):
		"""Overloads the slicing operator to get data with caching
		"""
		zslice, xslice, yslice = key
		for item in (zslice, xslice, yslice):
			if isinstance(item, slice) and item.step is not None:
				raise ValueError("Sorry, we don't support strided slices yet")
		# First check if we have the requested data already in memory
		result = self.check_cache(zslice, xslice, yslice)
		
		if result is not None:
			return result
		# Pad out the requested slice before we pull it from disk
		# so that we cache neighboring data in memory to avoid
		# repeatedly hammering the disk
		padded_zslice, padded_xslice, padded_yslice = self.pad_request(zslice, xslice, yslice)
		est_size = self.estimate_slice_size(padded_zslice, padded_xslice, padded_yslice)
		# Clear out enough space from the cache that we can fit the new
		# request within our memory limits.
		while self.cache and (self.cache_size + est_size) > self.max_mem_gb:
			self.empty_cache()
		padding = self.zarr_array[padded_zslice, padded_xslice, padded_yslice]
		self.cache[(
			slice_to_hashable(padded_zslice),
			slice_to_hashable(padded_xslice),
			slice_to_hashable(padded_yslice),
		)] = {
			"accesstime": time.time(),
			"array": padding,
		}
		

		result = self.check_cache(zslice, xslice, yslice)
		if result is None:
			# We shouldn't get cache misses!
			raise ValueError("Cache miss after cache loading")
		return result

def slice_to_hashable(slice):
	return (slice.start, slice.stop)

def hashable_to_slice(item):
	return slice(item[0], item[1], None)








def download_file(url, filenames, username, password, download_dir="."):
	# Send a request with basic authentication
	for filename in filenames:
		response = requests.get(url+filename, auth=(username, password), stream=True)
		
		# Check if the request was successful
		if response.status_code == 200:
			# Save the content to a file
			f_1 = filename.split("/")[-1]
			# if f_1.startswith("cell"):
			# 	filename = fixfname(filename)
			with open(f"{download_dir}/{filename}", "wb") as f:
				for chunk in response.iter_content(chunk_size=8192):
					f.write(chunk)
		else:
			print(f"Failed to download {url+filename}")

def list_files(url, username, password):
	# Send a request with basic authentication
	response = requests.get(url, auth=(username, password))
	
	# Check if the request was successful
	if response.status_code == 200:
		# Parse the HTML content
		soup = BeautifulSoup(response.text, "html.parser")
		
		# Find all the links
		links = soup.find_all("a")
		
		# Extract the href attribute and filter out the parent directory link
		files = [link.get("href") for link in links if link.get("href") != "../"]
		#remove files not ending in .tif
		files = [i for i in files if i.endswith(".tif")]
		
		return files
	else:
		return []

def indices_from_slice(slice_list):
	# Generate ranges for each dimension from the input slice objects
	ranges = [range(s.start, s.stop+1) for s in slice_list]

	# Initialize an empty list to store the index tuples
	index_tuples = []

	# Define a recursive function to generate index tuples from ranges
	def generate_tuples(current_tuple, depth):
		if depth == len(ranges):
			index_tuples.append(current_tuple)
		else:
			for index in ranges[depth]:
				generate_tuples(current_tuple + (index,), depth + 1)
	
	# Call the recursive function to generate index tuples
	generate_tuples((), 0)
	#rearange each tuple to be z,y,x
	index_tuples = [i[::-1] for i in index_tuples]

	return index_tuples




# class Volpkg(object):
# 	def __init__(self, folder, sessionId0):
# 		if folder.endswith(".volpkg") or os.path.exists(folder+".volpkg"):
# 			self.basepath = folder if folder.endswith(".volpkg") else folder+".volpkg"
# 			#get all volumes in the folder
# 			volumes = os.listdir(f"{self.basepath}/volumes")
# 			#remove hidden files
# 			volumes = [i for i in volumes if not i.startswith(".")]
# 			volume = volumes[0] #should switch to a dialog to select volume
# 			self.volume = volume
# 			self.img_array, self.tifstack = load_tif(f"{self.basepath}/volumes/{volume}")
# 			self.segmentations = None #TODO
# 		else:
# 			self.basepath = folder+".volpkg"
# 			#make volpkg folder
# 			os.mkdir(self.basepath)
# 			self.img_array, self.tifstack = load_tif(folder)
# 			#copy tifstack to volumes folder
# 			os.mkdir(f"{self.basepath}/volumes")
# 			#volume name
# 			os.mkdir(f"{self.basepath}/volumes/{sessionId0}")
# 			for i, tif in enumerate(self.tifstack):
# 				#use cp command
# 				os.system(f"cp {tif} {self.basepath}/volumes/{sessionId0}/{i}.tif")
			
# 			self.segmentations = None
			
# 	def saveVCPS(self, file_name, annotations, imshape, ordered=True, point_type='float', encoding='utf-8'):
# 		annotations = self.stripAnnoatation(annotations, imshape)
# 		#check if paths directory exists
# 		if not os.path.exists(self.basepath+"/paths"):
# 			os.mkdir(self.basepath+"/paths")
# 		#check if file_name directory exists
# 		if not os.path.exists(self.basepath+"/paths/"+file_name):
# 			os.mkdir(self.basepath+"/paths/"+file_name)
# 		file_path = f"{self.basepath}/paths/{file_name}/pointset.vcps"
# 		height, width, dim = annotations.shape
# 		header = {
# 			'width': width,
# 			'height': height,
# 			'dim': dim,
# 			'ordered': 'true' if ordered else 'false',
# 			'type': point_type,
# 			'version': '1'
# 		}

# 		with open(file_path, 'wb') as file:
# 			# Write header
# 			for key, value in header.items():
# 				file.write(f"{key}: {value}\n".encode(encoding))
# 			file.write("<>\n".encode(encoding))

# 			# Write data
# 			format_str = 'd' if point_type == 'double' else 'f'
# 			for i in range(height):
# 				for j in range(width):
# 					point = annotations[i, j]
# 					for value in point:
# 						file.write(struct.pack(format_str, value))
		
# 		#write meta.json {"name":"20230426114804","type":"seg","uuid":"20230426114804","vcps":"pointset.vcps","volume":"20230210143520"}
# 		meta = {
# 			"name": file_name,
# 			"type": "seg",
# 			"uuid": file_name,
# 			"vcps": "pointset.vcps",
# 			"volume": self.volume
# 		}
# 		with open(f"{self.basepath}/paths/{file_name}/meta.json", 'w') as file:
# 			json.dump(meta, file)


# 	def stripAnnoatation(self, annotationsRaw, imshape):
# 		interpolated = [i for i in annotationsRaw if len(i) > 0]

# 		H = len(interpolated)
# 		W = max([len(i) for i in interpolated])
# 		im = np.zeros((H, W*2, 3), dtype=np.float64)
# 		#replace all 0's with nan
# 		im[im == 0] = np.nan

# 		cy = H//2

# 		Center = interpolated[cy][len(interpolated[cy])//2]
# 		for i in range(len(interpolated)):
# 			if len(interpolated[i]) > 0:
# 				#find the center of the slice by finding the point with min distance from true center
# 				center = interpolated[i][0]
# 				centerIndex = 0
# 				for jindex, j in enumerate(interpolated[i]):
# 					if np.sqrt((j.x-Center.x)**2 + (j.y-Center.y)**2) < np.sqrt((center.x-Center.x)**2 + (center.y-Center.y)**2):
# 						center = j
# 						centerIndex = jindex
# 				#populate the image with the interpolated to the left and right of the center
				
# 				for jindex, j in enumerate(interpolated[i]):

# 					x,y = interpolated[i][jindex].x, interpolated[i][jindex].y
# 					x *= imshape[0]
# 					y *= imshape[1]
			
					
# 					im[i, W - (centerIndex-jindex)] = [x,y,i]
# 		return im

def fixfname(f):
	#remove .tif
	f = f[:-4]
	s = f.split("_")
	l2 = s[-3:-1]
	#prefix each with 2 extra zeros
	l2[0] = "00"+l2[0]
	l2[1] = "00"+l2[1]
	#join
	s[-3:-1] = l2
	#join
	f = "_".join(s)
	#add .tif
	f += ".tif"
	return f
