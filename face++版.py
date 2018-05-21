#coding=utf8  

'''
为了正确率及效率
这次使用了face++在线识别替代了opencv本地识别，露脸秒开门。
树莓派性能不足，识别效率太低，要在门口站半天。
其他外设可以自行增减
'''

import picamera	#树莓派摄像头
import cv2	#opencv
import numpy as np

import requests	#post
import json

import time
import thread	#多线程

import shutil	
import os	
import subprocess	#文件以及系统操作

import epd2in13	#墨水屏
epd = epd2in13.EPD()

import RPi.GPIO as GPIO	#树莓派GPIO操作
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(4,GPIO.IN)	#人体红外
GPIO.setup(17,GPIO.OUT)	#继电器-电机 MG995
GPIO.setup(18,GPIO.OUT)	#继电器-电机 MG995
GPIO.setup(27,GPIO.IN)	#霍尔传感器，电机圈数计数
GPIO.setup(22,GPIO.OUT)	#16路舵机控制器的使能控制
GPIO.setup(23,GPIO.IN)	#霍尔传感器，监测门是否开启
GPIO.output(17,True)
GPIO.output(18,True)

import Adafruit_PCA9685	#16路舵机控制器
pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(50)

from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.core import lib
from luma.oled.device import ssd1306	#OLED屏幕控制

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont	#图像处理相关

fx = 1024	#摄像头获取画面大小
fy = 768

image = np.empty((fy * fx * 3,), dtype=np.uint8)	#新建图片

classfier = cv2.CascadeClassifier("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml")	#使用haar分类器

angnowx = 50
angnowy = 100
angnowz = 130 	#初始化摄像头角度

faceup = False
rec = False
req = False
lock = False

ay = ["6b6858***************942df7aac37", "3f7470*************b1dd95ffc796b", "c4f731da******************73a57f81e"]
yba = ["f1571f*************b1efb3c94d"]
wjl = ["1d2a94dc9***********0bb0425c408d8a"]
rzs = ["b3c42d4b1************9e2f188ea649"]	#face++人脸集合

def turn(x, y, z)	#摄像头转向，xyz为角度
	if x > 180:
		x = 180
	elif x < 0:
		x = 0
	if y > 180:
		y = 180
	elif y < 0:
		y = 0
	if z > 180:
		z = 180
	elif z < 0:
		z = 0
	datex=int(4096*((x+0.5)*11+500)/(20000)+0.5)
	datey=int(4096*(((y+0.5)/2)*11+500)/(20000)+0.5)
	datez=int(4096*((z+0.5)*11+500)/(20000)+0.5)
	pwm.set_pwm(0, 0, datex)
	pwm.set_pwm(1, 0, datey)
	pwm.set_pwm(2, 0, datez)

def opendoor():	#开门
	global lock
	lock = True
	GPIO.output(17,False)
	GPIO.output(18,True)
	i = 0
	while i < 3:
		if GPIO.input(27) == 0:
			i = i + 1
			time.sleep(0.5)
		time.sleep(0.1)
	GPIO.output(17,True)
	GPIO.output(18,True)
	
def closedoor():	#关门
	global lock
	GPIO.output(17,True)
	GPIO.output(18,False)
	time.sleep(0.5)
	i = 0
	while i < 2:
		if GPIO.input(27) == 0:
			i = i + 1
			time.sleep(0.5)
		time.sleep(0.1)
	GPIO.output(17,True)
	GPIO.output(18,True)
	lock =False

