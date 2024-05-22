import rospy # ROS에서 지원하는 파이썬 패키지(라이브러리), ROS 파이썬 노드에 있는 것, 필요한 기본 기능을 import함
from geometry_msgs.msg import Twist

# geometry_msgs.msg 패키지에서 Twist로 import 함
# Twist 메시지는 로봇의 선속도(linear velocity)와 각속도(angular velocity)를 표현하는 데 사용

import sys, select, os

# import select
# 소켓 프로그래밍에서 I/O 멀티플렉싱을 가능하게 하는 모듈
# I/O 멀티플렉싱(multiplexing)이란 하나의 전송로로 여러 종류의 데이터를 송수신하는 방식
# 소켓 = 컴퓨터 네트워크에서 데이터를 주고받는 통로
# 소켓 프로그래밍 = 네트워크를 통해 통신하는 소프트웨어를 개발

if os.name == 'nt':
  import msvcrt, time
else:
  import tty, termios

BURGER_MAX_LIN_VEL = 0.22 
BURGER_MAX_ANG_VEL = 2.84 

WAFFLE_MAX_LIN_VEL = 0.26 # 와플 로봇의 최대 선형 속도를 초당 미터(m/s)로 정의, 로봇이 최대 0.26 미터/초의 속도로 직진 또는 후진할 수 있음
WAFFLE_MAX_ANG_VEL = 1.82 # 와플 로봇의 최대 각속도를 라디안/초(rad/s)로 정의,  로봇이 최대 1.82 라디안/초의 속도로 회전할 수 있음

LIN_VEL_STEP_SIZE = 0.01 # 선속도 (로봇이 직선 방향으로 얼마나 빠르게 움직이는지를 나타냄)
ANG_VEL_STEP_SIZE = 0.1  # 각속도 (로봇이 회전하는 속도)

# Turtlebot3 제어 하는 문자열
msg = """                           
Control Your TurtleBot3!
---------------------------
Moving around:
        w
   a    s    d
        x

w/x : increase/decrease linear velocity (Burger : ~ 0.22, Waffle and Waffle Pi : ~ 0.26)
a/d : increase/decrease angular velocity (Burger : ~ 2.84, Waffle and Waffle Pi : ~ 1.82)

space key, s : force stop

CTRL-C to quit
"""

e = """
Communications Failed
"""

# 특정 시간 동안 키보드 입력을 기다려서, 입력이 있으면 해당 키를 반환하고, 입력이 없으면 빈 문자열을 반환하는 기능
def getKey():
    if os.name == 'nt':
        timeout = 0.1 # 변수는 키 입력을 기다리는 시간을 제한하는 변수
        startTime = time.time() # 시작 시간 기록을 StartTime 변수에 넣음
        while(1):
            if msvcrt.kbhit(): # 키보드 입력이 있을 경우
                if sys.version_info[0] >= 3: # 파이썬 버전이 3 이상인 경우
                    return msvcrt.getch().decode()  # 바이트를 문자열로 디코딩 (입력된 키 반환)
                else: 
                    return msvcrt.getch() # 아닐경우 키를 바이트로 반환
            elif time.time() - startTime > timeout: # 키 입력 시간이 timeout 시간보다 크면 
                return '' # 빈 문자열 반환
            


    tty.setraw(sys.stdin.fileno()) # 'sys.stdin' = 표준 입력 스트림을 나타내는 객체 (입력된 데이터를 읽어들이는 데 사용)

    # 터미널을 raw(원시) 모드로 설정
    # raw 모드에서는 키 입력이 즉시 프로그램으로 전달
    # raw 모드에서는 이러한 버퍼링이 없고, 입력 시 발생하는 모든 키 이벤트를 읽을 수 있음

    # 읽을 수 있는 데이터가 있는지 확인하는 코드 (키 입력이 있는지 확인)
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)

    # 첫 번째 매개변수 = 읽을 준비가 된 파일 디스크립터 목록
    # 두 번째 매개변수 = 쓸 준비가 된 파일 디스크립터 목록
    # 세 번째 매개변수 = 예외 상황이 발생한 파일 디스크립터 목록
    # 네 번째 매개변수 = 최대 대기 시간

    # `rlist`에 `sys.stdin` 파일 디스크립터를 넣고, `select` 함수를 사용하여 0.1초 동안 읽을 준비가 된 파일 디스크립터 목록을 가져옴 
    # 만약 `rlist`에 `sys.stdin`이 포함되어 있다면, `sys.stdin`에서 읽을 수 있는 데이터가 있다는 뜻

    if rlist: # 'rlist'에 값이 있는 경우 (키 입력이 있는경우),  `select` 모듈에서 `sys.stdin` 파일 디스크립터를 반환했는지 확인
        key = sys.stdin.read(1) # 하나의 문자를 읽음
    else:
        key = ''  # `sys.stdin` 파일 디스크립터를 반환하지 않았을 때 실행, 키가 입력되지 않았으므로 `key` 변수에 빈 문자열을 할당

    # 터미널 입력 설정을 원래대로 복원
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

    # `tcsetattr` 함수는 터미널 속성을 설정하는 데 사용
    # `TCSADRAIN` 인수는 모든 출력 버퍼를 비우고 터미널 설정을 적용하는 데 사용
    # `settings` 변수는 원래의 터미널 입력 설정을 저장
    return key # 읽은 키 반환

