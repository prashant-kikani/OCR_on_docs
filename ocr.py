import time
from PIL import Image
import cv2
import pytesseract, os, re, itertools
import numpy as np

'''
TARGET:
MAWB Number, Overseas Agent, Port of Loading, Port of Discharge
Shipper, Consignee, Chargeable Weight, Product Description

'''

# Format is, key : a tuple. 1st element of tuple is bool showing whether its distributive word or not. 2nd item is, all the synonyms.
imp = {
	'awb': (False, ['awb', 'master', 'mawb', 'airway', 'bill']),
	'origin': (False, ['origin']),
	'destination': (False, ['destination']),
	'departure': (False, ['departure', 'loading', 'discharge']),
	'agent': (True, ['agent']),
	'shipper': (True, ['shipper', 'shpr']),
	'consignee': (True, ['consignee', 'cons']),
	'weight': (False, ['weight', 'kilo', 'kgs']),
	'discription': (True, ['discription']) 
}

rotate_thresh = 2

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
dirr = 'all'
n_img_to_try = 1														# Test run tesseract on these many randomly selected images from 200 images.

# Improvement: Do for each possible font to reduce time.
# Preprocessing on image : like thresholding on image. To check whether it improves performance or not.

# read img at given path
def read_img(img):
	'''
	img: PIL Image object

	returns:
	text in the img.
	'''
	text = pytesseract.image_to_string(img, lang='eng')
	text = re.sub(r'[^\x00-\x7F]+', '', text)                                  # remove non-ascii chars.
	return text.lower()

# search for a word in given sentences.
def search_for(words, sents, is_dis):
	'''
	word: word we need to search
	sents: List of all the sentences.

	returns:
	Howmany instances of word founded. Also prints results. 
	'''
	first, found = True, 0
	print('searching for' + '.' * 10 + words[0])
	for word in words:
		for ind, j in enumerate(sents):
			if word in j:
				print(j)
				found = 1
				# print(word, 'in:', j)
				if first:
					# print('relevent sentence(s) for ', word, ':')
					first = False
				if is_dis:
					print(*[x for x in sents[ind + 1 : ind + 4] if word not in x], sep = '\n')
					# print(*sents[ind : ind + 4], sep = '\n')
				else:
					print(*[x for x in sents[ind + 1 : ind + 2] if word not in x], sep = '\n')
					# print(*sents[ind : ind + 2], sep = '\n')
		if found == 1:
			break

	return found

# found all the words in the give text.
def found_it(text, imp):
	'''
	text: Text read by OCR
	imp: map of our search list.

	returns:
	total_found: total occurance founded
	sents: all the sentences.
	'''
	sents = re.split('\n', text)
	sents = list(filter(None, sents))
	clean_sents = []
	for i in sents:
		if re.search('[a-zA-Z0-9]', i):
			clean_sents.append(i)
	sents = clean_sents
	print(*sents, sep='\n')
	
	total_found = 0
	for k, v in imp.items():
		found = search_for(words = v[1], sents = sents, is_dis = k[0])
		total_found += found
	return total_found, sents


# Choose random images form 200 images & check results.
all_imgs = os.listdir(dirr)
for _ in range(n_img_to_try):
	ra_ind = np.random.randint(0, len(all_imgs))
	f = all_imgs[ra_ind]
	print(str(f) + "."*50)
	img = Image.open(dirr + '/' + f)
	text = read_img(img = img)
	total_found, sents = found_it(text, imp)	

	img.show()
	# Image might be rotated. So, try different angles.
	if total_found < rotate_thresh: 
		print('Failed to found more than 2. Rotating by 270')
		img1 = img.transpose(Image.ROTATE_270)
		text = read_img(img = img1)
		total_found, sents = found_it(text, imp)
		img1.show()

		if total_found < rotate_thresh:
			print('Again failed to found more than 2. Rotating by 90')
			img1 = img.transpose(Image.ROTATE_90)
			text = read_img(img = img1)
			total_found, sents = found_it(text, imp)
			img1.show()
			
			if total_found < rotate_thresh: 
				print('BAD QUALITY!') 
	
	words = [i.split() for i in sents]
	words = list(itertools.chain.from_iterable(words))   						# flatten




# To dictionary correct a word. i.e. find the closest matched word in the sentences. 
# Not used till now.
def sim_word(s):
    try:
        # brl = len(s)
        arr = []
        for _ in range(36):
            arr.append([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        # print('arr0',arr, len(arr))
        for c, i in enumerate(s):
            try:
                if i == '|':
                    ind = ord('i') - 97
                    arr[ind][0] += 1
                    arr[ind][arr[ind][0]] = c
                    continue
                if i != ' ':
                    if 57 >= ord(i) >= 48:                                                      # numbers
                        ind = ord(i) - 22                                                       # numbers
                        arr[ind][0] += 1
                        arr[ind][arr[ind][0]] = c
                        continue
                    ind = ord(i) - 97
                    arr[ind][0] += 1
                    arr[ind][arr[ind][0]] = c
            except IndexError:
                pass
        diffarr = []
        for i in brands_array:
            diff = 0
            for c, j in enumerate(i):
                for k, f in enumerate(j[1:]):
                    diff += abs(arr[c][k] - i[c][k])
            diffarr.append(diff)
        mini = 9999999
        mini_ind = -1
        for ind, i in enumerate(diffarr):
            if i < mini:
                mini = i
                mini_ind = ind
        return brands[mini_ind]
    except Exception as e:
        pass
        print("Color error : ", e)