def searchface(  face, bot):	#再使用face++判断人脸
	try:
		global faceup
		cv2.imwrite('/home/pi/facedata/temp.jpg', face)
		#thread.start_new_thread( show,("face", ))
		show("face")	#在屏幕上显示人脸
		payload = {'api_key': 't-YPx****************xeysvWbO0x5',
				   'api_secret': 'EsryaL**************bvAdypmevZR',
				   'outer_id': '1****8'}
		files = {'image_file': open('/home/pi/facedata/temp.jpg', 'rb')}
		r = requests.post('https://api-cn.faceplusplus.com/facepp/v3/search', files=files, data=payload)  
		data=json.loads(r.text)	#post
		if "error_message" not in data:	#判断数据
			if "results" in data:
				if data["results"][0]["face_token"] in wjl and data["results"][0]["confidence"]>=data["thresholds"]["1e-5"]:
					#print'卫家磊'
					#thread.start_new_thread( show,(u"卫家磊", ))
					show(u"卫家磊")
					opendoor()
					closedoor()
					bot.SendTo(g418, '卫家磊滚进了寝室')
					if time.strftime("%Y-%m-%d", time.localtime()) not in os.listdir('/home/pi/facedata/记录/成功/'):
						os.mkdir('/home/pi/facedata/记录/成功/'+time.strftime("%Y-%m-%d", time.localtime()))
					shutil.move('/home/pi/facedata/temp.jpg','/home/pi/facedata/记录/成功/'+time.strftime("%Y-%m-%d", time.localtime())+'/'+time.strftime("%H:%M:%S", time.localtime())+'小卫.jpg')	#以时间+名字保存照片
				elif data["results"][0]["face_token"] in rzs and data["results"][0]["confidence"]>=data["thresholds"]["1e-5"]:
					#print'饶子昇'
					#thread.start_new_thread( show,(u"饶子昇", ))
					show(u"饶子昇")
					opendoor()
					closedoor()
					bot.SendTo(g418, '饶子昇爬进了寝室')
					if time.strftime("%Y-%m-%d", time.localtime()) not in os.listdir('/home/pi/facedata/记录/成功/'):
						os.mkdir('/home/pi/facedata/记录/成功/'+time.strftime("%Y-%m-%d", time.localtime()))
					shutil.move('/home/pi/facedata/temp.jpg','/home/pi/facedata/记录/成功/'+time.strftime("%Y-%m-%d", time.localtime())+'/'+time.strftime("%H:%M:%S", time.localtime())+'子昇.jpg')
				elif data["results"][0]["face_token"] in yba and data["results"][0]["confidence"]>=data["thresholds"]["1e-5"]:
					#print'姚博岸'
					#thread.start_new_thread( show,(u"姚博岸", ))
					show(u"姚博岸")
					opendoor()
					closedoor()
					bot.SendTo(g418, '哦卡诶里纳赛，Master!')
					if time.strftime("%Y-%m-%d", time.localtime()) not in os.listdir('/home/pi/facedata/记录/成功/'):
						os.mkdir('/home/pi/facedata/记录/成功/'+time.strftime("%Y-%m-%d", time.localtime()))
					shutil.move('/home/pi/facedata/temp.jpg','/home/pi/facedata/记录/成功/'+time.strftime("%Y-%m-%d", time.localtime())+'/'+time.strftime("%H:%M:%S", time.localtime())+'博岸.jpg')
				elif data["results"][0]["face_token"] in ay and data["results"][0]["confidence"]>=data["thresholds"]["1e-5"]:
					#print'阿姨'
					#thread.start_new_thread( show,(u"阿姨", ))
					show(u"阿姨")
					opendoor()
					closedoor()
					bot.SendTo(g418, '阿姨突击了寝室')
					if time.strftime("%Y-%m-%d", time.localtime()) not in os.listdir('/home/pi/facedata/记录/成功/'):
						os.mkdir('/home/pi/facedata/记录/成功/'+time.strftime("%Y-%m-%d", time.localtime()))
					shutil.move('/home/pi/facedata/temp.jpg','/home/pi/facedata/记录/成功/'+time.strftime("%Y-%m-%d", time.localtime())+'/'+time.strftime("%H:%M:%S", time.localtime())+'阿姨.jpg')
				else:
					#print '未知生物'
					#thread.start_new_thread( show,(u"未知生物", ))
					show(u"未知生物")
					bot.SendTo(g418, '我寝遭到坏蜀黍偷窥')
					if time.strftime("%Y-%m-%d", time.localtime()) not in os.listdir('/home/pi/facedata/记录/失败/'):
						os.mkdir('/home/pi/facedata/记录/失败/'+time.strftime("%Y-%m-%d", time.localtime()))
					shutil.move('/home/pi/facedata/temp.jpg','/home/pi/facedata/记录/失败/'+time.strftime("%Y-%m-%d", time.localtime())+'/'+time.strftime("%H:%M:%S", time.localtime())+'.jpg')
			else:
				#print '未识别到有效人脸'
				#thread.start_new_thread( show,(u"再试一次", ))
				show(u"再试一次")
				if time.strftime("%Y-%m-%d", time.localtime()) not in os.listdir('/home/pi/facedata/记录/错误/'):
						os.mkdir('/home/pi/facedata/记录/错误/'+time.strftime("%Y-%m-%d", time.localtime()))
				shutil.move('/home/pi/facedata/temp.jpg','/home/pi/facedata/记录/错误/'+time.strftime("%Y-%m-%d", time.localtime())+'/'+time.strftime("%H:%M:%S", time.localtime())+'.jpg')
		else:
			print'错误'
			print r.text
			
	finally:
		faceup = False

