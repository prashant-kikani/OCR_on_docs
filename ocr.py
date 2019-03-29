from PIL import Image
import cv2, shutil, time
import pytesseract, os, re, itertools
import numpy as np

'''
TARGET:
MAWB Number, Overseas Agent, Port of Loading, Port of Discharge
Shipper, Consignee, Chargeable Weight, Product Description

'''

# Format is, key : a tuple. 1st element of tuple is bool showing whether its distributive word or not. 2nd element is, all the synonyms.
imp = {
	'mawb': (False, ['mawb', 'master', 'awb', 'airway', 'bill']),
	'destination': (False, ['destination', 'dst', 'unloading']),
	'departure': (False, ['departure', 'loading', 'discharge', 'origin']),
	'agent': (True, ['agent']),
	'shipper': (True, ['shipper', 'shpr']),
	'consignee': (True, ['consignee', 'cons', 'consigned']),
	'weight': (False, ['weight', 'wght', 'g.w', 'kilo', 'kgs']),
	'discription': (True, ['discription', 'detail']) 
}

# Only using this if horizontal flipping is there.
# rotate_thresh = 1	# if less than this items found, then rotate image might be rotated. We rotate by 270 or 90 degree & try again.


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
dirr = 'all'
no_img_to_try = 1	# Test run of tesseract on these many randomly selected images from ACM 200 images.

# Improvement: Do for each possible font to reduce time.
# Preprocessing on image : like thresholding on image. To check whether it improves performance or not.

# read img at given path
def read_img(img):
	'''
	img: PIL Image object

	returns
	text in the img.
	'''
	text = pytesseract.image_to_string(img, lang='eng')
	text = re.sub(r'[^\x00-\x7F]+', '', text)	# remove non-ascii chars.
	return text.lower()

# search for a word in given sentences.
def search_for(words, sents, is_dis):
	'''
	word: word we need to search
	sents: List of all the sentences.
	is_dis: word is distripctive or not.

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
				if first:
					first = False
				if is_dis:
					print(*[x for x in sents[ind + 1 : ind + 3] if word not in x], sep = '\n')
					# print(*sents[ind : ind + 4], sep = '\n')
				else:
					print(*[x for x in sents[ind + 1 : ind + 3] if word not in x], sep = '\n')
					# print(*sents[ind : ind + 2], sep = '\n')
		if found == 1:
			break
	print()
	return found

# found all the words in the give text.
def found_it(text, imp):
	'''
	text: Text read by OCR
	imp: dictionary of our search list words.

	returns:
	total_found: total occurance founded
	sents: all the sentences from text.

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
		found = search_for(words = v[1], sents = sents, is_dis = v[0])
		total_found += found
	return total_found, sents

# Horizontal projection for detecting image is rotated or not.
def is_rotate(path):
	'''
	path: path of image

	return
	to rotate or not.
	'''
	img = cv2.imread(path, 0)
	print('img shape', img.shape)
	# Also one other method is hough transform.
	proj_h = np.sum(img, 1)			# horizontal projection
	proj_v = np.sum(img, 0)			# vertical projection

	print(proj_h.shape, proj_v.shape)
	std_h = proj_h.std() # / (img.shape[0])
	std_v = proj_v.std() # / (img.shape[0])
	print('std_h', std_h, 'std_v', std_v)
	if std_h > std_v:					# if std_h is more, image is okay. Otherwise we need to rotate it.
		return False
	return True

def pil_to_cv2gray(img1):
	'''
	img1: PIL Image 

	return
	openCV gray image
	'''
	pil_image = img1.convert('RGB')
	open_cv_image = np.array(pil_image)
	open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
	return open_cv_image


