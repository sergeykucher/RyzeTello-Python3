import ryze_tello

import pygame
import os
import cv2
import datetime
import threading

_DIR_SNAPSHOT = 'img'
_DIR_VIDEO = 'video'
_MAIN_WINDOW_CAPTION = 'DJI Ryze Tello Control'
_MAIN_WINDOW_X_Y = '310, 30'
_FILENAME_INTRO = 'tello.jpg'

class RyzeTelloUI:
    '''
    Class describes Ryze Tello User Interface
    Creating instance argument class RyzeTello required
    Default optional arguments are:
    dir_snapshot = 'img' - directory to save snapshots
    dir_video = 'video'- directory to save video records
    main_window_caption = 'DJI Ryze Tello Control' - main windows caption
    main_window_x_y = '310, 30' - main windows position (x,y) at start
    filename_intro = 'tello.jpg' - intro pic filename
    '''

    __FPS = 30
    __WHITE_COLOR = (255, 255, 255)
    __SILVER_COLOR = (192, 192, 192)
    __GRAY_COLOR = (128, 128, 128)
    __DARKGRAY_COLOR = (64, 64, 64)
    __RED_COLOR = (255, 0, 0)
    __BLUE_COLOR = (0, 0, 255)
    __BLACK_COLOR = (0, 0, 0)
    __FONT_NAME = 'Microsoft Sans Serif'

    def __init__(self, tello, dir_snapshot=_DIR_SNAPSHOT, dir_video=_DIR_VIDEO,
                main_window_caption=_MAIN_WINDOW_CAPTION, main_window_x_y=_MAIN_WINDOW_X_Y,
                filename_intro=_FILENAME_INTRO):

        self.is_recording = False
        self.is_recording_stop = False
        self.is_snapshortting = False
        self.is_broadcasting = False

        self.tello = tello
        self.dir_snapshot = dir_snapshot
        self.dir_video = dir_video
        self.main_window_caption = main_window_caption
        os.environ['SDL_VIDEO_WINDOW_POS'] = main_window_x_y
        self.filename_intro = filename_intro
        
        pygame.init()
        self.tello_ui = pygame.display.set_mode((self.tello.frame_width + 20, self.tello.frame_height + 100))
        pygame.display.set_caption(self.main_window_caption)
        self.surf_rec_indicator = pygame.Surface((100, 40))
        self.surf_rec_indicator.set_colorkey(self.__BLACK_COLOR)
        self.surf_video = pygame.Surface((self.tello.frame_width, self.tello.frame_height))
        self.surf_state = pygame.Surface((self.tello.frame_width + 20, 100))
    
        self.start = self.intro_window()
        if self.start:
            self.main_window()

    def button(self,text_button,x_button,y_button,width_button,height_button,inactive_color,active_color):
        '''
        Draw button with given parameters
        Return True if clicked
        '''
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if x_button+width_button > mouse[0] > x_button and y_button+height_button > mouse[1] > y_button:
            pygame.draw.rect(self.tello_ui, active_color,(x_button,y_button,width_button,height_button))
            if click[0] == 1:
                return True
        else:
            pygame.draw.rect(self.tello_ui, inactive_color,(x_button,y_button,width_button,height_button))
        font = pygame.font.SysFont(self.__FONT_NAME,20, bold=1)
        text = font.render(text_button, True, self.__BLACK_COLOR)
        rect = text.get_rect()
        rect.center = ((x_button+(width_button//2)), (y_button+(height_button//2)))
        self.tello_ui.blit(text, rect)
        pygame.display.flip()

    def intro_window(self):
        '''
        Intro window
        '''
        self.tello_ui.fill(self.__BLACK_COLOR)
        font = pygame.font.SysFont(self.__FONT_NAME, 32)
        text = font.render(self.main_window_caption,True,self.__WHITE_COLOR)
        text_rect = text.get_rect(center=((self.tello.frame_width+20)//2, 40))
        self.tello_ui.blit(text, text_rect)
        image = pygame.image.load(self.filename_intro)
        self.surf_image = pygame.Surface(image.get_size())
        for transparency in range (0,255,2):
            self.surf_image.fill(self.__BLACK_COLOR)
            image.set_alpha(transparency)
            self.surf_image.blit(image,(0,0))
            self.tello_ui.blit(self.surf_image,((10, 100)))
            pygame.display.flip()
        font = pygame.font.SysFont(self.__FONT_NAME, 16)
        text = font.render("Control keys:",True,self.__SILVER_COLOR)
        self.tello_ui.blit(text, (140, 560))
        text = font.render("'Q' - Takeoff        SPACE - Land",True,self.__SILVER_COLOR)
        self.tello_ui.blit(text, (140, 580))
        text = font.render("UP - Move forward    DOWN - Move back    LEFT - Turn left    RIGHT - Turn right",True,self.__SILVER_COLOR)
        self.tello_ui.blit(text, (140, 600))
        text = font.render("'W' - Move up          'S' - Move down          'A' - Shift left          'D' - Shift right",True,self.__SILVER_COLOR)
        self.tello_ui.blit(text, (140, 620))
        text = font.render("F1 - Start record      F2 - Stop record      F3 - Take snapshot      F10 - Restart video",True,self.__SILVER_COLOR)
        self.tello_ui.blit(text, (140, 640))
        pygame.display.flip()
        
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT:
                    self.tello.close()
                    return False
            start = self.button("Start",300,700,100,50,self.__DARKGRAY_COLOR,self.__SILVER_COLOR)
            if start:
                return True
            bye = self.button("Quit",580,700,100,50,self.__DARKGRAY_COLOR,self.__SILVER_COLOR)
            if bye:
                self.tello.close()
                return False
            clock.tick(self.__FPS)

    def seek_key_send_command(self,keys):
        '''
        Seek command in configuration schema and send it to Tello
            pygame.K_q      :   "takeoff",
            pygame.K_SPACE  :   "land",
            pygame.K_UP     :   "forward 50",
            pygame.K_DOWN   :   "back 50",
            pygame.K_LEFT   :   "ccw 30",
            pygame.K_RIGHT  :   "cw 30",
            pygame.K_w      :   "up 50",
            pygame.K_s      :   "down 50",
            pygame.K_a      :   "left 50",
            pygame.K_d      :   "right 50"
        '''
        if keys[pygame.K_q]:
            self.tello.tello_send_command("takeoff")
            return
        if keys[pygame.K_SPACE]:
            self.tello.tello_send_command("land")
            return
        if keys[pygame.K_UP]:
            self.tello.tello_send_command("forward 50")
            return
        if keys[pygame.K_DOWN]:
            self.tello.tello_send_command("back 50")
            return
        if keys[pygame.K_LEFT]:
            self.tello.tello_send_command("ccw 30")
            return
        if keys[pygame.K_RIGHT]:
            self.tello.tello_send_command("cw 30")
            return
        if keys[pygame.K_w]:
            self.tello.tello_send_command("up 50")
            return
        if keys[pygame.K_s]:
            self.tello.tello_send_command("down 50")
            return
        if keys[pygame.K_a]:
            self.tello.tello_send_command("left 50")
            return
        if keys[pygame.K_d]:
            self.tello.tello_send_command("right 50")
            return

    def broadcast_init(self):
        '''
        Initialize brodcasting
        '''
        self.tello.tello_send_command('streamon')
        try:
            self.tello_stream = cv2.VideoCapture(self.tello.tello_video_stream)
        except Exception as ex:
            print("Exception opening cv2.VideoCapture instance", ex)
        if not self.is_broadcasting:
            self.thread_tello_video_broadcast = threading.Thread(target=self.tello_video_broadcast)
            self.thread_tello_video_broadcast.start()

    def tello_video_broadcast(self):
        '''
        Read Video stream from Tello and broadcast it in Pygame window
        If is_snapshortting = True - take snapshort
        If is_recording = True - record video from Tello
        '''
        self.is_broadcasting = True
        while self.tello_stream.isOpened():
            try:
                ret, frame = self.tello_stream.read()
                if ret:
                    if self.is_snapshortting:
                        self.take_snapshot(frame)
                        self.is_snapshortting = False
                    if self.is_recording:
                        self.video_writer_file.write(frame)
                    if self.is_recording_stop:
                        self.video_writer_file.release()
                        self.is_recording = False
                        self.is_recording_stop = False
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = frame.swapaxes(0,1)
                    frame = pygame.surfarray.make_surface(frame)
                    self.surf_video.blit(frame, (0,0))
                    self.tello_ui.blit(self.surf_video, (10,0))
                    if self.is_recording:
                        self.draw_rec_indicator()
                pygame.display.flip()
            except Exception as ex:
                print ('Exception in tello_video_broadcast ',ex)
        print('Exiting tello_video_brodcast')
        self.is_broadcasting = False

    def print_tello_state(self, **kwargs):
        '''
        Print Tello state
        State is printed in WHITE_COLOR if received from Tello
        Otherwise print last state in BLUE_COLOR
        Optional parameters are available for Battery, Lowest temperature and Highest temperature:
        bat=<value>, templ=<value>, temph=<value>
        if you want it to be printed in RED_COLOR when danger 
        '''
        TELLO_STATE_TEMPLATE = {'pitch':    ["Attitude pitch {} degree    ",(40, 5)],
                                'roll' :    ["Attitude roll  {} degree    ",(40, 20)],
                                'yaw'  :    ["Attitude yaw   {} degree    ",(40, 35)],
                                'vgx'  :    ["Speed x        {} m/s       ",(40, 50)],
                                'vgy'  :    ["Speed y        {} m/s       ",(40, 65)],
                                'vgz'  :    ["Speed z        {} m/s       ",(40, 80)],
                                'templ':    ["Lowest temperature  {} °C   ",(330, 5)],
                                'temph':    ["Highest temperature {} °C   ",(330, 20)],
                                'tof'  :    ["TOF distance   {} cm    ",(330, 35)],
                                'h'    :    ["Height         {} cm    ",(330, 50)],
                                'bat'  :    ["Current battery percentage {} %     ",(330, 65)],
                                'baro' :    ["Barometer measurement  {} cm   ",(660, 5)],
                                'time' :    ["Motors on time   {}    ",(660, 20)],
                                'agx'  :    ["Acceleration x   {}    ",(660, 35)],
                                'agy'  :    ["Acceleration y   {}    ",(660, 50)],
                                'agz'  :    ["Acceleration z   {}    ",(660, 65)]}
        self.surf_state.fill(self.__BLACK_COLOR)
        font = pygame.font.SysFont(self.__FONT_NAME, 14)
        response = self.tello.get_tello_response()
        text_color = self.__WHITE_COLOR if response else self.__BLUE_COLOR
        state = self.tello.get_tello_state()
        for key in state:
            dangerous_value = False
            if key in kwargs:
                if key == 'bat' and int(state[key]) < kwargs[key]:
                    dangerous_value = True
                if key == 'templ' and int(state[key]) > kwargs[key]:
                    dangerous_value = True
                if key == 'temph' and int(state[key]) > kwargs[key]:
                    dangerous_value = True
            if dangerous_value:        
                text = font.render(TELLO_STATE_TEMPLATE[key][0].format(state[key]),True,self.__RED_COLOR)
            else:
                text = font.render(TELLO_STATE_TEMPLATE[key][0].format(state[key]),True,text_color)
            self.surf_state.blit(text, TELLO_STATE_TEMPLATE[key][1])
        self.tello_ui.blit(self.surf_state, (0, self.tello.frame_height))

    def recording_init(self):
        '''
        Initialize cv2.VideoWriter object
        '''
        if not os.path.exists(self.dir_video):
            os.mkdir(self.dir_video)
        now = datetime.datetime.now()
        self.video_file_name = "{}.avi".format(now.strftime("%Y-%m-%d_%H-%M-%S"))
        video_path_file_name = os.path.sep.join(("./", self.dir_video, self.video_file_name))
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        try:
            self.video_writer_file = cv2.VideoWriter(video_path_file_name, fourcc, self.tello.frame_rate,
                                                    (self.tello.frame_width, self.tello.frame_height))
        except Exception as ex:
            print("Exception open VideoWriter", ex)
            self.video_writer_file.release()
        else:
            print("Starting record to {}".format(self.video_file_name))
            self.is_recording = True

    def draw_rec_indicator(self):
        '''
        Draw REC indicator on Video Surface when recording
        '''
        font = pygame.font.SysFont(self.__FONT_NAME, 36, bold=1)
        text = font.render("REC",True,self.__RED_COLOR)
        self.surf_rec_indicator.blit(text, (2, 0))
        self.tello_ui.blit(self.surf_rec_indicator, (self.tello.frame_width - 100, 40))

    def take_snapshot(self, frame):
        '''
        Take snapshot
        '''
        if not os.path.exists(self.dir_snapshot):
            os.mkdir(self.dir_snapshot)
        now = datetime.datetime.now()
        filename = "{}.jpg".format(now.strftime("%Y-%m-%d_%H-%M-%S"))
        path_filename = os.path.sep.join(("./",self.dir_snapshot, filename))
        cv2.imwrite(path_filename, frame)
        print("Snapshort saved {}".format(filename))

    def close(self):
        '''
        Release Tello stream cv2.VideoCapture instatnce and cv2.VideoWriter instance if recording
        '''
        try:
            self.tello_stream.release()
        except Exception as ex:
            print("Exception releasing cv2.VideoCature instance", ex)    
        self.tello_stream.release()
        try:
            self.video_writer_file.release()
        except Exception as ex:
            print("Exception releasing cv2.VideoWriter instance", ex)    

    def main_window(self):
        '''
        Main window
        '''
        self.tello_ui.fill(self.__BLACK_COLOR)
        self.print_tello_state(bat=20,templ=80,temph=80)
        pygame.display.flip()
        
        self.broadcast_init()

        run = True
        clock = pygame.time.Clock()
        while run:
            pygame.time.delay(50)
            self.print_tello_state(bat=20,templ=80,temph=80)
            
            keys = pygame.key.get_pressed()
            self.seek_key_send_command(keys)

            if keys[pygame.K_F1]:
                if not self.is_recording:
                    self.recording_init()
            if keys[pygame.K_F2]:
                if self.is_recording:
                    print("Stop record to {}".format(self.video_file_name))
                    self.is_recording_stop = True
            if keys[pygame.K_F3]:
                self.is_snapshortting = True
                pygame.time.delay(1000)
            if keys[pygame.K_F10]:
                print("Restarting brodcast")
                self.broadcast_init()
            pygame.display.flip()
            clock.tick(self.__FPS)

            for event in pygame.event.get(): 
                if event.type == pygame.QUIT:
                    self.tello.close()
                    self.close()
                    pygame.quit()
                    run = False


if __name__ == "__main__":        

    drone = ryze_tello.RyzeTello()
    drone_ui = RyzeTelloUI(drone) 
