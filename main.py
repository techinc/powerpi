import spidev as SPI
import ST7789
import time
import RPi.GPIO as GPIO
import DS18B20 as DS
from datetime import datetime
import socket
import os
import paho.mqtt.client as mqtt

import Image
import ImageDraw
import ImageFont
import ImageColor


broker_address='mqtt.ti'

sensor_root='sensorcloud/1'
sensor_name='powerpi'
voltage=240
json_sensor_template='{ epoch: "%d", sensor: "%s", value: "%s", unit: "%s" }'


ticks= 0
ticks_daily= 0
ticks_monthly= 0
instapower= 0
temp= 99.9
3
def unix_time(ttt):
    return((ttt- datetime(1970,1,1)).total_seconds())

def on_mqtt_connect(client, userdata, flags, rc):
    mqtt_client.publish("%s/%s/%s" % (sensor_root , sensor_name, "control"), sensor_name)

def send_mqtt_temp(ttt,temp):
    payload = json_sensor_template % ( unix_time(ttt), "temperature", str(temp),'celsius')
    mqtt_client.publish("%s/%s/%s" % (sensor_root , sensor_name, 'temp'), "[ %s ]" % ( payload ))

def send_mqtt_power(ttt, ticks, instapower):
    payload_ticks = json_sensor_template % (unix_time(ttt), "ticks" , str(ticks),'count')
    payload_power = json_sensor_template % (unix_time(ttt), 'power' , "%.3f" % (instapower*1000),'watt')
    payload_current = json_sensor_template % (unix_time(ttt), 'current', "%.3f" % (instapower*1000/voltage), 'Amperes')
    payload_consumed_power = json_sensor_template % (unix_time(ttt), 'consumed_power', "%.3f" % (0.001*ticks), 'kW/h')
    mqtt_client.publish("%s/%s/%s" % (sensor_root, sensor_name, 'power'), "[ %s , %s , %s , %s ]" % ( payload_ticks, payload_power, payload_current, payload_consumed_power))


mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_mqtt_connect
mqtt_client.connect(broker_address, 1883, 60)



def callback_edgedown(channel):
    global ticks
    ticks+= 1
    #print "puls"

def show_power():
    global disp, draw, image1, font40
    global ticks, ticks_daily, ticks_monthly
    draw.rectangle([(97,26),(239,65)], fill="WHITE")
    draw.text((97, 26), '{:06.3f}'.format(1.0*instapower), fill = "#00BF00", font=font40)
    draw.rectangle([(97,96),(239,135)], fill="WHITE")
    draw.text((97, 96), '{:06.2f}'.format(1.0*ticks_daily/1000), fill = "#00BFBF", font=font40)
    draw.rectangle([(97,166),(239,203)], fill="WHITE")
    draw.text((97, 166), '{:06.0f}'.format(1.0*ticks_monthly/1000), fill = "#BF00BF", font=font40)
    disp.ShowImage(image1,0,0)

def show_temp():
    global disp, draw, image1, font20, font40
    global temp, ttt
    draw.rectangle([(0,130),(95,169)], fill="WHITE")
    draw.text((0, 130), '{:4.1f}'.format(temp), fill = "#BF0000", font=font40)
    draw.rectangle([(0,180),(95,220)], fill="WHITE")
    draw.text((0, 180), '{:02.0f}:{:02.0f}:{:02.0f}'.format(ttt.hour, ttt.minute, ttt.second), fill = "#BFBF00", font=font20)
    draw.text((0, 201), '{:02.0f}-{:02.0f}-{:02.0f}'.format(ttt.day, ttt.month, ttt.year-2000), fill = "#BFBF00", font=font20)
    disp.ShowImage(image1,0,0)

def is_new_day(t1,t2):
    return t1.day!=t2.day

def is_new_month(t1,t2):
    return t1.month!=t2.month

# Raspberry Pi pin configuration:
RST = 27
DC = 25
BL =  18
bus = 0 
device = 0 
onewire = 4

sensors= DS.scan(onewire)

# 240x240 display with hardware SPI:
disp = ST7789.ST7789(SPI.SpiDev(bus, device),RST, DC, BL)

# Initialize library.
disp.Init()

# Clear display.
disp.clear()

# Setup interrupts
pinput= 5 
GPIO.setup(pinput,GPIO.IN,GPIO.PUD_UP)
#GPIO.setup(pinput,GPIO.IN,GPIO.PUD_DOWN)
#GPIO.add_event_detect(pinput,GPIO.RISING,callback=callback_edgedown,bouncetime=1)
GPIO.add_event_detect(pinput,GPIO.FALLING,callback=callback_edgedown,bouncetime=1)

# Create blank image for drawing.
image1 = Image.new("RGB", (disp.width, disp.height), "WHITE")
draw = ImageDraw.Draw(image1)
font20 = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 20)
fontip = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 15)
font40 = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 40)

try:
    gw= os.popen("ip -4 route show default").read().split(' ')
    my_ip= gw[6]
except:
    my_ip= '0.0.0.0'

draw.text((3, 220), 'TechInc PowerPi 0.1', fill = "#FF5733", font=font20)
draw.text((138, 4), 'now kW/h', fill = "#00BF00", font=font20)
draw.text((138, 74), 'today kW', fill = "#00BFBF", font=font20)
draw.text((138, 144), 'month kW', fill = "#BF00BF", font=font20)
draw.text((3, 107), 'temp C', fill = "#BF0000", font=font20)
draw.text((101, 205), my_ip, fill = "#3F3F3F", font=fontip)

rots= [0, 270, 180, 90]
angles= ['00','15','30','45','60','75']
images= []
for rot in rots:
    for angle in angles:
        image = Image.open('/home/pi/powerpi/logo96-'+angle+'.bmp')	
        images.append(image.rotate(rot))

disp.ShowAnimationInImage(image1,images, 1, 1)
show_power()

lasttt= ticktt= datetime.now()
lastticks= 0
print "starting main loop"
while 1:
    DS.pinsStartConversion([onewire])
    time.sleep(0.75)

    temp=26.1
    for i in sensors:
        temp= DS.read(False,onewire,i)
#    print temp
    ttt= datetime.now()
    show_temp()
    send_mqtt_temp(ttt,temp)
    if is_new_month( ttt, lasttt):
        ticks_monthly= 0
    if is_new_day( ttt, lasttt):
        ticks_daily= 0
        show_power()

    lasttt= ttt

    if lastticks!=ticks:
        # calc kw/h
        timedelta= (ttt-ticktt).total_seconds()
        instapower= (3.6*(ticks-lastticks))/timedelta
        #print instapower
        send_mqtt_power(ttt,ticks,instapower)
        disp.AnimateTickInImage()
        ticks_daily+= ticks-lastticks
        ticks_monthly+= ticks-lastticks
        curr_power= ticks
        lastticks= ticks
        show_power()
        ticktt= ttt

