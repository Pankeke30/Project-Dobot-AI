import threading
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove, MyType,alarmAlarmJsonFile
from time import sleep
import numpy as np
import re
import cv2
import keyboard
import time

# 全局变量(当前坐标)
current_actual = None
algorithm_queue = None
enableStatus_robot = None
robotErrorState = False
globalLockValue = threading.Lock()

def ConnectRobot():
    try:
        ip = "192.168.0.11"
        dashboardPort = 29999
        movePort = 30003
        feedPort = 30004
        print("正在建立连接...")
        dashboard = DobotApiDashboard(ip, dashboardPort)
        move = DobotApiMove(ip, movePort)
        feed = DobotApi(ip, feedPort)
        print(">.<连接成功>!<")
        return dashboard, move, feed
    except Exception as e:
        print(":(连接失败:(")
        raise e

def RunPoint(move: DobotApiMove, point_list: list):
    move.MovL(point_list[0], point_list[1], point_list[2], point_list[3])

def GetFeed(feed: DobotApi):
    global current_actual
    global algorithm_queue
    global enableStatus_robot
    global robotErrorState
    hasRead = 0
    while True:
        data = bytes()
        while hasRead < 1440:
            temp = feed.socket_dobot.recv(1440 - hasRead)
            if len(temp) > 0:
                hasRead += len(temp)
                data += temp
        hasRead = 0
        feedInfo = np.frombuffer(data, dtype=MyType)
        if hex((feedInfo['test_value'][0])) == '0x123456789abcdef':
            globalLockValue.acquire()
            # Refresh Properties
            current_actual = feedInfo["tool_vector_actual"][0]
            algorithm_queue = feedInfo['isRunQueuedCmd'][0]
            enableStatus_robot=feedInfo['EnableStatus'][0]
            robotErrorState= feedInfo['ErrorStatus'][0]
            globalLockValue.release()
        sleep(0.001)

def WaitArrive(point_list):
    while True:
        is_arrive = True
        globalLockValue.acquire()
        if current_actual is not None:
            for index in range(4):
                if (abs(current_actual[index] - point_list[index]) > 1):
                    is_arrive = False
            if is_arrive :
                globalLockValue.release()
                return
        globalLockValue.release()  
        sleep(0.001)

def ClearRobotError(dashboard: DobotApiDashboard):
    global robotErrorState
    dataController,dataServo =alarmAlarmJsonFile()    # 读取控制器和伺服告警码
    while True:
      globalLockValue.acquire()
      if robotErrorState:
                numbers = re.findall(r'-?\d+', dashboard.GetErrorID())
                numbers= [int(num) for num in numbers]
                if (numbers[0] == 0):
                  if (len(numbers)>1):
                    for i in numbers[1:]:
                      alarmState=False
                      if i==-2:
                          print("机器告警 机器碰撞 ",i)
                          alarmState=True
                      if alarmState:
                          continue                
                      for item in dataController:
                        if  i==item["id"]:
                            print("机器告警 Controller errorid",i,item["zh_CN"]["description"])
                            alarmState=True
                            break 
                      if alarmState:
                          continue
                      for item in dataServo:
                        if  i==item["id"]:
                            print("机器告警 Servo errorid",i,item["zh_CN"]["description"])
                            break  
                       
                    choose = input("输入1, 将清除错误, 机器继续运行: ")     
                    if  int(choose)==1:
                        dashboard.ClearError()
                        sleep(0.01)
                        dashboard.Continue()

      else:  
         if int(enableStatus_robot[0])==1 and int(algorithm_queue[0])==1:
            dashboard.Continue()
      globalLockValue.release()
      sleep(5)

piece_coordinates = None

cap = cv2.VideoCapture(1)
       
if __name__ == '__main__':
    dashboard, move, feed = ConnectRobot()
    print("开始使能...")
    dashboard.EnableRobot()
    print("完成使能:)")
    feed_thread = threading.Thread(target=GetFeed, args=(feed,))
    feed_thread.setDaemon(True)
    feed_thread.start()
    feed_thread1 = threading.Thread(target=ClearRobotError, args=(dashboard,))
    feed_thread1.setDaemon(True)
    feed_thread1.start()
    print("循环执行...")
    #point_a = [312, 63, -60, 200]
    #point_b = [160, 260, -30, 170]
    dashboard.SpeedFactor(5)

    while True:

        ret, frame = cap.read()

        # Obtenemos las dimensiones del fotograma
        height, width, _ = frame.shape
        
        # Calculamos las coordenadas del centrom
        center_coordinates = (int(width / 2), int(height / 2))

        #print("Coordenadas del centro:", center_coordinates)
        
        # Dibujamos un círculo en el centro del fotograma
        cv2.circle(frame, center_coordinates, 5, (255, 255, 255), -1)

        # Convertir el frame de BGR a HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Definir el rango de colores a detectar en HSV
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
            
        # máscara para el color rojo y aplicarla al frame original
        mask = cv2.inRange(hsv, lower_red, upper_red)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            M = cv2.moments(max_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                piece_coordinates = (cx, cy)
                #print("Centro de la pieza:", piece_coordinates)
                cv2.circle(frame, piece_coordinates, 5, (255, 255, 255), -1)
                cv2.drawContours(frame, [max_contour], -1, (0,255,0), 2)


                # Calculamos la diferencia en píxeles entre el centroide y el centro
                diff_x = center_coordinates[0] - cx
                diff_y = center_coordinates[1] - cy
                #print("Diferencia en x:", diff_x)
                #print("Diferencia en y:", diff_y)

                point_a = [220, 12, -28, 200]
                #point_b = [160, 260, -30, 170]

                #RunPoint(move, point_a)############################
                #WaitArrive(point_a)############################3

                def coor():
                    print(point_a)


                xx = 0
                yy = 0

                xx += diff_x
                yy += diff_y
                xx,yy =yy,xx

                point_a[0] += xx
                point_a[1] += yy

                print('el valor es este: ')

                #RunPoint(move, point_a)
                #WaitArrive(point_a)

            

                keyboard.add_hotkey('m', coor())
                time.sleep(1)
            
        cv2.imshow('Original', frame)
        cv2.imshow('Mask', mask)

        

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        #break

        

    cap.release()
    cv2.destroyAllWindows()

    print('llegaste...................................................................')
    print(point_a)

    RunPoint(move, point_a)################
    WaitArrive(point_a)###################
