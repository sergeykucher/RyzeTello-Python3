import socket
import threading
import time

_LOCAL_ADDRESS_STATE = ('', 8890)
_LOCAL_ADDRESS_COMMAND_RESPONSE = ('',8889)
_TELLO_ADDRESS_COMMAND_RESPONSE = ('192.168.10.1', 8889)
_TELLO_VIDEO_STREAM = 'udp://@0.0.0.0:11111'
_TIMEOUT_RESPONSE = 2000 # in msec
_TIMEOUT_SLEEP = 10 # in sec
_FRAME_RATE = 30
_FRAME_WIDTH = 960
_FRAME_HEIGHT = 720
_FPS = 30

class RyzeTello():
    '''
    Class describes Ryze Tello interact
    Read Tello SDK fo more information at http://www.ryzerobotics.com
    No required argument
    Default optional arguments are:
    local_address_state = ('', 8890) - socket as tuple to receive Tello state
    local_address_command_response = ('',8889) - socket as tuple to receive Tello response
    tello_address_command_response = ('192.168.10.1', 8889) - socket as tuple to send Tello command
    tello_video_stream = 'udp://@0.0.0.0:11111' - ip address and port as str to receive Tello video stream
    timeout_response = 2000 - timeout in ms to wait response from Tello
    timeout_sleep = 10 - in sec to wait before sending 'command' to Tello
    frame_rate = 30 - frame rate of Tello video stream
    frame_width = 960 - frame width of Tello video stream
    frame_height = 720 - frame height of Tello video stream
    '''
    
    def __init__(self, local_address_state=_LOCAL_ADDRESS_STATE, local_address_command_response=_LOCAL_ADDRESS_COMMAND_RESPONSE,
                    tello_address_command_response=_TELLO_ADDRESS_COMMAND_RESPONSE,tello_video_stream=_TELLO_VIDEO_STREAM,
                    timeout_response=_TIMEOUT_RESPONSE,timeout_sleep=_TIMEOUT_SLEEP,
                    frame_rate=_FRAME_RATE,frame_width=_FRAME_WIDTH,frame_height=_FRAME_HEIGHT):
        self.__tello_state = {'pitch':'n/a','roll':'n/a','yaw':'n/a','vgx':'n/a','vgy':'n/a','vgz':'n/a',
                    'templ':'0','temph':'0','tof':'n/a','h':'n/a','bat':'0','baro':'n/a',
                    'time':'n/a','agx':'n/a','agy':'n/a','agz':'n/a'}
        self.__tello_response = ''

        self.local_address_state = local_address_state
        self.local_address_command_response = local_address_command_response
        self.tello_address_command_response = tello_address_command_response
        self.tello_video_stream = tello_video_stream
        self.timeout_response = timeout_response
        self.timeout_sleep = timeout_sleep
        self.frame_rate = frame_rate
        self.frame_width = frame_width
        self.frame_height = frame_height

        # Create a UDP sockets for receiving Tello state
        self.socket_state = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_state.bind(self.local_address_state)
        # Creating thread for receiving Tello state
        self.thread_tello_receive_state = threading.Thread(target=self.tello_receive_state)
        self.thread_tello_receive_state.start()
        print("Starting tello_receive_state thread")

        # Create a UDP sockets for command/response Tello
        self.socket_command_response = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_command_response.bind(self.local_address_command_response)
        # Creating thread for command/response Tello
        self.thread_tello_receive_response = threading.Thread(target=self.tello_receive_response)
        self.thread_tello_receive_response.start()
        print("Starting tello_receive_response thread")

        # Creating thread for wake Tello
        self.thread_tello_wake = threading.Thread(target=self.tello_wake)
        self.thread_tello_wake.start()
        print("Starting tello_wake thread")

    def tello_receive_state(self):
        '''
        Function receives and parses Tello state

        Example:
        “pitch:%d;roll:%d;yaw:%d;vgx:%d;vgy%d;vgz:%d;templ:%d;temph:%d;tof:%d;h:%d;bat:%d;baro:%.2f; time:%d;agx:%.2f;agy:%.2f;agz:%.2f;\r\n”
        Explanation:
            o pitch: Attitude pitch, degree
            o roll: Attitude roll, degree
            o yaw: Attitude yaw, degree
            o vgx: Speed x,
            o vgy: Speed y,http://www.ryzerobotics.com
            o vgz: Speed z,
            o templ: Lowest temperature, celcius degree
            o temph: Highest temperature, celcius degree
            o tof: TOF distance, cm
            o h: Height, cm
            o bat: Current battery percentage, %
            o baro: Barometer measurement, cm
            o time: Motors on time,
            o agx: Acceleration x,
            o agy: Acceleration y,
            o agz: Acceleration z,
        '''
        while not self.socket_state._closed: 
            try:
                state = self.socket_state.recv(1024)
                state_list = state.decode("utf-8")[:-3].split(';')
                self.__tello_state = dict([tuple(param.split(':')) for param in state_list])
            except Exception as ex:
                print ('Exception in tello_receive_state', ex)
        print ("Socket on {} port is closed. Exiting tello_receive_state...".format(self.local_address_state[1]))

    def get_tello_state(self):
        return self.__tello_state

    def tello_receive_response(self):
        '''
        Fuction receives response from Tello and assign it to variable tello_response
        Then print it in console
        '''
        while not self.socket_command_response._closed:
            try:
                response = self.socket_command_response.recv(1024)
                self.__tello_response = response.decode(encoding="utf-8")
                print(self.__tello_response)
            except OSError as os_error:
                print('Exception in tello_receive_response', os_error)
            except UnicodeDecodeError as decode_error:     
                print('Exception in tello_receive_response', decode_error)
            except Exception as ex:
                print('Exception in tello_receive_response', ex)
        print ("Socket on {} port is closed. Exiting tello_receive_response...".format(self.local_address_command_response[1]))

    def get_tello_response(self):
        return self.__tello_response

    def tello_send_command(self, command_to_tello='command'):
        '''
        Function send command to Tello and wait for response not more then timeout=3000 ms
        '''
        self.__tello_response = ''

        print(command_to_tello)
        try:
            self.socket_command_response.sendto(command_to_tello.encode(encoding="utf-8"), self.tello_address_command_response)
        except Exception as ex:
            print("Exception in tello_send_command", ex)
        timeout = self.timeout_response
        while not self.__tello_response:
            time.sleep(0.05)
            timeout -= 50
            if not timeout:
                print("Tello doesn't response to command '{}'.".format(command_to_tello))
                break

    def tello_wake(self):
        '''
        Function send 'command' to Tello every 10 sec
        '''
        while not self.socket_command_response._closed:
            try:
                self.tello_send_command()
                time.sleep(self.timeout_sleep)    
            except Exception as ex:
                print ('Exception in tello_wake', ex)
        print ("Socket on {} port is closed. Exiting tello_wake...".format(self.local_address_command_response[1]))

    def close(self):
        self.socket_state.close()
        self.socket_command_response.close()
