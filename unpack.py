import os
import magic
import rarfile
import tarfile
import gzip
import zipfile
import bz2

m = magic.Magic()
COMPRESS_TYPES = ["gzip", "bzip2"]
ARCHIVE_TYPES = ["Zip", "RAR", "POSIX tar"]

class upack_archives:

	def __init__(self, fname, output_dir=os.getcwd()):
		self.output_dir = output_dir
		self.base_name = self.get_base_name(fname)
		self.extract_dir = self.directory + "/" + self.base_name + "_extracted"
		self.make_directory(self.extract_dir)
		self.extract(self.extract_dir, fname)
	
	def get_base_name(self, fname):
		clean_name = fname
		if clean_name.rfind("/") >= 0:
			clean_name = clean_name[clean_name.rfind("/")+1:]
		if clean_name.find(".") >= 0:
			clean_name = clean_name[:clean_name.find(".")]
		return clean_name

	def make_directory(self, path)
		if not os.path.exists(path):
			os.makedirs(path)

	def extract(self, extract_path=self.extract_dir, fname):
		ftype = m.from_file(fname)	
		
		if any(t in ftype for t in COMPRESS_TYPES):
		
			if ftype.find("gzip") >= 0:
				ext = gzip.GzipFile(fname, 'rb')
			elif ftype.find("bzip2") >= 0:
				bz = bz2.BZ2File(fname, 'rb');
		
			filedata = ext.read()
			path = extract_path + "/" + fname + "_data"
			self.make_directory(path)	
			w = open(path_extract + "/feed_data","w")
			w.write(filedata)
			if not os.path.isdir(path_extract+"/feed_data") and not is_archived(path_extract+"/feed_data"):
				newname = get_base_name(fname)
				return os.rename(path_extract+"/feed_data", newname + ".xml")
		
		elif (t in ftype for t in ARCHIVE_TYPES):
			if ftype.find("RAR") >= 0:
				ext = rarfile.RarFile(fname)
			elif ftype.find("POSIX tar") >= 0:
				ext = tarfile.open(fname)
			elif ftype.find("Zip") >= 0:
				ext = zipfile.ZipFile(fname)
			ext.extractall(path=path_extract)
		else:
			return fname

		if fname.find(EXTRACT_PATH + "/") >= 0:
			os.remove(fname)
		flist = []
		for root, dirs, dirfiles in os.walk(path_extract):
			for name in dirfiles:
				flist.append(root + "/" + name)
		print str(flist)
		if len(flist) > 1:
			fname = extract_file(path, find_best_match(flist, fname))
		else:
			fname = extract_file(path, flist[0])
		return fname


	def largest_file():
	
	def find_best_match(name):

	def file_name_list():

	def get_directory():
		return self.directory
