#TODO
#Set Wallpaper
#options:
#destination dir
#		update frequency(from reddit and wallpaper)
#		subreddit to fetch (validate input)
#		image ordering(random, latest, previous)
#		update image repo
#		change wallpaper 
#		both
#		add sub-reddit
#	remove sub-reddit
#	reset prefrences
#
#png and other formats support
#Select some image in the dir
#Add support for multiple desktops
#simplejson.scanner.JSONDecodeError: Expecting value: line 1 column 1 (char 0) no internet access


import requests, urllib2
import ctypes
import random
import os, platform
import string
import re
import argparse
import subprocess
import time

#from _winreg import *
from sys import executable
from os import path
#from pprint import pprint 
#import unicodedata

#EarthPorn/

#args parser
parser = argparse.ArgumentParser(description='Download images from a sub-reddit and store it in a given folder')
parser.add_argument('-d', '--dest', help="Destination of stored images",
					default='~/Pictures/')
#parser.add_argument('-l', '--link', help='''Link to the sub-reddit. 
					#Format:{http://www.reddit.com/r/xxxx/{xxx}/(nothing here)}''', 
					#default='http://www.reddit.com/r/earthporn/')
parser.add_argument('-o', '--ordering', help="The order in which next wallpaper will be set", 
					choices=['random', 'latest', 'previous'],
					default='random')
parser.add_argument('-r', '--image-rate', help="(Integral)Rate of image repo update(in hours), Range(0-2000)",
					type = int,
					default = 24)
parser.add_argument('-w', '--wallpaper-rate', help="(Integral)Rate of wallpaper update(in minutes), Range(0-21600)",
					type = int,
					default = 30)
parser.add_argument('-t', '--task', help="Update the images repo",
					choices=['update', 'change', 'both', 'none'],
					default = "both")
parser.add_argument('-a', '--add', help="add a subreddit")
args = parser.parse_args()

if args.image_rate not in range(0,2000) or args.wallpaper_rate not in range(0,21600):
	parser.print_help()
	exit(-1)

valid_chars = "-_.[]() %s%s" % (string.ascii_letters, string.digits)

last_file = '.last'
subreddit_file = '.subreddits'
bad_url_file = '.not jpg urls'
###first change ordering then change wallpaper

####DONE(not checked) delete last file if modified date more than 2 days before today

#Folder hadling
imgdir = args.dest
if platform.system() == 'Windows' and '~user' not in args.dest:
	imgdir = args.dest.replace('~','~user')
#fix this for windows 
imgdir = os.path.abspath(os.path.expanduser(imgdir)) 

x = '~user' if platform.system() == 'Windows' else '~'
home = os.path.expanduser(x)

if not os.path.isfile(path.join(home, subreddit_file)):
	with open(path.join(home, subreddit_file),'w') as f: 
		f.write('http://www.reddit.com/r/EarthPorn/')
	args.add = 'http://www.reddit.com/r/EarthPorn/'

#TODO check for duplicates
if args.add:
	if 'reddit' in args.add:
		args.add += '/' if not args.add.endswith('/') else ''
		x = args.add.index('/r/')
		subreddit = args.add[x+3:args.add.index('/', x+4)]
		directory = path.join(imgdir, subreddit)
		if not os.path.exists(directory):
			os.makedirs(directory)
			open(path.join(imgdir,bad_url_file), 'w').close()
		with open(path.join(home, subreddit_file),'a') as f: 
			f.write('\n' + args.add)

if args.task == 'update':
	update_repo = True
	change_wallpaper = False
elif args.task == 'change':
	change_wallpaper = True
	update_repo = False
elif args.task == 'none':
	change_wallpaper = False
	update_repo = False
else:
	update_repo = True
	change_wallpaper = True

#add url validation and extended support(weekly, monthly, etc)
#subreddit_link = args.link



#print os.path.abspath(__file__)
#print args.ordering
#print args.image_rate
#print args.wallpaper_rate
#print imgdir
#print subreddit_link


