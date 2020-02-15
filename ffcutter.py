#!/bin/python3
import os
import sys
import math
import re
import signal
import locale
import subprocess
import collections
import tempfile
import shutil
import json
import hashlib

import colorama
from docopt import docopt
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog

from mpv import MPV
from gui import Ui_main, Ui_shiftDialog


doc = """ffcutter

Usage:
    ffcutter
    ffcutter <video-file> [-s <save-file> --mpv=mpv-option...]
    ffcutter -h | --help

Options:
    -s <save-file>          Specify save file. Default is "filename.ffcutter" inside working directory.
    -m --mpv mpv-option     Specify additional mpv option or change the default ones.

Examples:
    ffcutter ./movie.mkv
    ffcutter ./movie.mkv -s ./movie.mkv.ffcutter
    ffcutter ./movie.mkv -m hr-seek=yes -m wid=-1

Default mpv options:
    wid=$wid
    keep-open=yes
    rebase-start-time=no
    framedrop=no
    osd-level=2
    osd-fractions=yes

Program state is saved into the save file on every user action.

GUI keys:

    space - Play/pause.
    arrows - Step frames.
    ctrl + arrows - Step seconds.
    alt + arrows - Jump anchors.
    up/down arrows - Step 5%.

    z - Put anchor on the current playback position.
    x - Remove highlighted anchor.

    h - Print this help message to the terminal.
    i - Print input file information to the terminal.

    ctrl + o - Open its directory.

    f - Input frame start/end shift which will be applied to all segments during encoding / stream copy.

If program crashes try to rerun it (duh).
"""

# TODO
# handle keystrokes from terminal too
# mpv keyframe/anchor jumps often fail, any way to fix that?
# don't generate concat when just one segment