def dilate_erode(img):
	cv2.namedWindow('img', cv2.WINDOW_NORMAL)
	cv2.resizeWindow('img', 800,800)
	cv2.imwrite('img.jpg', img)
	cv2.imshow('img', img)
	
	# kernel = np.ones((5,5),np.uint8)
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 15)) # size of kernel differs image by image. if image is dense, size less, else large.
	dil = cv2.erode(img, kernel, iterations = 2) # no of iterations also depends on image.
	cv2.namedWindow('erode', cv2.WINDOW_NORMAL)
	cv2.resizeWindow('erode', 800,800)
	cv2.imwrite('mask.jpg', dil)
	cv2.imshow('erode', dil)

	_, contours, hierarchy = cv2.findContours(dil, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE) # cv2.RETR_EXTERNAL, cv2.RETR_TREE
	print('total contours:', len(contours))
	# print(contours)
	
	# make a dir if not, to save output contours. (i.e. TEXT CLUSTERS)
	if not os.path.exists('contours'):
		os.makedirs('contours')
	
	try:
		for f in os.listdir('contours'):
			os.remove('contours/' + f)
	except:
		pass

	# Crop TEXT CLUSTERS from original image & save it.
	for idx, c in enumerate(contours):
		x, y, w, h = cv2.boundingRect(c)
		if w > 60 and h > 30:
			new_img = img[y : y + h,x : x + w]
			cv2.imwrite('contours/' + str(idx) + '.png', new_img)

	cv2.drawContours(img, contours, -1, (0, 255, 0), 3)
	cv2.namedWindow('final', cv2.WINDOW_NORMAL)
	cv2.resizeWindow('final', 800,800)
	cv2.imwrite('contours.jpg', img)
	cv2.imshow('final', img)

	'''
	erd = cv2.erode(img, kernel, iterations = 1)
	cv2.namedWindow('erode', cv2.WINDOW_NORMAL)
	cv2.resizeWindow('dilate', 800,800)
	cv2.imshow('dilate', erd)
	tmp = cv2.dilate(img, kernel, iterations = 5)
	both = cv2.erode(tmp, kernel, iterations = 1)
	cv2.namedWindow('both', cv2.WINDOW_NORMAL)
	cv2.resizeWindow('both', 800,800)
	cv2.imshow('both', both)
	'''
	cv2.waitKey(0)


# Choose random images form 200 images & check results.
all_imgs = os.listdir(dirr)
for _ in range(no_img_to_try):
	ra_ind = np.random.randint(0, len(all_imgs))
	f = all_imgs[ra_ind]
	print(str(f) + "."*50)
	img_name = dirr + '/' + f
	img = cv2.imread(img_name, 0)
	dilate_erode(img)
	# '''
	rotate_ans = is_rotate(path = img_name)
	img = Image.open(img_name)
	if rotate_ans:
		img = img.transpose(Image.ROTATE_270)
		open_cv_image = pil_to_cv2gray(img)
		dilate_erode(open_cv_image)	# just to save text clusters.
	
	text = read_img(img = img)
	total_found, sents = found_it(text, imp)
	img.show()

	# Image might be rotated. So, try different angles.
	if total_found == 0: 		# if we didn't find anything
		if not rotate_ans:		# if std_h is higher than std_v, image must be 180 degree rotated
			img1 = img.transpose(Image.ROTATE_180)

			open_cv_image = pil_to_cv2gray(img1)

			dilate_erode(open_cv_image)
			text = read_img(img = img1)
			total_found, sents = found_it(text, imp)
			img1.show()
		else:					# if std_v is higher, we already have rotated by 270 degree, so it must be 90 degree rotated
			print('Failed to found more than 2. Image might be rotated. Rotating actual image by 90')
			img = Image.open(img_name)
			img1 = img.transpose(Image.ROTATE_90)

			open_cv_image = pil_to_cv2gray(img1)
			
			dilate_erode(open_cv_image)
			text = read_img(img = img1)
			total_found, sents = found_it(text, imp)
			img1.show()

		if total_found == 0: 
			print('BAD QUALITY!') 
	
	words = [i.split() for i in sents]
	words = list(itertools.chain.from_iterable(words))   						# flatten
	# all the word level work do here.
	# '''


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