#print home + subreddit_file
ff = open(path.join(home, subreddit_file),'r')
lines = [line.strip() for line in ff]
imgdir_base = imgdir
subreddit_list = []
for subreddit_link in lines:
	x = subreddit_link.index('/r/')
	subreddit = subreddit_link[x+3:subreddit_link.index('/', x+4)]
	imgdir = os.path.join(imgdir_base,subreddit) 
	
	subreddit_list.append(subreddit)
	
	if update_repo:
		#Link id of the last image
		if os.path.isfile(path.join(imgdir,last_file)):
			x = time.time() - (os.path.getmtime(path.join(imgdir,last_file)))
			if x < 2*24*60*60:
				with open(path.join(imgdir,last_file),'r') as f: 
					last = f.read()
			else:
				last = ''
		else:
			last = ''
		print subreddit_link
		header={'user-agent':'my test application 1.0'}
		if last:
			r = requests.get(subreddit_link + '.json?limit=50&before=' + last,headers=header)
			#urllib2.urlopen(url).read()
		else:
			r = requests.get(subreddit_link + '.json?limit=20', headers=header)
		data = r.json()
		#pprint(data)

		#Retrieve all new images in reverse order(to get the last id in the var last_file)
		for post in reversed(data['data']['children']):
			
			f = open(path.join(imgdir,bad_url_file), 'a') 
			
			#make the filename valid 
			title = post['data']['title'].replace(' ', '_').replace('*', 'x')
			title = ''.join(c for c in title if c in valid_chars)[:250]
			#unicodedata.normalize('NFKD', title).encode('ascii','ignore')
			url = post['data']['url']
			
			#detect imgur album
			if 'imgur' in url and '/a/' in url:
				print "album :'( " 
				#use external script
				#continue
			#fix for urls with further args
			elif 'imgur' in url and '.jpg' in url:
				url = url[:url.index('.jpg') + 4]
				#print url
			#imgur page links fix
			elif 'imgur' in url and not url.endswith('.jpg'):
				url+= '.jpg'
			#flickr fix 
			elif 'flickr' in url:
				html = urllib2.urlopen(url).read()
				#try original
				img_url = re.findall(r'https:[^":]*_o\.jpg', html)
				#else fetch large
				if len(img_url) == 0:
					img_url = re.findall(r'https:[^":]*_b\.jpg', html)
				#if failed to find large's url
				if len(img_url) != 0:
					url = img_url[0].replace('\/', '/')
				#print url
			#check for pinned text posts
			if url.endswith('.jpg'):
				last = post['data']['name']
				#print url
				#print imgdir
				try:
					print title
					response=urllib2.urlopen(url)
					f_image = open(path.join(imgdir,title + '.jpg'),'wb')
					f_image.write(response.read())
					f_image.close()
					#Store the link id of the last image fetched for next use
					with open(path.join(imgdir,last_file),'w') as f: 
						f.write(last)
				except Exception:
					#import traceback
					#checksLogger.error('generic exception: ' + traceback.format_exc())
					print url
					f.write(url + '\n')
			else:
				f.write(url + '\n')

#do this only once
if change_wallpaper:
	#imgdir += 'EarthPorn/'
	imgs = []
	#extract all images downloaded by this program(improve this method)
	#find subdirs using listdir and use listdir on thos subdirs
	for paths, subdirs, files in os.walk(imgdir_base):
		#extract list of relevant subdirectories
		if paths == imgdir_base:
			sub = list(set(subdirs) & set(subreddit_list) )
		#combine to a common list, the files of revevant subdirs
		for d in sub:
			if paths == path.join(imgdir_base, d):
				for filename in files:
					imgs.append(path.join(paths, filename))
	random.seed()
	img = random.choice(imgs)
	while not img.endswith('.jpg'):
		img = random.choice(imgs)
	print imgdir + img
	if platform.system() == 'Windows':
		#Reg code only for win 8
		from _winreg import *
		subkey  = 'Software\\Microsoft\\Windows\\CurrentVersion\\Run'
		script  = os.path.abspath(__file__)
		pythonw = path.join(path.dirname(executable), 'pythonw.exe')
		hKey = OpenKey(HKEY_CURRENT_USER, subkey, 0, KEY_SET_VALUE)
		SetValueEx(hKey, 'MyApp', 0, REG_SZ, '"{0}" "{1}"'.format(pythonw, script))
		CloseKey(hKey)
		SPI_SETDESKWALLPAPER=20
		ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER,0, path.join(imgdir,img) ,0)
	elif platform.system() == 'Linux':
		desk_env = os.environ.get('DESKTOP_SESSION')
		if desk_env == 'kde-plasma':
			num = int(subprocess.check_output("kreadconfig --file kwinrc --group Desktops --key Number".split(" ")))
			x = num
			for n in range(12,25):
				if x > 0:
					s = 'kreadconfig --file plasma-desktop-appletsrc --group Containments --group ' + str(n)\
						+ ' --group Wallpaper --group image --key wallpaper'
					if subprocess.check_output(s.split(' ')).strip() != '':
						s = 'kwriteconfig --file plasma-desktop-appletsrc --group Containments --group ' + str(n)\
							+ ' --group Wallpaper --group image --key wallpaper ' + path.join(imgdir,img)
						print s
						subprocess.call(s.split(' '))
						x -= 1
						img = random.choice(imgs)
						while not img.endswith('.jpg'):
							img = random.choice(imgs)
						
			subprocess.call(['pkill', 'plasma-'])
			FNULL = open(os.devnull, 'w')
			subprocess.call(['plasma-desktop'], stdout=FNULL, stderr=FNULL)
		elif 'gnome' in desk_env.tolower():
			s = 'gsettings set org.gnome.desktop.background picture-uri ' + path.join(imgdir,img)
			subprocess.call(s.split(' '))
		elif 'mate' in desk_env.tolower():
			s = 'gconftool-2 -type string -set /desktop/gnome/background/picture_filename \"' + path.join(imgdir,img) + '\"'
			subprocess.call(s.split(' '))
		#elif 'xfce' in desk_env.tolower():
			#echo -e '# xfce backdrop list\n/path/to/image.png' > $HOME/.config/xfce4/desktop/backdrops.list 
			#xfdesktop --reload
			#print
		else:
			print 'get some other desktop-environment'
print 'done'