def angle( angx, angy, angz):	#人脸跟踪角度计算
	global angnowx, angnowy, angnowz
	angx = angx*180/fx
	angy = angy*180/fy
	angz = angz*180/fx
	angnowx = angnowx - (90 - angx)/4
	angnowy = angnowy - (90 - angy)/4-abs(90-angnowx)/4
	angnowz = angnowz - (90 - angz)/4
	#print str(angnowx)+' '+str(angx)
	turn(angnowx, angnowy, angnowz)

def onrec(bot):	#先用opencv寻找人脸，截取人脸部分 先全图搜索，找到人脸后指定区域搜索减小计算时间
	global faceup, angnowx, angnowy, angnowz
	try:
		camera = picamera.PiCamera()
		camera.resolution = (fx, fy)
		camera.vflip = True
		camera.hflip = True
		angnowx = 50
		angnowy = 100
		angnowz = 130
		angx = fx/2
		angy = fy/2
		angz = fy/2
		x = 0
		y = 0
		w = fx
		h = fy
		num = 5
		GPIO.output(22,False)
		while rec:
			if num == 5:
				angnowx = 50
				angnowy = 100
				angnowz = 130
				turn(50, 40, 130)
				time.sleep(1)
				GPIO.output(22,True)
			camera.capture(image, format='bgr')
			img = image.reshape((fy, fx, 3))
			gray = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)[y:(y + h), x:(x + w)], (w, h))
			faces = classfier.detectMultiScale(gray, 1.2, 2, minSize=(fx/8, fx/8), maxSize=(h, h))
			if len(faces) > 0:
				num = 0
				GPIO.output(22,False)
				for (xx, yy, w, h) in faces:
					#print str(xx) + ' ' + str(yy) + ' ' + str(w) + ' ' + str(h)
					x = x + xx - int((w) * 0.2)
					y = y + yy - int((h) * 0.2)
					if x < 0:
						x = 0
					if y < 0:
						y = 0
					w = int((w) * 1.44)
					h = int((h) * 1.44)
					#print str(x) + ' ' + str(y) + ' ' + str(w) + ' ' + str(h) + '\n'
					if faceup == False:
						face = cv2.resize(img[y:(y + h), x:(x + w)], (w, h))
						faceup = True
						thread.start_new_thread( searchface, ( face, bot, ))
				angx = fx - (x + int(w/2))
				angy = fy - (y + int(h/2))
				angz = x + int(w/2)
				thread.start_new_thread( angle, ( angx, angy, angz, ))
			else:
				num = num + 1
				if  int(h * 1.44) < fy and x > int(w * 0.2) and y > int(h * 0.2):
					x = x - int(w * 0.2)
					y = y - int(h * 0.2)
					w = int(w * 1.44)
					h = int(h * 1.44)
				else:
					x = 0
					y = 0
					w = fx
					h = fy

	finally:
		try:
			camera.close()
			GPIO.output(22,False)
			datex=int(4096*(((95)*11)+500)/(20000)+0.5)
			datey=int(4096*500/(20000)+0.5)
			datez=int(4096*(((90)*11)+500)/(20000)+0.5)
			pwm.set_pwm(0, 0, datex)
			pwm.set_pwm(2, 0, datez)
			pwm.set_pwm(1, 0, datey)
			time.sleep(1)
		finally:
			GPIO.output(22,True)

