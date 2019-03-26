import os, shutil

target_folder = r'G:\ML\Big Data\task\OTH-M\all'

# go through all 20 dir.
for i in os.listdir('.'):
	if i not in ['all', 'mrg.py']:
		print('i', i)
		# go through all files, rename it (to avoid overwrite), & copy it in a folder.
		for file in os.listdir(i):
			print('file', file)
			os.rename(i + '/' + file, i + '/' + i + '_' + file)
			shutil.copy(i + '/' + file, target_folder)