#  두 개의 변수를 입력으로 받아들이고 문자열을 반환
def vels(target_linear_vel, target_angular_vel): # vels(선형 속도, 각속도)
    return "currently:\tlinear vel %s\t angular vel %s " % (target_linear_vel,target_angular_vel) # %s는 문자열 반환, linear과 angular에 각각 %s로 반환

# 입력값이 출력값보다 크다면, 출력값을 입력값에 가깝게 증가
# 입력값이 출력값보다 작다면, 출력값을 입력값에 가깝게 감소
# 출력값을 입력값과 가능한 한 가깝게 유지
def makeSimpleProfile(output, input, slop): # output = 함수의 출력 값, input = 함수의 입력 값, slop = 출력 값을 더하거나 뺄 허용 오차
    if input > output: # input 값이 더 크다면
        output = min( input, output + slop ) # input와 output + slop중 작은 값으로 output 변수에 할당
    elif input < output: # output 값이 더 크다면
        output = max( input, output - slop ) # input와 output - slop중 큰 값으로 output 변수에 할당
    else:
        output = input # output와 input 값이 같다면

    return output # output 리턴

# 속도가 일정 범위를 못넘어가는 함수    
# input 값이 low보다 작거나 high보다 큰 경우, 해당 값을 제한
def constrain(input, low, high): # input = 제한을 적용하려는 값, low = 하한 값, high = 상한 값
    if input < low:
      input = low
    elif input > high:
      input = high
    else:
      input = input

    return input

# 모델에 따라 선형 속도를 제한 (vel값을 로봇 모델에 따라 제한된 범위 내에서 유지, 벗어난 경우 해당 범위로 제한)
def checkLinearLimitVelocity(vel):
    if turtlebot3_model == "burger":
      vel = constrain(vel, -BURGER_MAX_LIN_VEL, BURGER_MAX_LIN_VEL)
    elif turtlebot3_model == "waffle" or turtlebot3_model == "waffle_pi": # 터틀봇3 모델이 waffle or waffle_pi 이면
      vel = constrain(vel, -WAFFLE_MAX_LIN_VEL, WAFFLE_MAX_LIN_VEL) 
      # 선형 속도 vel을 -WAFFLE_MAX_LIN_VEL{최대 선형속도(m/s)} ~ WAFFLE_MAX_LIN_VEL 사이의 값으로 제한

    else:
      vel = constrain(vel, -BURGER_MAX_LIN_VEL, BURGER_MAX_LIN_VEL)

    return vel

