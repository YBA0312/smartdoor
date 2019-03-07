#coding=utf8  

from picamera.array import PiRGBArray
import picamera
import cv2
import numpy as np

import serial

import requests
import json
import pymysql
import datetime
import time
import threading

import shutil
import os

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17,GPIO.OUT)
GPIO.setup(27,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(22,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.output(17,False)

key = "t-YPx***********************O0x5"
secret = "Esry***********************mevZR"
outer_id = "PiStudio"
url = 'https://api-cn.faceplusplus.com/facepp/v3/search'

fx=640#960#320#
fy=480#720#240#
#image = np.empty((fy * fx * 3,), dtype=np.uint8)
classfier = cv2.CascadeClassifier("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml")

def SQLread(com):
	db = pymysql.connect("101.*******0","root","0*****","pistudio" )
	sql = db.cursor()
	sql.execute(com)
	list=[]
	for res in sql.fetchall():
		list.append(res)
	sql.close()
	db.close()
	return list

def SQLwrite(com):
	db = pymysql.connect("101**********50","root","0****2","pistudio" )
	sql = db.cursor()
	try:
		sql.execute(com)
		db.commit()
	except Exception as e:
		db.rollback()
	sql.close()
	db.close()
	
def SQLsign(id):
	d1 = datetime.datetime.now()
	d2 = datetime.datetime(2018,7,28)
	day = (d1 - d2).days
	db = pymysql.connect("10********50","root","0*****","pistudio" )
	sql = db.cursor()
	sql.execute('select name,qq,lastsign,contsign,allsign from people join sign on people.id=sign.id where people.id='+str(id))
	for res in sql.fetchall():
		name = res[0]
		qq = res[1]
		lastsign = res[2]
		contsign = res[3]
		allsign = res[4]
	print(name)
	if ((d1 - datetime.timedelta(days = 1)).strftime("%Y-%m-%d"))==str(lastsign):
		contsign=contsign + 1
	else:
		contsign=0
	allsign = allsign + 1
	#print(str(d1.strftime("%Y-%m-%d")))
	try:
		sql.execute('UPDATE sign SET lastsign='+str(d1.strftime("%Y%m%d"))+',contsign='+str(contsign)+',allsign='+str(allsign)+' WHERE id='+str(id))
		db.commit()
	except Exception as e:
		db.rollback()
	if contsign>10:
		score=2
	elif contsign==0:
		score=1
	else:
		score=1+int(contsign)/10
	req = requests.post('http://10*********.50:5700/send_group_msg?access_token=0****2&group_id=379075373&message='+name+' 今日签到成功\n连续签到'+str(contsign+1)+'天 Score+'+str("%.1f" % score)+'\n出勤率'+str("%.2f" % (100*allsign/(day+1)))+'%')
	#print(req.text)
	addscore = SQLread('select score from score where id='+str(id))[0][0]+score
	try:
		sql.execute('UPDATE score SET score='+str(addscore)+' WHERE id='+str(id))
		db.commit()
	except Exception as e:
		db.rollback()
	sql.close()
	db.close()
	
def OPENDOOR():
	GPIO.output(17,True)
	time.sleep(3)
	GPIO.output(17,False)
	time.sleep(1)

def FACE():
	while 1:
		try:
			print('face start')
			camera = picamera.PiCamera()
			camera.resolution = (fx, fy)
			camera.rotation = 180
			camera.led = False
			camera.framerate = 32
			rawCapture = PiRGBArray(camera, size=(fx, fy))
			#camera.start_preview()
			#print("start\n")
			#camera.capture(image, format='bgr')
			for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
				image = frame.array
				#print("capture\n")
				#img = image.reshape((fy, fx, 3))
				#image = open('temp.jpg','rb')
				gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
				#print("gray\n")
				faces = classfier.detectMultiScale(gray, 1.2, 3, minSize=(int(fy/4), int(fy/4)), maxSize=(fy, fy))
				#print("cv\n")
				if len(faces) > 0 :
					for (x, y, w, h) in faces:
						#cv2.rectangle( image, ( x, y ), ( x + w, y + h ), ( 100, 255, 100 ), 2 )
						#cv2.putText( image, str( len( faces ) ), ( x, y ), cv2.FONT_HERSHEY_SIMPLEX, 0.5, ( 0, 0, 255 ), 2 )
						face = cv2.resize(gray[y:(y+h), x:(x+w)], (w, h))
						#print("write\n")
						nowday = time.strftime("%Y-%m-%d", time.localtime())
						nowtime = time.strftime("%H:%M:%S", time.localtime())
						if nowday not in os.listdir('/home/pi/facedata/pistudio/'):
							os.mkdir('/home/pi/facedata/pistudio/'+nowday)
						cv2.imwrite('/home/pi/facedata/pistudio/'+nowday+'/'+nowtime+'.jpg', face)
						#print("write over\n")
						req = requests.post(url=url, data={'api_key':key,'api_secret':secret,'outer_id':outer_id}, files={'image_file':open('/home/pi/facedata/pistudio/'+nowday+'/'+nowtime+'.jpg','rb')})
						#print("update\n")
						data=json.loads(req.text)
						if "error_message" not in data and "results" in data:
							if data["results"][0]["confidence"]>=data["thresholds"]["1e-5"]:
								OPENDOOR()
								id = SQLread('select id from face where token="'+data["results"][0]["face_token"]+'"',)
								if id != None:
									#opendoor.start()
									if SQLread('select * from j409 where id='+str(id[0][0])+' and date="'+nowday+'"',) == []:
										SQLsign(id[0][0],)
									SQLwrite('INSERT INTO j409(date,time,way,id) VALUES ("'+nowday+'","'+nowtime+'","face",'+str(id[0][0])+')',)
				'''
				cv2.imshow( "Frame", image )
				cv2.waitKey( 1 )
				'''
				rawCapture.truncate(0)
				#time.sleep(0.5)
		except:
			camera.stop_preview()
			print('face error')
			#requests.post('http://1*******  50:5700/send_group_msg?access_token=0*****&group_id=379075373&message='+str(e))
		
def FINGER():
	while 1:
		try:
			search = [0x3A,0x04,0xA6,0x80,0x00,0x04,0x1C,0x00,0x00,0x00,0x63,0x18]
			print("finger start")
			while 1:
				if GPIO.input(22) == True:
					print("finger on")
					ser = serial.Serial("/dev/ttyAMA0", 115200)
					ser.write(search)
					fd = ser.read(4)
					if fd[2]==0x00 and fd[3]==0x00:
						fd = ser.read(6)
						OPENDOOR()
						id = SQLread('select id from finger where num="'+str(fd[4])+'"',)
						nowday = time.strftime("%Y-%m-%d", time.localtime())
						nowtime = time.strftime("%H:%M:%S", time.localtime())
						if SQLread('select * from j409 where id='+str(id[0][0])+' and date="'+nowday+'"',) == []:
							SQLsign(id[0][0],)
						SQLwrite('INSERT INTO j409(date,time,way,id) VALUES ("'+nowday+'","'+nowtime+'","finger",'+str(id[0][0])+')',)
					ser.close()
				time.sleep(0.1)
		except:
			ser.close()
			print("finger error")

def SWITCH():
	while (1):
		if GPIO.input(27) == True:
			print('switch open')
			OPENDOOR()
		time.sleep(0.2)
opendoor = threading.Thread(target=OPENDOOR)
face = threading.Thread(target=FACE)
finger = threading.Thread(target=FINGER)
face.start()
#finger.start()
SWITCH()