def status(bot):	#判断摄像头及识别程序开启时机
	global rec
	while True:
		while GPIO.input(4) == False or GPIO.input(23):
			time.sleep(0.5)
			showtime()
		rec = True
		thread.start_new_thread( onrec,(bot, ))
		while GPIO.input(4) and GPIO.input(23) == False:
			time.sleep(1)
		rec = False
		if GPIO.input(23):
			if lock == False:
				bot.SendTo(g418, '结界被强行突破')
		show("main")
		time.sleep(2)

def onInit(bot):	#在qq机器人启动时加载
	thread.start_new_thread( status,(bot, ))
	epd.init(epd.lut_partial_update)
	#thread.start_new_thread( show,(1, ))
	show("main")

'''
from qqbot import qqbotsched
@qqbotsched(minute='5-55/10')
def request(bot):
	global req
	bot.SendTo(bot.List('buddy',"GA-17")[0], '请求确认存活', resendOn1202=False)
	t = 0
	while req==False:
		if t == 10:
			bot.SendTo(bot.List('buddy',"GA-17")[0], '请求确认存活', resendOn1202=False)
			t = 0
			break
		t = t+1
		time.sleep(0.5)
	while req==False:
		if t == 10:
			bot.SendTo(g418, '警告！与GA-17失去连接', resendOn1202=False)
			break
		t = t+1
		time.sleep(0.5)
	req = False
'''

def onQQMessage(bot, contact, member, content):	#在QQ机器人接收到消息时
	global req
	if content == "请求确认存活":
		time.sleep(1)
		bot.SendTo(contact, '收到请求')
	elif content == "收到请求":
		req = True
	elif content == "开门":
		if member == None:
			bot.SendTo(contact, '要在群里发哦~')
		elif member.nick == "不死鳥の守り" or member.card == "姚博岸":
			bot.SendTo(contact, '哦卡诶里纳赛，Master!')
			opendoor()
			closedoor()
		else:
			bot.SendTo(contact, '请说“主人我没脸开门”')
	elif content == "仅开门":
		if member == None:
			bot.SendTo(contact, '要在群里发哦~')
		elif member.nick == "不死鳥の守り" or member.card == "姚博岸":
			opendoor()
		else:
			bot.SendTo(contact, '你没权利命令我哦~')
	elif content == "仅关门":
		if member == None:
			bot.SendTo(contact, '要在群里发哦~')
		elif member.nick == "不死鳥の守り" or member.card == "姚博岸":
			closedoor()
		else:
			bot.SendTo(contact, '你没权利命令我哦~')
	elif content == "主人我没脸开门":
		if member == None:
			bot.SendTo(contact, '羞羞的事要在群里说哦~')
		elif member.nick == "你好，我叫小卫。" or member.card == "418 卫家磊":
			bot.SendTo(contact, '哼哼，谁让你总是欺负Master，就不给你开门，快说“博岸我错了”')
		else:
			opendoor()
			closedoor()
	elif content == "博岸我错了":
		if member.nick == "你好，我叫小卫。" or member.card == "418 卫家磊":
			opendoor()
			closedoor()
		else:
			bot.SendTo(contact, '你不欺负Master，不用道歉哦~')
	elif content == 'ip':
		response = requests.post('http://2018.ip138.com/ic.asp')
		ip = response.text
		ip = ip[ip.find('[')+1:ip.find(']')]
		#print(ip)
		bot.SendTo(contact, "这是我家的地址：", resendOn1202=False)
		bot.SendTo(contact, ip, resendOn1202=False)
	elif content == 'ip备用':
		response = requests.post('http://members.3322.org/dyndns/getip')
		ip = response.text
		#ip = ip.decode("utf8")
		#print(ip)
		bot.SendTo(contact, "我的外网IP是：", resendOn1202=False)
		bot.SendTo(contact, ip[:len(ip)-1], resendOn1202=False)
	elif '听我话' in content:
		sys = os.popen(content[content.find(' ')+1:]).readlines()
		sysstr = ""
		for s in sys:
			sysstr = sysstr + s
		bot.SendTo(contact, sysstr)