# 회전 속도 범위 체크 함수 (회전 속도 범위 제한, 허용 범위 조절)
def checkAngularLimitVelocity(vel):
    if turtlebot3_model == "burger":
      vel = constrain(vel, -BURGER_MAX_ANG_VEL, BURGER_MAX_ANG_VEL)
    elif turtlebot3_model == "waffle" or turtlebot3_model == "waffle_pi":
      vel = constrain(vel, -WAFFLE_MAX_ANG_VEL, WAFFLE_MAX_ANG_VEL)
      # 선형 속도 vel을 -WAFFLE_MAX_LIN_VEL{최대 각속도(rad/s)} ~ WAFFLE_MAX_LIN_VEL 사이의 값으로 제한
    else:
      vel = constrain(vel, -BURGER_MAX_ANG_VEL, BURGER_MAX_ANG_VEL)

    return vel

if __name__=="__main__":
    # 현재 스크립트{Python명령어로 이루어진 Python 프로그램 파일(확장자.py)로 직접 실행 가능한 Python 파일} 파일이 프로그램의 시작점이 맞는지 판단하는 작업
    # 즉, 스크립트 파일이 메인 프로그램으로 사용될 때와 모듈로 사용될 때를 구분하기 위한 용도
    # 인터프리터(명령어 한 줄씩 컴파일링)에서 직접 실행했을 경우에만 if문 내의 코드를 돌리라는 명령
    # (TMI)모듈 = 다른 모듈에 import 되는 Python 프로그램 파일
    # https://medium.com/@chullino/if-name-main-%EC%9D%80-%EC%99%9C-%ED%95%84%EC%9A%94%ED%95%A0%EA%B9%8C-bc48cba7f720

    # 윈도우가 아닐 경우 표준 입력 버퍼의 초기값을 저장합니다.
    if os.name != 'nt':
        settings = termios.tcgetattr(sys.stdin)

    rospy.init_node('turtlebot3_teleop')        
    # rospy가 정보를 가질 때까지 rospy에게 node의 이름을 말해주는 중요한 역할
    # ROS 노드 = ROS 시스템 내에서 작업을 수행하는 단위

    # 'cmd_vel'이라는 토픽에 Twist 메시지를 발행하는 퍼블리셔를 설정
    pub = rospy.Publisher('cmd_vel', Twist, queue_size=10) # 메세지를 발행(메시지를 특정 토픽에 보내는 동작)하는 역할
    # 'cmd_vel'이라는 토픽에 메시지를 발행하는 퍼블리셔를 생성 
    # (토픽 = ROS에서 메시지를 주고받는 메커니즘, publisher가 메세지를 전달하는 리소스, 서로 다른 노드간에 데이터를 주고 받음
    # 여기서는 이동 속도 명령을 전달하기 위한 토픽으로 사용)
    #  Twist는 ROS 메시지 유형을 나타내며, 이 메시지는 로봇의 선속도와 각속도를 포함
    #  queue_size=10은 퍼블리셔가 유지할 메시지 대기열의 최대 크기를 지정

    turtlebot3_model = rospy.get_param("model", "burger")

    # ROS 파라미터 서버에서 "model"이라는 파라미터 값을 가져옴
    # 만약 해당 파라미터가 존재하지 않으면 기본값으로 "burger"를 사용 (burger = 터틀봇의 모델)

    status = 0 # 터틀봇의 현재 상태를 나타내는 변수를 0으로 초기화
    target_linear_vel   = 0.0 # TurtleBot3의 목표 선형 속도를 0.0으로 초기화  ... 1
    target_angular_vel  = 0.0 # TurtleBot3의 목표 각속도를 0.0으로 초기화     ... 2
    control_linear_vel  = 0.0 # TurtleBot3의 제어 선형 속도를 0.0으로 초기화  ... 3
    control_angular_vel = 0.0 # TurtleBot3의 제어 각속도를 0.0으로 초기화     ... 4
    
    # 1, 2는 사용자가 TurtleBot3에게 원하는 속도를 지정하는 데 사용
    # 3, 4는 실제 속도를 제어하는 데 사용

    try: # 코드 실행중 발생할 수 있는 예외를 처리하기 위함
        print(msg) # Turtlebot3 제어 하는 문자열
        while not rospy.is_shutdown(): # ROS가 종료될 때까지 무한히 실행되는 루프  
            key = getKey() # 키보드에 입력받아 변수 'Key'에 할당
            if key == 'w' : 
                target_linear_vel = checkLinearLimitVelocity(target_linear_vel + LIN_VEL_STEP_SIZE) # Turtlebot의 목표 선속도
                # checkLinearLimitVelocity() 함수는 선형 속도를 제한 (허용 범위 조절)

                status = status + 1
                # 특정 동작이 수행될 때마다 status 값을 증가시키는 것, 해당 동작의 횟수를 세는 용도
                # 키보드 입력에 따라 터틀봇의 속도가 조정될 때마다 status 값을 1씩 증가

                print(vels(target_linear_vel,target_angular_vel))
                # 현재 설정된 target_linear_vel(선속도)와 target_angular_vel(각속도)를 출력

            elif key == 'x' :
                target_linear_vel = checkLinearLimitVelocity(target_linear_vel - LIN_VEL_STEP_SIZE)
                #  # checkLinearLimitVelocity() = 선속도를 제한하는 함수
                # target_linear_vel(현재 목표 선속도) -  LIN_VEL_STEP_SIZE(선속도 크기 0.01)

                status = status + 1
                print(vels(target_linear_vel,target_angular_vel)) # 현재의 선속도와 각 속도를 출력

            elif key == 'a' :
                target_angular_vel = checkAngularLimitVelocity(target_angular_vel + ANG_VEL_STEP_SIZE)
                # checkAngularLimitVelocity() = 각속도를 제한하는 함수
                # target_angular_vel(현재 목표 각속도) + ANG_VEL_STEP_SIZE(각속도 크기 0.1)

                status = status + 1
                print(vels(target_linear_vel,target_angular_vel)) 

            elif key == 'd' :
                target_angular_vel = checkAngularLimitVelocity(target_angular_vel - ANG_VEL_STEP_SIZE)
                # target_angular_vel(현재 목표 각속도) - ANG_VEL_STEP_SIZE(각속도 크기 0.1)

                status = status + 1
                print(vels(target_linear_vel,target_angular_vel))

                # 스페이스바나 s가 입력될 때 속도를 0으로 설정함
            elif key == ' ' or key == 's' : # 공백 or 's' 키가 눌러지면
                target_linear_vel   = 0.0 # TurtleBot3의 목표 선형 속도를 0.0으로 초기화 
                target_angular_vel  = 0.0 # TurtleBot3의 목표 각속도를 0.0으로 초기화   
                control_linear_vel  = 0.0 # TurtleBot3의 제어 선형 속도를 0.0으로 초기화  
                control_angular_vel = 0.0 # TurtleBot3의 제어 각속도를 0.0으로 초기화 
                print(vels(target_linear_vel, target_angular_vel)) # 현재의 선속도와 각 속도를 출력
            else:
                if (key == '\x03'): # Ctrl+C를 누르면 
                    break           # break문이 실행되어 반복문을 종료하여 프로그램을 종료

            if status == 20 : # status가 20일때
                print(msg)    # Turtlebot3 제어 하는 문자열을 출력
                status = 0    # status를 0으로 설정

            # 로봇의 선속도 및 각속도를 제어하는 코드, makeSimpleProfile 함수를 사용하여 
            # 제어 선속도 및 각속도를 목표 선속도 및 각속도에 도달할 때까지 조정
            # Twist 객체를 사용하여 로봇의 선형 및 회전 속도를 설정
            twist = Twist()
            # Twist 클래스의 새로운 객체를 생성 (인스턴스 생성)
            # Twist()는 로봇의 선속도와 각속도를 나타냄

            
            control_linear_vel = makeSimpleProfile(control_linear_vel, target_linear_vel, (LIN_VEL_STEP_SIZE/2.0))
            # makeSimpleProfile() 함수는 목표 선속도(target_linear_vel)에 도달하기 위해 제어 선속도(control_linear_vel)를 조정하는 함수
            # 즉, makeSimpleProfile() 함수를 호출하여 control_linear_vel 변수를 업데이트
            # (LIN_VEL_STEP_SIZE/2.0)은 제어 선속도를 목표 선속도에 도달할 때까지 얼마나 빠르게 조정할지를 결정하는 값 (속도 단계 크기)

            twist.linear.x = control_linear_vel # twist 객체의 linear.x 속성을 control_linear_vel로 설정하여 로봇의 x축 방향 선속도를 제어
            twist.linear.y = 0.0 # 로봇의 y축 방향 선속도를 0으로 설정
            twist.linear.z = 0.0 # 로봇의 z축 방향 선속도를 0으로 설정
            
            control_angular_vel = makeSimpleProfile(control_angular_vel, target_angular_vel, (ANG_VEL_STEP_SIZE/2.0))
            # makeSimpleProfile() 함수는 목표 각속도(target_angular_vel)에 도달하기 위해 제어 각속도(control_angular_vel)를 조정하는 함수
            # 즉, makeSimpleProfile() 함수를 호출하여 control_angular_vel 변수를 업데이트
            # (ANG_VEL_STEP_SIZE/2.0)은 제어 각(회전)속도를 목표 회전 속도에 도달할 때까지 얼마나 빠르게 조정할지를 결정하는 값

            twist.angular.x = 0.0  # 로봇의 x축 방향 각속도를 0으로 설정
            twist.angular.y = 0.0  # 로봇의 y축 방향 각속도를 0으로 설정
            twist.angular.z = control_angular_vel # twist 객체의 angular.z 속성을 control_angular_vel로 설정하여 로봇의 z축 방향 각속도를 제어

            pub.publish(twist) 
            # pub =  Publisher 객체, publish() 메서드 = Publisher 객체가 게시할 데이터를 인자로 받아서 해당 주제에 데이터를 발행하는 역할
            # pub.publish() = 발행할 메시지 객체를 인자로 받아 해당 토픽에 메시지를 발행
            # Twist 객체(twist)를 pub 객체의 publish() 메서드를 호출하여, 로봇에게 새로 계산된 선속도 및 각속도 메세지를 보냄


    except: # except Exception as e:
        print(e) # e는 예외 객체, 예외의 종류와 메시지, 그리고 예외가 발생한 위치 등의 정보가 포함되어 있긴 함

    finally: # 예외가 발생되더라도 무조건 실행되는 finally문
        twist = Twist() 
        # `finally` 블록 안에서 `Twist` 객체인 twist 생성 (인스턴스 생성)
        # Twist 객체는 선속도와 각속도를 나타내는 데 사용

        # 로봇을 멈추게 하는 역할
        twist.linear.x = 0.0; twist.linear.y = 0.0; twist.linear.z = 0.0    # Twist 객체의 선속도(x,y,z)를 모두 0으로 설정
        twist.angular.x = 0.0; twist.angular.y = 0.0; twist.angular.z = 0.0 # Twist 객체의 각속도(x,y,z)를 모두 0으로 설정
        pub.publish(twist)

    if os.name != 'nt': # 운영체제가 Windows가 아닌 경우에만 실행되도록 하는 조건
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

        # 터미널 입력 설정(tcsetattr)을 원래대로(이전 상태 settings) 복원 및 되돌림
        # `tcsetattr` 함수는 터미널 속성을 설정하는 데 사용
        # `TCSADRAIN` 인수는 모든 출력 버퍼를 비우고 터미널 설정을 적용하는 데 사용
        # `settings` 변수는 원래의 터미널 입력 설정을 저장