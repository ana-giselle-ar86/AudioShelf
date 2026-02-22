# frames/player/book_loader.py
# Copyright (c) 2025-2026 Mehdi Rajabi
# License: GNU General Public License v3.0 (See LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import wx
import os
import logging
from datetime import datetime
from typing import Optional
from database import db_manager
from i18n import _
from . import event_handlers

class BookLoader:
    def __init__(self, frame):
        self.frame = frame

    def load_book_data(self):
        frame = self.frame
        try:
            if not frame.book_title:
                details = db_manager.get_book_details(frame.book_id)
                frame.book_title = details['title'] if details else _("Unknown Book")

            frame.SetTitle(frame.book_title)
            if frame.title_text:
                frame.title_text.SetLabel(frame.book_title)

            frame.book_files_data = db_manager.get_book_files(frame.book_id)
            if not frame.book_files_data:
                raise ValueError(f"No playable files found for book_id {frame.book_id}")

            frame.book_file_durations = [duration for (_, _, _, duration) in frame.book_files_data]
            frame.total_book_duration_ms = sum(frame.book_file_durations)

            state = db_manager.get_playback_state(frame.book_id)

            file_index = 0
            start_pos_ms = 0
            start_rate = 1.0
            eq_settings = "0,0,0,0,0,0,0,0,0,0"
            is_eq_enabled = False

            if state:
                file_index = state.get('last_file_index', 0)
                start_pos_ms = state.get('last_position_ms', 0)
                start_rate = state.get('last_speed_rate', 1.0)
                eq_settings = state.get('last_eq_settings', eq_settings)
                is_eq_enabled = state.get('is_eq_enabled', is_eq_enabled)

                try:
                    threshold_sec = int(db_manager.get_setting('smart_resume_threshold_sec') or 300)
                    rewind_ms = int(db_manager.get_setting('smart_resume_rewind_ms') or 0)
                    last_played_str = state.get('last_played_at')

                    if rewind_ms > 0 and start_pos_ms > 0 and last_played_str:
                        last_played_dt = datetime.strptime(last_played_str, '%Y-%m-%d %H:%M:%S.%f')
                        diff_seconds = (datetime.now() - last_played_dt).total_seconds()

                        if diff_seconds > threshold_sec:
                            start_pos_ms = max(0, start_pos_ms - rewind_ms)
                            logging.info(f"Smart Rewind applied: {rewind_ms}ms back.")
                except Exception as e:
                    logging.warning(f"Could not apply smart rewind: {e}")

            if not (0 <= file_index < len(frame.book_files_data)):
                logging.warning(f"Saved file index {file_index} out of bounds. Resetting to 0.")
                file_index = 0
                start_pos_ms = 0

            frame.current_file_index = file_index

            try:
                frame.current_file_duration_ms = frame.book_file_durations[file_index]
                (frame.current_file_id, frame.current_file_path, _, _) = frame.book_files_data[file_index]
            except IndexError:
                raise ValueError(f"Critical index error: Could not retrieve file at index {file_index}")

            frame.start_pos_ms = start_pos_ms
            frame.current_target_rate = start_rate
            frame.previous_target_rate = frame.current_target_rate
            frame.current_eq_settings = eq_settings
            frame.is_eq_enabled = is_eq_enabled

            if frame.nvda_focus_label and frame.current_file_path:
                file_name = os.path.basename(frame.current_file_path)
                frame.nvda_focus_label.SetLabel(file_name)

            frame._update_audio_filters()

        except Exception as e:
            logging.error(f"Error loading book data: {e}", exc_info=True)
            wx.MessageBox(_("Error loading book data. Please check logs."), _("Load Error"),
                          wx.OK | wx.ICON_ERROR, parent=frame)
            wx.CallAfter(lambda: event_handlers.on_escape(frame, None))

    def start_playback(self):
        frame = self.frame
        if frame.is_exiting or not frame.engine:
            return

        frame.engine_to_frame_index_map.clear()
        file_paths_to_load = []

        for i, (file_id, path, file_index, duration) in enumerate(frame.book_files_data):
            file_paths_to_load.append(path)
            frame.engine_to_frame_index_map.append(i)

        if not file_paths_to_load:
            logging.error("start_playback: No files found in DB list.")
            wx.MessageBox(_("Error: No audio files found for this book."),
                          _("Playback Error"), wx.OK | wx.ICON_ERROR, parent=frame)
            wx.CallAfter(lambda: event_handlers.on_escape(frame, None))
            return

        try:
            new_start_index = frame.engine_to_frame_index_map.index(frame.current_file_index)
        except ValueError:
            logging.warning("Index mismatch. Resetting to start.")
            new_start_index = 0
            frame.current_file_index = frame.engine_to_frame_index_map[0]
            (frame.current_file_id, frame.current_file_path, _, _) = frame.book_files_data[0]
            frame.start_pos_ms = 0

        success = frame.engine.load_playlist(
            file_paths=file_paths_to_load,
            start_index=new_start_index,
            start_time_ms=frame.start_pos_ms,
            rate=frame.current_target_rate
        )

        if success:
            frame.engine.play()
            frame.is_playing = True
            if not frame.ui_timer.IsRunning():
                frame.ui_timer.Start(1000)
            if frame.nvda_focus_label and not frame.nvda_focus_label.IsBeingDeleted():
                frame.nvda_focus_label.SetFocus()
        else:
            logging.error("Engine failed to load playlist.")
            wx.MessageBox(_("Error: Could not load the audio file."),
                          _("Playback Error"), wx.OK | wx.ICON_ERROR, parent=frame)
            frame.is_playing = False
            wx.CallAfter(lambda: event_handlers.on_escape(frame, None))

    def _clear_current_book_state(self):
        frame = self.frame
        frame.book_id = -1
        frame.book_title = ""
        frame.book_files_data.clear()
        frame.book_file_durations.clear()
        frame.total_book_duration_ms = 0
        frame.current_file_index = 0
        frame.current_file_id = None
        frame.current_file_path = None
        frame.current_file_duration_ms = 0
        frame.is_playing = False
        frame.start_pos_ms = 0
        frame.current_target_rate = 1.0
        frame.previous_target_rate = 1.0
        frame.engine_to_frame_index_map.clear()
        frame.loop_point_a_ms = None
        frame.is_file_looping = False
        frame.save_state_counter = 0
        frame.current_eq_settings = "0,0,0,0,0,0,0,0,0,0"
        frame.is_eq_enabled = False

    def load_new_book(self, new_book_id: int, new_book_title: str):
        frame = self.frame
        if frame.is_exiting:
            return

        logging.info(f"Switching to Book ID {new_book_id}...")

        if frame.engine:
            current_time = 0
            try:
                current_time = frame.engine.get_time()
            except Exception as e:
                logging.warning(f"Could not get time for saving old book: {e}")

            if current_time > 60000:
                if frame.parent_frame and hasattr(frame.parent_frame, 'update_history_list'):
                    wx.CallAfter(frame.parent_frame.update_history_list)

            event_handlers.save_playback_state(frame, final_time_ms=current_time)
            frame.engine.stop()
            
            if frame.ui_timer.IsRunning():
                frame.ui_timer.Stop()

        self._clear_current_book_state()
        frame.book_id = new_book_id
        frame.book_title = new_book_title
        
        self.load_book_data()
        self.start_playback()