def onStartupComplete(bot):	#在qq机器人启动完成时
	global g418
	g418 = bot.List('group',  "1-418")[0]
	cs = bot.List('group',  "内部测试")[0]
	show("main")
	time.sleep(3)
	#thread.start_new_thread( showtime,())
	bot.SendTo(cs, 'Captain on the bridge,System启动完成')
	
def show(data):	#墨水屏显示部分
	if data == "main":
		epd.init(epd.lut_full_update)
		image = Image.open('/home/pi/图片/0014.jpg')
		image = image.resize((250,128),Image.ANTIALIAS)
		image = image.convert('1')
		draw = ImageDraw.Draw(image)
		font30 = ImageFont.truetype('/usr/share/fonts/ds.ttf', 30)
		font12 = ImageFont.truetype('/usr/share/fonts/cs.ttf', 12)
		font20 = ImageFont.truetype('/usr/share/fonts/cs.ttf', 20)
		draw.rectangle((150, 28, 250, 128), fill = 255)
		draw.text((160, 30), u'——by', font = font20, fill = 0)
		draw.text((160, 53), u'姚博岸', font = font30, fill = 0)
		draw.text((152, 100), u'QQ824381616', font = font12, fill = 0)
		image = image.transpose(Image.ROTATE_90)
		epd.set_frame_memory(image, 0, 0)
		epd.display_frame()
		epd.set_frame_memory(image, 0, 0)
		epd.display_frame()
	elif data == "face":
		epd.init(epd.lut_partial_update)
		image = Image.open('/home/pi/facedata/temp.jpg')
		image = image.resize((128,128),Image.ANTIALIAS)
		image = image.convert('1')
		image = image.transpose(Image.ROTATE_90)
		#image.save("/home/pi/2.png","PNG")
		epd.set_frame_memory(image, 0, 122)
		epd.display_frame()
		epd.set_frame_memory(image, 0, 122)
		epd.display_frame()
	else:
		epd.init(epd.lut_partial_update)
		image = Image.new('1', (122,128), 255)
		draw = ImageDraw.Draw(image)
		font22 = ImageFont.truetype('/usr/share/fonts/cs.ttf', 22)
		draw.text((10, 50), data, font = font22, fill = 0)
		image = image.transpose(Image.ROTATE_90)
		epd.set_frame_memory(image, 0, 0)
		epd.display_frame()
		epd.set_frame_memory(image, 0, 0)
		epd.display_frame()
	
def showtime():	#显示时间
	epd.init(epd.lut_partial_update)
	font = ImageFont.truetype('/usr/share/fonts/cs.ttf', 18)
	#epd.clear_frame_memory(0xFF)
	image = Image.new('1', (80, 25), 255)
	draw = ImageDraw.Draw(image)
	draw.text((0, 0), time.strftime("%H:%M:%S", time.localtime()), font = font, fill = 0)
	image = image.transpose(Image.ROTATE_90)
	epd.set_frame_memory(image, 0, 0)
	epd.display_frame()
	epd.set_frame_memory(image, 0, 0)
	epd.display_frame()

def onQrcode(bot, pngPath, pngContent):	#在获取到二维码时，显示在墨水屏上
	epd.init(epd.lut_partial_update)
	image = Image.open(pngPath)
	image = image.resize((99,99),Image.ANTIALIAS)
	image = image.transpose(Image.ROTATE_90)
	epd.set_frame_memory(image, 28, 0)
	epd.display_frame()
	epd.set_frame_memory(image, 28, 0)
	epd.display_frame()

def onExit(bot, code, reason, error):	#出错重启
	os.system('sudo reboot')