class GUI(QtWidgets.QDialog):

    statusbar_update = QtCore.pyqtSignal()
    player_loaded = QtCore.pyqtSignal()
    frameindex_built = QtCore.pyqtSignal()
    shell_message = QtCore.pyqtSignal(str)

    def __init__(self, filename=None, save_filename=None, mpv_options=[], skip_index=False):
        super().__init__()
        self.filename = filename
        self.save_filename = save_filename
        self.mpv_options = mpv_options

        self.initialize_ui()
            
    def initialize_ui(self):
        self.segments = []
        self.save_file_path = None
        self.frame_total = None
        self.frame_num = None
        
        self.hover_cursor = None # mouse position on the seek seekbar
        self.playback_pos = None
        self.playback_len = None
        self.anchor = None # single anchor position that hasn't become a segment
        self.closest_anchor = None # self.anchor or anchor closest to playback_pos

        self.state_loaded = False

        self.show_keyframes = False
        self.running_ffmpeg = False

        self.pts = []
        self.ipts = []
        self.ffmpeg_shift_a = 0
        self.ffmpeg_shift_b = 0
        
        # set up the user interface from Designer
        self.ui = Ui_main()
        self.ui.setupUi(self)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle('ffcutter')
        self.setFocus(True)
        
        self.ui.print.clicked.connect(self.print_ffmpeg)
        self.ui.run.clicked.connect(self.run_ffmpeg)
        
        def open_file():
            fname = QFileDialog.getOpenFileName(self)
            self.filename = fname[0]
            self.save_filename = os.path.split(self.filename)[1] + '.ffcutter'
            if self.filename != '':    
                self.execute_file()
                                   
        self.ui.openFile.clicked.connect(open_file)   

        self.ui.print.setEnabled(False)
        self.ui.run.setEnabled(False)
        
        editor = self.ui.argsEdit
        text = editor.toPlainText()

        outfile = ' '
        text = re.sub(r'out:[^\S\n]*\n', 'out: %s\n' % outfile, text)
        editor.setPlainText(text)

        def toggle_editor():
            editor.setHidden(not editor.isHidden())
            if not editor.isHidden():
                editor.setFocus(True)

        editor.hide()
        self.ui.toggleArgsEdit.clicked.connect(toggle_editor)
        self.statusbar_update.connect(self.update_statusbar)

        self.seekbar_pressed = False
        self.ui.seekbar.paintEvent = self.seekbar_paint_event
        self.ui.seekbar.mouseMoveEvent = self.seekbar_mouse_move_event
        self.ui.seekbar.mousePressEvent = self.seekbar_mouse_press_event
        self.ui.seekbar.mouseReleaseEvent = self.seekbar_mouse_release_event
        self.ui.seekbar.leaveEvent = self.seekbar_leave_event

        self.refresh_statusbar_timer = QtCore.QTimer(self)
        self.refresh_statusbar_timer.setInterval(300)
        self.refresh_statusbar_timer.timerEvent = lambda _: self.update_statusbar()
        self.show()
         
        # check if necessary binaries are present
        self.ffmpeg_bin = 'ffmpeg'
        self.ffprobe_bin = 'ffprobe'
        self.interrupted = False
        
        if getattr(sys, 'frozen', False):
            dirname = os.path.split(sys.executable)[0]
            self.ffmpeg_bin = os.path.join(dirname, 'ffmpeg.exe')
            self.ffprobe_bin = os.path.join(dirname, 'ffprobe.exe')
        elif os.name == 'nt':
            dirname = os.path.split(__file__)[0]
            self.ffmpeg_bin = os.path.join(dirname, 'ffmpeg.exe')
            self.ffprobe_bin = os.path.join(dirname, 'ffprobe.exe')

        
        self.directory = getattr(sys, '_MEIPASS', os.path.abspath('.'))
        self.ffmpeg_bin = os.path.join(self.directory, 'ffmpeg.exe')
        self.ffprobe_bin = os.path.join(self.directory, 'ffprobe.exe')
        print(self.directory)
        
        if not shutil.which(self.ffmpeg_bin):
            self.print_error('FFmpeg weren\'t found.')
            self.ui.run.setEnabled(False)
            self.ffmpeg_bin = None
        if not shutil.which(self.ffprobe_bin):
            self.print_error('FFprobe weren\'t found. Wont be able to build frame index.')
            self.ffprobe_bin = None    
    
    
    # Read a file choosed #########################################################################
    ###############################################################################################
    
    def execute_file(self):
        self._, self.ext= os.path.splitext(self.filename)
                        
        if self.ext == ".txt" :
            self.execute_text_file()
        else :
            self.load_file()   
            
    def execute_text_file(self):
        self.scene_list = []
        with open(self.filename, 'rb') as fp:
            for line in fp:
                self.scene_list.append(line.decode('utf-8'))
        command_list = []
        for i, line in enumerate(self.scene_list):
            line_args = line.split()
            line_args[2] = int(line_args[2])
            line_args[3] = int(line_args[3])       
            video_segment = [line_args[0], line_args[1], line_args[2], line_args[3]]
            command_list.append(self.make_ffmpeg_command(video_segment))
        
        if not command_list == []:
            self.run_ffmpeg(commands = command_list)
        else :
            print("Input file doesn't have a proper form")
        
        
    def make_ffmpeg_command(self, video_segment):
        input_file = video_segment[0]        
        infile_name, ext = os.path.splitext(os.path.split(input_file)[1])
        if ext == '' :
            input_file = os.path.join(input_file ,self.get_infile_path(input_file))

        cmd = [self.ffprobe_bin] + [' -v 0 -of csv=p=0 -select_streams v:0 -show_entries stream=r_frame_rate '] + [input_file]
        cmd = "".join(map(str, cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        cmdout, err = proc.communicate()
        frame_duration = 1/float(eval(cmdout.decode("utf-8").rstrip()))
        
        outfile_path = video_segment[1]
        if not os.path.exists(outfile_path):
            os.mkdir(outfile_path)
        
        infile_name, _ext = os.path.splitext(os.path.split(input_file)[1])
        start = video_segment[2]
        end = video_segment[3]
        tmpfile = '%s.part%d-%d%s' % (infile_name, start, end, _ext)
        if ext == '':
            self.save_data_file(video_segment, tmpfile)
        tmpfile = os.path.join(outfile_path, tmpfile)

            
        

        ffmpeg = self.ffmpeg_bin or 'ffmpeg'
        start = start*frame_duration 
        end = end*frame_duration + frame_duration

        command = [ffmpeg, '-i', input_file, '-y', '-ss', str(start), '-to', str(end), '-c', 'copy', tmpfile]
        
        return command
    
    # Save data file ##############################################################################
    ###############################################################################################
    
    def get_cmd_option(self, filename, option):
        with open(filename, 'rb') as fp:
            for line in fp:
                line = line.decode()
                if line.find(option) != -1 :
                    line = line.replace(option, "", 1)
                    line = line.replace("\r\n", "", 1)
                    return line
    
    def get_infile_path(self, infile_path):
        metainfo_file = os.path.join(infile_path, "metainfo.txt")
        cam_filename = self.get_cmd_option(metainfo_file, "cam=")
        return cam_filename
    
    def save_data_file(self, segment, video_filename):
        infile_path = segment[0]
        outfile_path = segment[1]
        if not os.path.exists(outfile_path):
            os.mkdir(outfile_path)
        
        start = segment[2]
        end = segment[3]
        
        metainfo_file = os.path.join(infile_path, "metainfo.txt")

        
        def save_can_print_out():
            inputdata_file, outputdata_file = get_in_out_file("sync=")
            
            f_in = open(inputdata_file, 'r')
            f_out = open(outputdata_file, 'w')
            
            f_out.write(f_in.readline())
            for i in range(0, start-1):
                f_in.readline()
                
            for i in range(start-1, end):
                line = f_in.readline()   
                line = line.replace(str(i), str(i- start + 1), 1)
                line_split = line.split(",")
                idx_time_parsing_line = line_split[0:2]
                data_parsing_line = list(map(int, line_split[2:]))                

                if i==start-1:
                    self.min_canidx = min(x for x in data_parsing_line if x > 0) - 1
                elif i==end-1:
                    self.max_canidx = max(x for x in data_parsing_line if x > 0)                

                for i in range(len(data_parsing_line)):
                    if data_parsing_line[i] > 0 :
                        data_parsing_line[i] -= self.min_canidx
                
                data_line = ", ".join(str(x) for x in data_parsing_line) + "\n"
                idx_time_line = ", ".join(str(x) for x in idx_time_parsing_line) + ", "
                
                line = idx_time_line + data_line
                f_out.write(line)
        
            f_in.close()
            f_out.close()            
            write_meta("sync="+os.path.split(outputdata_file)[1]+"\n")

            
        def save_dc_merged():
            inputdata_file, outputdata_file = get_in_out_file("dgps_car=")  
            
            f_in = open(inputdata_file, 'r')
            f_out = open(outputdata_file, 'w')
            
            for i in range(0, self.min_canidx):
                f_in.readline()
            for i in range(self.min_canidx, self.max_canidx+1):
                line = f_in.readline()
                line = line.replace(str(i), str(i-self.min_canidx), 1)
                f_out.write(line)
            
            f_in.close()
            f_out.close()
            write_meta("dgps_car="+os.path.split(outputdata_file)[1]+"\n")
        
        def save_cam_params():
            cam_params_filename = self.get_cmd_option(metainfo_file, "cam_params=")
            inputdata_file = os.path.join(infile_path, cam_params_filename)
            outputdata_file = os.path.join(outfile_path, cam_params_filename)      
            shutil.copyfile(inputdata_file, outputdata_file)
            write_meta("cam_params="+os.path.split(outputdata_file)[1]+"\n")
             
                    
        def get_in_out_file(option):
            filename = self.get_cmd_option(metainfo_file, option)
            
            inputdata_filename = os.path.join(infile_path, filename)
            filename, ext = os.path.splitext(filename)
            outputdata_filename = '%s.ffcutter.part%d-%d.txt' % (filename, start , end)
            outputdata_filename = os.path.join(outfile_path, outputdata_filename)
            
            return inputdata_filename, outputdata_filename
        
        def write_meta(line):
            outputdata_file = os.path.join(outfile_path, "metainfo.txt")
            f_out = open(outputdata_file, 'a')
            f_out.write(line)
            f_out.close()
        
        
        outputdata_file = os.path.join(outfile_path, "metainfo.txt")
        open(outputdata_file, 'w').write("cam="+video_filename+"\n")
        save_can_print_out()
        save_dc_merged()
        save_cam_params()
        
    
    # Load video file #############################################################################
    ###############################################################################################    

    def load_file(self):   
        self.ui.horizontalLayout_3.removeWidget(self.ui.video)
        self.ui.video = QtWidgets.QWidget()
        self.ui.video.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ui.video.setStyleSheet("background-color: rgb(117, 80, 123);")
        self.ui.video.setObjectName("video")
        self.ui.horizontalLayout_3.addWidget(self.ui.video)
        
        self.segments = []
        self.save_file_path = None
        self.frame_total = None
        self.frame_num = None
        
        self.hover_cursor = None # mouse position on the seek seekbar
        self.playback_pos = None
        self.playback_len = None
        self.anchor = None # single anchor position that hasn't become a segment
        self.closest_anchor = None # self.anchor or anchor closest to playback_pos

        self.state_loaded = False

        self.show_keyframes = False
        self.running_ffmpeg = False

        self.pts = []
        self.ipts = []
        self.ffmpeg_shift_a = 0
        self.ffmpeg_shift_b = 0
        ##################################################
        
        self.ui.print.setEnabled(True)
        self.ui.run.setEnabled(True)
 
        self.save_filename = os.path.split(self.filename)[1] + '.ffcutter'
        self.setWindowTitle('ffcutter - ' + os.path.split(self.filename)[-1])
        
        if self.save_file_path is None :
            self.save_file_path = os.path.split(self.filename)[0]
        
        self.tmpdir = os.path.join(tempfile.gettempdir(), 'ffcutter')
        try:
            os.mkdir(self.tmpdir)
        except FileExistsError:
            pass
        except Exception:
            self.tmpdir = tempfile.gettempdir()

        colorama.init()

        editor = self.ui.argsEdit
        text = editor.toPlainText()
        outfile = self.get_user_ffmpeg_args()[0]
        text = re.sub(r'out:[^\S\n]*\n', 'out: %s\n' % outfile, text)
        editor.setPlainText(text)

        def set_shifts():
            self.ffmpeg_shift_a = wrapper.a.value()
            self.ffmpeg_shift_b = wrapper.b.value()
            
        dialog = QtWidgets.QDialog(self)
        wrapper = Ui_shiftDialog()
        wrapper.setupUi(dialog)
        dialog.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        wrapper.a.setValue(self.ffmpeg_shift_a)
        wrapper.b.setValue(self.ffmpeg_shift_b)
        dialog.accepted.connect(set_shifts)

        self.shifts_dialog = dialog
        self.shifts_dialog_ui = wrapper
        self.shifts_dialog_ui.suggestion.hide()
        
        self.show()
        self.init_player()

        # SIGINT handling trickery    
        timer = QtCore.QTimer(self)
        timer.timerEvent = lambda _: None
        timer.start(1000)
        self.interrupted = False
        
        
    def interrupt(self):
        if self.running_ffmpeg:
            self.interrupted = True
        else:
            self.print('Exiting gracefully.')
            QtWidgets.QApplication.quit()
    
    # Player #################################################################################
    ###############################################################################################

    def init_player(self):
        def mpv_log(loglevel, component, message):
            self.print('Mpv log: [{}] {}: {}'.format(loglevel, component, message))
        
        mpv_args = []
        mpv_kw = {
            'wid': int(self.ui.video.winId()),
            'keep-open': 'yes',
            'rebase-start-time': 'no',
            'framedrop': 'no',
            'osd-level': '2',
            'osd-fractions': 'yes',
        }
        for opt in self.mpv_options:
            if '=' in opt:
                k, v = opt.split('=', 1)
                mpv_kw[k] = v
            else:
                mpv_args.append(opt)

        
        player = MPV(*mpv_args, log_handler=mpv_log, **mpv_kw)
        self.player = player
        player.pause = True

        def on_player_loaded():
            if self.ffmpeg_bin:
                self.check_ffmpeg_seek_problem()
            self.ui.loading.hide()
            self.state_loaded = True

        def on_playback_len(s):
            self.playback_len = s
            player.unobserve_property('duration', on_playback_len)

        def on_playback_pos(s):
            player.observe_property('estimated-frame-number', on_framenum_count)
            if self.playback_pos is None:
                self.player_loaded.emit()
            self.playback_pos = s
            self.statusbar_update.emit()
            self.ui.seekbar.update()
            
        def on_framenum_count(s):
            self.frame_num = s
            
        def on_frametotal_total(s):
            self.frame_total = s
            
        self.player_loaded.connect(on_player_loaded)
        player.observe_property('estimated-frame-count', on_frametotal_total)         
        player.observe_property('time-pos', on_playback_pos)
        player.observe_property('duration', on_playback_len)
        player.play(self.filename)
        
    def check_ffmpeg_seek_problem(self):
        self.print('Testing if ffmpeg stream copy seeking on this file works correctly...')

        def clean():
            for f in [first_frame1, first_frame2, tmpfile]:
                try:
                    os.remove(f)
                except Exception:
                    pass
        
        def find_global_frame_shift():
            cmd = [self.ffprobe_bin, self.filename] + '-show_frames -show_packets -select_streams v -print_format json=c=1 -v error'.split()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            pts = []
            while True:
                line = proc.stdout.readline().decode()
                if not line:
                    break
                elif '"frame"' in line:
                    break
    
                if '"packet"' in line and line.startswith('        {'):
                    packet = json.loads(line.strip()[:-1])
                    t = packet.get('dts_time', packet.get('pts_time', None))
                    if t is None:
                        return
                    pts.append(float(t))
    
            proc.terminate()
    
            q = collections.deque(maxlen=10)
            for t in sorted(set(pts)):
                rm = []
                for v in q:
                    if abs(v-t) <= 0.002:
                        rm.append(v)
                for v in rm:
                    q.remove(v)
                    pts.remove(v)
    
            if len(pts) > 1:
                label = self.shifts_dialog_ui.suggestion
                label.show()
                label.setText('%s -%s -%s' % (label.text(), len(pts)-1, len(pts)-1))
                
        first_frame1 = os.path.join(self.tmpdir, 'sample1.png')
        tmpfile = os.path.join(self.tmpdir, 'sample2' + os.path.splitext(self.filename)[1])
        first_frame2 = os.path.join(self.tmpdir, 'sample2.png')
        errmsg = 'Failed testing ffmpeg.'

        # get frame with encoding on
        cmd = [self.ffmpeg_bin] + '-i FILE -y -frames 1 -v error'.split() + [first_frame1]
        cmd[2] = self.filename
        proc = subprocess.Popen(cmd)
        if self._wait(proc, errmsg):
            clean()
            return

        # get frame with encoding off and try to find offset
        # stream copy 1 frame video
        cmd = [self.ffmpeg_bin] + '-i FILE -y -ss TIME -c copy -frames 1 -v error'.split() + [tmpfile]
        cmd[2] = self.filename
        cmd[5] = str(self.playback_pos)
        proc = subprocess.Popen(cmd)
        if self._wait(proc, errmsg):
            clean()
            return

        # get that video first frame
        cmd = [self.ffmpeg_bin] + '-i -y -frames 1 -v error'.split() + [first_frame2]
        cmd.insert(2, tmpfile)
        proc = subprocess.Popen(cmd)
        if self._wait(proc, errmsg):
            clean()
            return

        with open(first_frame1, 'rb') as frame1, open(first_frame2, 'rb') as frame2:
            hash1 = hashlib.md5(frame1.read()).hexdigest()
            hash2 = hashlib.md5(frame2.read()).hexdigest()
            if hash1 != hash2:
                find_global_frame_shift()
                self.print_error('FFmpeg stream copy seeking seem to work incorrectly.\n' +
                                 '    No-encode mode will most likely be inaccurate.\n' +
                                 '    Use F key to adjust global offsets.')
            else:
                self.print('FFmpeg stream copy seeking seem to work correctly.')

        clean()

    def _wait(self, proc, msg='Failed executing command.'):
        if proc.wait() != 0:
            self.print_error('%s\n' % msg +
                             '    Command: %s\n' % ' '.join(proc.args) +
                             '    Exit code: %s' % proc.returncode)
        return proc.returncode
    
    def update_statusbar(self):
        if self.playback_pos is None:
            return

        seeking = self.player.seeking
        text = '<pre>{}{}{} (frame:{})</pre>'.format(
                'K ' if self.player.video_frame_info['picture-type'] == 'I' else '  ',
                format_time(floor(self.playback_pos, 3), full=True),
                ' ... ' if seeking else '',
                f'{self.frame_num}/{self.frame_total}',
            ) 
        
        if seeking and not self.refresh_statusbar_timer.isActive():
            self.refresh_statusbar_timer.start()
        elif not seeking and self.refresh_statusbar_timer.isActive():
            self.refresh_statusbar_timer.stop()
        self.ui.status.setText(text)

    # Print info messages #########################################################################
    ###############################################################################################

    def print(self, *args, **kw):
        print(*args, **kw)

    def print_error(self, *args, **kw):
        msg = colorama.Fore.LIGHTRED_EX + kw.get('sep', ' ').join([str(a) for a in args]) + colorama.Style.RESET_ALL
        print(msg, **kw)

    def print_segments(self):
        line = ' '.join(['%d-%d' % (a, b) for a, b in self.segments])
        if self.anchor is not None:
            line += ' (%d)' % self.anchor
        self.print(line)

    def print_video_info(self):
        proc = subprocess.run([self.ffmpeg_bin, '-i', self.filename], stderr=subprocess.PIPE)
        no = True
        self.print()
        term = shutil.get_terminal_size((80, 20))

        def sep(title=''):
            self.print('--' + title + '-' * (term.columns-2-len(title)))

        self.print()
        for line in proc.stderr.decode().splitlines():
            if line.startswith('Input'):
                no = False
            if no:
                continue

            if ': Video:' in line:
                sep('VIDEO')
                color = colorama.Fore.LIGHTCYAN_EX
                style = colorama.Style.BRIGHT
                reset = colorama.Style.RESET_ALL
                # we (I) are mostly interested in video bitrate, so
                line = re.sub(r'\b\d+\s+\w+/s\b', color + style + r'\g<0>' + reset, line)
                self.print(line)
            elif line.startswith('At least'):
                continue
            else:
                if ': Audio:' in line:
                    sep('AUDIO')
                self.print(line)
        self.print()
        
    # Keyboard events #############################################################################
    ###############################################################################################

    def to_next_anchor(self, backwards=False):
        anchors = [t for ab in self.segments for t in ab]
        if self.anchor is not None:
            anchors.append(self.anchor)
            anchors = sorted(anchors)

        i = sidesi(self.playback_pos, anchors)[0 if backwards else 1]

        if i is not None:
            self.player.seek(anchors[i], 'absolute', 'exact')

    def keyPressEvent(self, event):
        k = event.key()
        ctrl = event.modifiers() == Qt.ControlModifier
        alt = event.modifiers() == Qt.AltModifier
        shift = event.modifiers() == Qt.ShiftModifier

        if ctrl and k in (Qt.Key_Q, Qt.Key_W):

            QtWidgets.QApplication.quit()

        elif k == Qt.Key_D and ctrl:

            try:
                import ptpdb
                ptpdb.set_trace()
            except ImportError:
                import pdb
                pdb.set_trace()

        elif k == Qt.Key_Escape:

            self.setFocus(True)

        elif k == Qt.Key_I:

            self.print_video_info()

        elif k == Qt.Key_H:

            self.print(doc)

        ################################

        if self.playback_pos is None or not self.state_loaded:
            return

        ################################

        if k == Qt.Key_Space:
            self.player.pause = not self.player.pause

        elif k == Qt.Key_Up:
            self.player.seek(5, 'relative-percent')

        elif k == Qt.Key_Down:
            self.player.seek(-5, 'relative-percent')

        elif k == Qt.Key_Left:
            if ctrl:
                self.player.seek(-1, 'relative', 'exact')
            elif alt:
                self.to_next_anchor(True)
            else:
                self.player.frame_back_step()

        elif k == Qt.Key_Right:
            if ctrl:
                self.player.seek(1, 'relative', 'exact')
            elif alt:
                self.to_next_anchor()
            else:
                self.player.frame_step()

        elif k == Qt.Key_Z:
            self.put_anchor()

        elif k == Qt.Key_X:
            self.del_anchor()

        elif k == Qt.Key_F:
            self.shifts_dialog_ui.a.setValue(self.ffmpeg_shift_a)
            self.shifts_dialog_ui.b.setValue(self.ffmpeg_shift_b)
            self.shifts_dialog.show()

        self.update_statusbar()

    # anchor ######################################################################################
    ###############################################################################################
    
    def del_anchor(self):
        if self.closest_anchor == self.anchor:
            self.anchor = None
        else:
            for a, b in self.segments:
                if a == self.closest_anchor:
                    self.segments.remove((a, b))
                    self.anchor = b
                elif b == self.closest_anchor:
                    self.segments.remove((a, b))
                    self.anchor = a

        self.print('> del, %s segments' % len(self.segments))
        self.print_segments()
        self.ui.seekbar.update()

    def put_anchor(self, split_if_inside=True):
        if self.anchor is None:
            self.anchor = self.playback_pos
            move = 0
        else:
            aa, bb = self.anchor, self.playback_pos
            if aa > bb:
                aa, bb = bb, aa

            aai = -1
            bbi = -1

            for i, seg in enumerate(self.segments):
                a, b = seg

                if a <= aa <= b:
                    aai = i
                if a <= bb <= b:
                    bbi = i

            def remove_between(aa, bb):
                segments = []
                for a, b in self.segments:
                    if not (a >= aa and b <= bb):
                        segments.append((a, b))
                self.segments = segments

            if aai == -1 and bbi == -1:
                move = 1
                # both sides on clean range

                remove_between(aa, bb)
                self.segments.append((aa, bb))

            elif aai > -1 and aai == bbi:
                move = 2
                # fully inside another segment -> split that segment

                a, b = self.segments.pop(aai)
                if a == aa:
                    self.segments.append((bb, b))
                elif b == bb:
                    self.segments.append((a, aa))
                else:
                    self.segments.extend([(a, aa), (bb, b)])

            elif (aai != -1 and bbi == -1) or (aai == -1 and bbi != -1):
                move = 3
                # only one side inside another segment

                if aai > -1:
                    aa, _ = self.segments.pop(aai)
                else:
                    _, bb = self.segments.pop(bbi)
                remove_between(aa, bb)
                self.segments.append((aa, bb))

            elif aai != bbi and split_if_inside:
                move = 4
                # both sides on different segments -> join those segments

                a, _ = self.segments.pop(aai)
                _, b = self.segments.pop(bbi-1)
                remove_between(aa, bb)

                self.segments.append((a, b))

            self.anchor = None

        self.segments = list(sorted(self.segments, key=lambda t: t[0]))

        print('put, move #%s, %s segments' % (move, len(self.segments)))
        self.print_segments()
        self.ui.seekbar.update()

    # File state ##################################################################################
    ###############################################################################################

    def get_state(self):
        return {
            'mode': 'keep' if self.ui.keep.isChecked() else 'remove',
            'segments': self.segments,
            'anchor': self.anchor,
            'ffargs': self.ui.argsEdit.toPlainText(),
            'encode': self.ui.encode.isChecked(),
            '2-pass': self.ui.twoPass.isChecked(),
            'shifts': (self.ffmpeg_shift_a, self.ffmpeg_shift_b),
        }

    # Encoding ####################################################################################
    ###############################################################################################

    def get_inversed_segments(self):
        segments = []
        anchors = [t for seg in self.segments for t in seg]
        prev = None
        for i, t in enumerate(anchors):
            if i % 2 == 0: # a
                if prev is None:
                    prev = 0
            else: # b
                prev = t
                if i == len(anchors)-1:
                    if not self.is_end(t):
                        segments.append((t, self.playback_len))
        return segments
    
    def adjust_segments(self, segments):
        frame_duration = 1/self.player.fps
        keep = self.ui.keep.isChecked()

        for i, seg in enumerate(segments):
            a, b = seg
            if keep:
                b += frame_duration
            else:
                a += frame_duration                
            a += frame_duration * self.ffmpeg_shift_a
            b += frame_duration * self.ffmpeg_shift_b
            a = closest(a, self.pts, max_diff=frame_duration) or a 
            b = closest(b, self.pts, max_diff=frame_duration) or b
           
            segments[i] = (a, b)

    def get_user_ffmpeg_args(self):
        outfile = None
        outargs = []
        inargs = []
        for line in self.ui.argsEdit.toPlainText().splitlines():
            line = line.strip()
            if line.startswith('out:'):
                outfile = line[4:].strip()
            elif line.startswith('out-args:'):
                outargs = line[9:].strip().split()
                outargs = map(str.strip, outargs)
                outargs = [arg for arg in outargs if arg and not arg.startswith('#')]
            elif line.startswith('in-args:'):
                inargs = line[8:].strip().split()
                inargs = map(str.strip, inargs)
                inargs = [arg for arg in inargs if arg and not arg.startswith('#')]

        if not outfile:
            orig_name, ext = os.path.splitext(os.path.split(self.filename)[1])
            outfile = orig_name + '.ffcutter' + ext

        outargs = outargs or []
        inargs = inargs or []

        return outfile, outargs, inargs


    # Run ffnoeg ##################################################################################
    ###############################################################################################
    
    def make_ffmpeg(self):
        outfile, outargs, inargs = self.get_user_ffmpeg_args()

        path_name, ext = os.path.splitext(outfile)
        tmpfiles = []
        keep = self.ui.keep.isChecked()

        encode_commands = []

        if keep:
            segments = self.segments.copy()
        else:
            segments = self.get_inversed_segments()

        self.adjust_segments(segments)
        
        frame_duration = 1/self.player.fps
        for segment in segments:
            start, end = segment
            if keep:
                end -= frame_duration
            else:
                start -= frame_duration 
            start = round(start/frame_duration)
            end = round(end/frame_duration)
            tmpfile = '%s.part%d-%d%s' % (path_name, start, end, ext)
            tmpfile = os.path.join(self.save_file_path, tmpfile)
            tmpfiles.append(tmpfile)

        # generate the commands       
        ffmpeg = self.ffmpeg_bin or 'ffmpeg'
        encode_command = [ffmpeg] + inargs + ['-i', self.filename, '-y']
        for i, seg in enumerate(segments):
            a, b = seg
            encode_command += ['-ss', str(a), '-to', str(b), '-c', 'copy'] + outargs + [tmpfiles[i]]
        encode_commands.append(encode_command)

        for cmd in encode_commands:
            while 'None' in cmd:
                i = cmd.index('None')
                cmd.pop(i)
                cmd.pop(i-1)
        return encode_commands
    
    def print_ffmpeg(self):
        self.print()
        for args in self.make_ffmpeg():
            self.print(' '.join(args))
        self.print()

    def run_ffmpeg(self, commands = None):
        if not commands :
            commands = self.make_ffmpeg()
        commands_len = len(commands)
        self._proc = None
        
        def next_run():
            args = commands.pop(0)
            self.print()
            self.print('%d/%d - %s' % (commands_len - len(commands), commands_len, ' '.join(args)))
            self._proc = subprocess.Popen(args)

        def stop(exit_code):
            self.ui.run.setEnabled(True)
            self.running_ffmpeg = False
            timer.stop()
            self.print()
            if self.interrupted:
                self.print_error('Interrupted. Command exit code: %s' % exit_code)
                self.interrupted = False
            elif exit_code == 0:
                self.print('Done.')
                self.ui.success = QtWidgets.QMessageBox()
                self.ui.success.setWindowTitle('Success')
                self.ui.success.setText('Successfully Save Files')
                self.ui.success.exec()
            else:
                self.print_error('Fail. Command exit code: %s' % exit_code)

        def check(_):
            code = self._proc.poll()
            if code is not None:
                if code != 0 or not commands:
                    stop(code)
                else:
                    next_run()
            elif self.interrupted:
                self._proc.send_signal(signal.SIGINT)

        self.running_ffmpeg = True
        next_run()

        timer = QtCore.QTimer(self)
        timer.timerEvent = check
        timer.setInterval(1000)
        timer.start()
        self.ui.run.setEnabled(False)
        
        
    # Bar #########################################################################################
    ###############################################################################################

    def seekbar_mouse_move_event(self, event):
        self.hover_cursor = event.x()
        if self.seekbar_pressed:
            self.seekbar_mouse_press_event(event)
        self.ui.seekbar.update()

    def seekbar_leave_event(self, event):
        self.hover_cursor = None
        self.ui.seekbar.update()

    def seekbar_mouse_press_event(self, event):
        if self.playback_pos is None:
            return

        self.seekbar_pressed = True
        precision = 'exact' if event.modifiers() == Qt.ControlModifier else None
        self.player.seek(event.x() / (self.ui.seekbar.width() / 100), 'absolute-percent', precision)
        self.ui.seekbar.update()

    def seekbar_mouse_release_event(self, event):
        self.seekbar_pressed = False

    def seekbar_paint_event(self, event):
        if self.playback_pos is None:
            return

        seekbar = self.ui.seekbar
        painter = QtGui.QPainter(seekbar)

        playback_inside_segment = self.playback_pos == self.anchor
        closest_anchor = None
        closest_anchor_diff = self.playback_len

        def time_to_x(s):
            return seekbar.width() * s / self.playback_len

        # segments
        color = QtGui.QColor(0xC36DCB)
        for a, b in self.segments:
            if a <= self.playback_pos <= b:
                playback_inside_segment = True

            diff = abs(a - self.playback_pos)
            if diff < closest_anchor_diff:
                closest_anchor = a
                closest_anchor_diff = diff

            diff = abs(b - self.playback_pos)
            if diff < closest_anchor_diff:
                closest_anchor = b
                closest_anchor_diff = diff

            a, b = time_to_x(a), time_to_x(b)
            w = b - a
            if w < 1:
                w = 1
            painter.fillRect(a, 0, w, seekbar.height(), color)

        # playback cursor
        painter.setPen(QtGui.QColor(Qt.black))
        a = time_to_x(self.playback_pos)
        painter.drawLine(a, 0, a, seekbar.height())

        # playback cursor inside segment indicator
        if playback_inside_segment:
            size = 5
            half = 2
            painter.fillRect(a-half, seekbar.height()/2-half, size, size, QtGui.QColor(0,0,0,200))

        # single anchor
        if self.anchor is not None:
            closest_anchor = self.anchor

            color = QtGui.QColor(Qt.cyan)
            painter.setPen(color)
            pos = time_to_x(self.anchor)
            painter.drawLine(pos, 0, pos, seekbar.height())

        # closest anchor highlight
        if closest_anchor is not None:
            pos = time_to_x(closest_anchor)

            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.darkGreen)

            h = 6
            halfw = 4
            p1 = QtCore.QPoint(pos, seekbar.height()-h)
            p2 = QtCore.QPoint(pos-halfw, seekbar.height())
            p3 = QtCore.QPoint(pos+halfw, seekbar.height())
            painter.drawPolygon(p1, p2, p3)

        self.closest_anchor = closest_anchor

        # hover cursor
        if self.hover_cursor is not None:
            painter.setPen(QtGui.QColor(0,0,0,90))
            painter.drawLine(self.hover_cursor, 0, self.hover_cursor, seekbar.height())

        # chapters
        if self.player.chapter_list:
            painter.setPen(Qt.black)
            for ch in self.player.chapter_list:
                x = time_to_x(ch['time'])
                painter.drawPoint(x, 0)
                painter.drawPoint(x-1, 0)
                painter.drawPoint(x+1, 0)
                painter.drawPoint(x, 1)

        # debug keyframes
        if self.show_keyframes:
            painter.setPen(Qt.red)
            backwards = False
            y = 0
            for t in self.ipts:
                painter.drawPoint(time_to_x(t), y)
                painter.drawPoint(time_to_x(t), y+1)
                y += 3 if not backwards else -3
                if y > seekbar.height() - 3:
                    backwards = True
                    y -= 6
                elif y < 0:
                    backwards = False
                    y += 6


def sidesi(target, sorted_elements, min_diff=0, max_diff=None):
    'sidesi(5, [3,4,5,6]) -> (1, 3)'

    t = target
    ls = sorted_elements
    log = False

    for i, e in enumerate(ls):
        # if log:
        #     print('--', t, e)

        if e >= target:
            a = b = None

            #########################

            ri = i
            while True:
                if ri == len(ls):
                    break

                d = ls[ri] - t
                if d != 0 and min_diff <= d:
                    if max_diff is not None and d > max_diff:
                        ri += 1
                        continue
                    b = ri
                    break

                ri += 1


            #########################

            li = i-1
            while True:
                if li == -1:
                    break

                d = t - ls[li]
                if d != 0 and min_diff <= d:
                    if max_diff is not None and d > max_diff:
                        li -= 1
                        continue
                    a = li
                    break

                li -= 1


            #########################

            if log:
                print('return:', a, t, b)

            return (a, b)
    else:
        if not ls:
            return (None, None)

        a = b = None

        li = len(ls) - 1
        while True:
            if li == -1:
                break

            d = t - ls[li]
            if d != 0 and min_diff <= d:
                if max_diff is not None and d > max_diff:
                    li -= 1
                    continue
                a = li
                break

            li -= 1

        if log:
            print('else  :', a, t, b)

        return (a, b)


def sides(target, elements, **kw):
    ai, bi = sidesi(target, elements, **kw)
    a = b = None
    if ai:
        a = elements[ai]
    if bi:
        b = elements[bi]
    return (a, b)


def closest(target, elements, max_diff=None):
    try:
        el = min(elements, key=lambda e: abs(target-e))
        if max_diff is None or abs(el - target) < max_diff:
            return el
    except ValueError:
        pass


def floor(number, ndigits=0):
    if not ndigits:
        return math.floor(number)
    else:
        m = 10**ndigits
        return math.floor(number*m)/m

#second가 현재 진행중인 초 format 만
def format_time(seconds, full=False):
    l = ''
    s = seconds

    h = int(s/3600)
    if full or h:
        s = s-3600*h
        l += '%02d:' % h

    m = int(s/60)
    if full or m:
        s = s-60*m
        l += '%02d:' % m
    elif h:
        l += '00:'

    if full or s < seconds:
        l += '%02d' % s
    else:
        l += '%d' % s

    dec = s % 1
    if full or dec:
        l += ('%.3f' % dec)[1:]
    
    return l

def parse_time(string):
    parts = string.split(':')
    if len(parts) == 1:
        return float(parts[0])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    else:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    # for qt + debug
    QtCore.pyqtRemoveInputHook()

    # for qt + mpv
    locale.setlocale(locale.LC_NUMERIC, 'C')

    no_index = '--no-index' in sys.argv
    if no_index:
        sys.argv.remove('--no-index')
    args = docopt(doc)
    gui = GUI(args['<video-file>'], args['-s'], args['--mpv'], no_index)

    # for qt + ctrl-c
    signal.signal(signal.SIGINT, lambda *_: gui.interrupt())

    sys.exit(app.exec_())
