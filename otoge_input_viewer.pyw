# IIDXコントローラの入力状態を表示したりリリース速度を計算したりする
import pygame
import sys, time
import numpy as np
import PySimpleGUI as sg
from functools import partial
import os
import threading
import traceback
from settings import Settings
from enum import Enum
import copy

FONT = ('Meiryo', 12)
FONTs = ('Meiryo', 8)

par_text = partial(sg.Text, font=FONT)
sg.theme('SystemDefault')

class DispButtons:
    def __init__(self):
        """コンストラクタ
        """
        self.settings = Settings()
        self.window = None
        self.window_settings = None
        self.joystick = None
        self.is_device_valid = False # コントローラを検出できている場合にTrue
        self.stop_thread = False # 強制停止用
        self.state = [0]*14
        self.scratch = [0]*4
        self.release = 0.0
        self.density = 0.0
        self.density_hist = []

    def update_string(self, target, value):
        """GUIの文字を変更する。main画面でのみ通したいので入口を共通化している。

        Args:
            target (str): パーツ名
            value (str): 書き込みたい文字列

        Returns:
            _type_: _description_
        """
        if self.window is None:
            return False
        try:
            self.window[target].update(value)
        except Exception:
            print(traceback.format_exc())
            pass

    def update_device_state(self):
        """コントローラの検出状態(OK/NG)を出力する
        """
        try:
            self.window['state'].update(f'OK')
            self.window['state'].update(text_color='#0000ff')
        except Exception:
            print(traceback.format_exc())
            pass


    def ico_path(self, relative_path:str):
        """アイコン表示用

        Args:
            relative_path (str): アイコンファイル名

        Returns:
            str: アイコンファイルの絶対パス
        """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def gui_main(self):
        """メイン画面の準備
        """
        menuitems = [
            ['File', ['settings', 'exit']],
        ]
        layout = [
            [sg.Menubar(menuitems, key='menu')],
            [par_text('release: ') ,par_text('', key='release'), par_text('[ms]')],
            [par_text('density: ') ,par_text('', key='density'), par_text('[notes/s]')],
            [par_text('')],
            [par_text('state_btn: '), par_text(str(self.state), key='state_btn')],
            [par_text('state_scr: '), par_text(str(self.scratch), key='state_scr')],
            [par_text('device1:'), par_text('', key='device1'), sg.Button('change', key='btn_change')]
        ]
        if self.joystick is not None:
            self.update_string('device1', f'{self.settings.connected_idx}.{self.joystick.get_name()}')
        self.window = sg.Window('Otoge input viewer for OBS', layout, grab_anywhere=True,return_keyboard_events=True,resizable=False,finalize=True,enable_close_attempted_event=True,icon=self.ico_path('icon.ico'),location=(self.settings.lx,self.settings.ly))

    def gui_settings(self):
        """設定画面の準備
        """
        # mainスレッド以外への遷移はすぐにやっておく
        layout = [
            [par_text('threshold for LN(default=225):',
                      tooltip='Set the time for determining long notes.\n何ms以上をCNとみなすかを設定。\ndefault=225'),
                      sg.Input(self.settings.ln_threshold,key='ln_threshold', size=(6,1))],
            [par_text('History size for release(default=100)',
                      tooltip='Set the number of notes for calculating release avg.\nリリース速度計算のために何ノーツを用いるか。\ndefault=100'),
             sg.Input(self.settings.size_release_hist,key='size_release_hist', size=(6,1))],
            [par_text('History size for density(default=100)',
                      tooltip='Set the number of notes for calculating chart density.\nノーツ密度計算のために何ノーツを用いるか。\ndefault=100'),
             sg.Input(self.settings.size_density_hist, key='size_density_hist', size=(6,1))],
        ]
        # modal=Trueによって元のウィンドウを操作できなくする
        self.window_settings = sg.Window('Settings - Otoge input viewer for OBS', layout, grab_anywhere=True,return_keyboard_events=True,resizable=False,finalize=True,enable_close_attempted_event=True,icon=self.ico_path('icon.ico'),location=(self.settings.lx,self.settings.ly), modal=True)
        while True:
            ev, val = self.window_settings.read()
            if ev in (sg.WIN_CLOSED, 'Escape:27', '-WINDOW CLOSE ATTEMPTED-', 'exit'):
                self.update_settings(val)
                self.window_settings.close()
                break

    def thread_write(self):
        """メンバ変数をxml出力するためのスレッド。皿や密度などの計算を正確に行うために別スレッド化する。
        """
        pre_state = None
        pre_scratch = None
        pre_density = None
        last_density_ts = time.perf_counter() # 最後に密度を計算した時刻を覚えておく。1sおきに処理したい。
        while True:
            cur_ts = time.perf_counter()
            if self.stop_thread:
                print('stop write thread')
                break
            # densityを計算
            if cur_ts - last_density_ts >= 1.0:
                last_density_ts = cur_ts
                # 全データが5s前になってしまったら切り捨て
                # 直近5sの範囲を取得
                if len(self.density_hist) > 0:
                    if cur_ts - self.density_hist[-1] > self.settings.time_window_density:
                        self.density_hist = []
                    for i in range(len(self.density_hist)):
                        if cur_ts - self.density_hist[i] <= self.settings.time_window_density:
                            break
                    self.density_hist = self.density_hist[i:] # 直近5秒以内の範囲だけに整形
                    self.density = len(self.density_hist) / self.settings.time_window_density
                else:
                    self.density = 0.0
            if (pre_state != self.state) or (pre_scratch != self.scratch) or (pre_density != self.density):
                self.update_string('density', f"{self.density:.1f}")
                self.update_string('state_btn', str(self.state))
                self.write_state()
                self.scratch = [0]*4
                pre_state = copy.copy(self.state)
                pre_scratch = copy.copy(self.scratch)
                pre_density = self.density
            #self.update_device_state()

            time.sleep(0.001)

    def write_state(self):
        """現在のキー入力状態をxmlファイルに出力

        Args:
            state (list(int)): キー入力状態(1-7鍵 *2)。0/1
            scratch (list(int)): 皿入力状態(up/down *2)
            release (float): 平均リリース時間
            density (float): 平均密度
        """
        with open('buttons.xml', 'w', encoding='utf-8') as f:
            f.write(f'<?xml version="1.0" encoding="utf-8"?>\n')
            f.write("<Items>\n")
            f.write(f"    <release>{self.release:.2f}</release>\n")
            f.write(f"    <density>{self.density:.2f}</density>\n\n")
            for i in range(14):
                f.write(f'    <btn{i+1}>{self.state[i]}</btn{i+1}>\n')
            for i in range(4):
                f.write(f'    <scr{i+1}>{self.scratch[i]}</btn{i+1}>\n')
            f.write("</Items>\n")

    def thread_detect(self):
        """コントローラ入力を監視するスレッド。
        """
        pygame.init()
        pygame.joystick.init()

        time_down = [-1]*14 # 押し始めた時刻を記録
        release_hist = []
        self.density_hist = []

        pre_scr_val = None
        pre_scr_is_up = False

        print('detect thread started')

        # 起動時のコントローラ接続
        cnt = pygame.joystick.get_count()
        if cnt > 0:
            self.is_device_valid = True
            if self.settings.connected_idx == None:
                self.settings.connected_idx = 0
            self.settings.connected_idx = min(self.settings.connected_idx, cnt-1)
            self.settings.connected_idx = self.settings.connected_idx
            self.joystick = pygame.joystick.Joystick(self.settings.connected_idx)
            self.window['device1'].update(f'{self.settings.connected_idx}.{self.joystick.get_name()}')
            self.joystick.init()

        while True:
            if self.stop_thread:
                print('stop detect thread')
                break
            try:
                for event in pygame.event.get():
                    #print(event)
                    if (event.type == pygame.JOYDEVICEADDED):
                        tmp = pygame.joystick.Joystick(event.device_index)
                        print(event.device_index, tmp.get_name())
                    elif (event.type == pygame.JOYDEVICEREMOVED):
                        print(f'コントローラ{event.instance_id} 接続解除')
                    elif event.type == pygame.JOYBUTTONDOWN:
                        if event.joy == self.settings.connected_idx:
                            if event.button >= 14:
                                continue
                            #print('down', event.button)
                            self.state[event.button] = 1
                            time_down[event.button] = time.perf_counter()
                    elif event.type == pygame.JOYBUTTONUP:
                        if event.joy == self.settings.connected_idx:
                            if event.button >= 14:
                                continue
                            self.state[event.button] = 0
                            tmp_release = (time.perf_counter() - time_down[event.button])*1000
                            if tmp_release < self.settings.ln_threshold:
                                self.density_hist.append(time.perf_counter())
                                release_hist.append(tmp_release)
                                if len(release_hist) > self.settings.size_release_hist:
                                    release_hist.pop(0)
                                self.release = sum(release_hist) / len(release_hist)
                                self.update_string('release', f"{self.release:.1f}")

                    elif event.type == pygame.JOYAXISMOTION:
                        if pre_scr_val is not None:
                            if event.value > pre_scr_val:
                                self.window['state_scr'].update('up')
                                if not pre_scr_is_up:
                                    self.density_hist.append(time.perf_counter())
                                self.scratch[0] = 1
                                pre_scr_is_up = True
                            elif event.value < pre_scr_val:
                                self.window['state_scr'].update('down')
                                if pre_scr_is_up:
                                    self.density_hist.append(time.perf_counter())
                                self.scratch[1] = 1
                                pre_scr_is_up = False
                        pre_scr_val = event.value
            #time.sleep(0.001)
            except Exception:
                print(traceback.format_exc())
                self.window['state'].update(f'NG')
                self.window['state'].update(text_color='#ff0000')
                break

        #joystick.quit()
        #pygame.quit()
        print('detect thread end')

    def change_device(self):
        """監視対象となるデバイスを変更する。外のコントローラがある場合はidxを1進める。
        """
        print('change device')
        cnt = pygame.joystick.get_count()
        if cnt > 0:
            self.settings.connected_idx = (self.settings.connected_idx + 1) % cnt
            self.joystick = pygame.joystick.Joystick(self.settings.connected_idx)
            self.window['device1'].update(f'{self.settings.connected_idx}.{self.joystick.get_name()}')
            self.joystick.init()
            self.update_string('device1', f'{self.settings.connected_idx}.{self.joystick.get_name()}')
        else:
            print('error! device not found')

    def update_settings(self, val):
        """設定画面の値を反映する。設定画面を閉じる時に実行する。

        Args:
            val (dict): sg.windowのevent
        """
        if str(self.settings.ln_threshold) != val['ln_threshold']:
            try:
                self.settings.ln_threshold = int(val['ln_threshold'])
            except Exception:
                pass
        if str(self.settings.size_release_hist) != val['size_release_hist']:
            try:
                self.settings.size_release_hist = int(val['size_release_hist'])
            except Exception:
                pass
        if str(self.settings.size_density_hist) != val['size_density_hist']:
            try:
                self.settings.size_density_hist = int(val['size_density_hist'])
            except Exception:
                pass

    def main(self):
        """メイン関数
        """
        #pygame.init()
        self.stop_thread = False
        self.gui_main()
        self.th_detect = threading.Thread(target=self.thread_detect, daemon=True)
        self.th_detect.start()
        self.th_write = threading.Thread(target=self.thread_write, daemon=True)
        self.th_write.start()
        while True:
            self.settings.lx = self.window.current_location()[0]
            self.settings.ly = self.window.current_location()[1]
            self.settings.connected_idx = self.settings.connected_idx
            ev, val = self.window.read()
            print(ev)
            if ev in (sg.WIN_CLOSED, 'Escape:27', '-WINDOW CLOSE ATTEMPTED-', 'exit'):
                self.stop_thread = True
                #self.th_detect.join()
                #self.th_write.join()
                self.settings.save()
                self.settings.disp()
                break
            elif ev == 'settings':
                self.gui_settings()
            elif ev == 'btn_change':
                self.change_device()
        print('main thread end')

app = DispButtons()
app.main()