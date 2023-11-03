from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os
from PyQt5.QtWidgets import QShortcut, QVBoxLayout, QFileDialog, QLabel, QDialog, QListWidget, QLineEdit, QTextEdit, \
    QPushButton, QListWidgetItem, QMessageBox
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QPixmap, QImage, QKeySequence
import eyed3
from PIL import Image, ImageDraw, ImageFont
import random
import sqlite3


class NotesWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('DDWrite')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.notes_list = QListWidget()
        layout.addWidget(self.notes_list)

        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)

        self.content_input = QTextEdit()
        layout.addWidget(self.content_input)

        save_button = QPushButton('Сохранить')
        save_button.clicked.connect(self.save_note)
        layout.addWidget(save_button)

        delete_button = QPushButton('Удалить')
        delete_button.clicked.connect(self.delete_note)
        layout.addWidget(delete_button)

        open_button = QPushButton('Открыть')
        open_button.clicked.connect(self.open_note)
        layout.addWidget(open_button)
        self.notes_list.itemDoubleClicked.connect(self.open_note)

        self.setLayout(layout)

        # Загрузите существующие записи из базы данных
        self.load_notes()

    def save_note(self):
        title = self.title_input.text()
        content = self.content_input.toPlainText()

        if title and content:
            db_connection = sqlite3.connect("notes.db")
            cursor = db_connection.cursor()
            cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
            db_connection.commit()
            db_connection.close()

            self.title_input.clear()
            self.content_input.clear()
            self.load_notes()

    def delete_note(self):
        selected_item = self.notes_list.currentItem()

        if selected_item:
            note_id = selected_item.data(Qt.UserRole)
            db_connection = sqlite3.connect("notes.db")
            cursor = db_connection.cursor()
            cursor.execute("DELETE FROM notes WHERE id=?", (note_id,))
            db_connection.commit()
            db_connection.close()
            self.load_notes()

    def load_notes(self):
        db_connection = sqlite3.connect("notes.db")
        cursor = db_connection.cursor()
        cursor.execute("SELECT id, title FROM notes")
        notes = cursor.fetchall()
        db_connection.close()

        self.notes_list.clear()

        for note in notes:
            item = QListWidgetItem(note[1])
            item.setData(Qt.UserRole, note[0])
            self.notes_list.addItem(item)

    def open_note(self):
        selected_item = self.notes_list.currentItem()

        if selected_item:
            note_id = selected_item.data(Qt.UserRole)
            db_connection = sqlite3.connect("notes.db")
            cursor = db_connection.cursor()
            cursor.execute("SELECT title, content FROM notes WHERE id=?", (note_id,))
            note_data = cursor.fetchone()
            db_connection.close()

            if note_data:
                title, content = note_data
                note_text = f"Заголовок: {title}\n\n{content}"

                # Откройте диалоговое окно с полным содержанием заметки
                QMessageBox.information(self, 'Полная заметка', note_text)


class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('About')
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        about_text = QLabel(
            'MP3 Player created with DDCompany. Thank you for using it. Alpha 1.0 \n ctrl+e - files \n '
            'ctrl+p - play/pause \n ctrl+i - about')
        layout.addWidget(about_text)

        image_label = QLabel()
        pixmap = QPixmap("logo01.png")
        image_label.setPixmap(pixmap)
        layout.addWidget(image_label)

        self.setLayout(layout)


class MP3Player(object):
    def setupUi(self, MainWindow):
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalSlider = QtWidgets.QSlider(self.centralwidget)
        self.horizontalSlider.setGeometry(QtCore.QRect(0, 250, 271, 21))
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.horizontalSlider.setStyleSheet(
            """
            QSlider::groove:horizontal {
                border: 1px solid #ccc;
                background: white;
                height: 10px;
                margin: 5px 0;
            }
        
            QSlider::handle:horizontal {
                background: #333;
                border: 1px solid #ccc;
                width: 20px;
                height: 10px;
                margin: -5px 0;
                border-radius: 5px;
            }
            """
        )
        self.PlayPause = QtWidgets.QPushButton(self.centralwidget)
        self.PlayPause.setGeometry(QtCore.QRect(110, 270, 51, 31))
        font = QtGui.QFont()
        font.setFamily("MV Boli")
        font.setPointSize(26)
        self.PlayPause.setFont(font)
        self.PlayPause.setStyleSheet("QPushButton {border-radius: 20px\n"
                                     "rgb(255, 255, 255)}")
        self.PlayPause.setObjectName("PlayPause")
        self.left_sw = QtWidgets.QPushButton(self.centralwidget)
        self.left_sw.setGeometry(QtCore.QRect(70, 270, 31, 31))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.left_sw.setFont(font)
        self.left_sw.setObjectName("left_sw")
        self.right_sw = QtWidgets.QPushButton(self.centralwidget)
        self.right_sw.setGeometry(QtCore.QRect(170, 270, 31, 31))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.right_sw.setFont(font)
        self.right_sw.setObjectName("right_sw")
        self.name_song = QtWidgets.QLabel(self.centralwidget)
        self.name_song.setGeometry(QtCore.QRect(20, 10, 221, 21))
        self.name_song.setObjectName("name_song")
        self.name_song.setText('')
        self.volume = QtWidgets.QSlider(self.centralwidget)
        self.volume.setGeometry(QtCore.QRect(240, 40, 16, 160))
        self.volume.setValue(100)
        self.volume.setOrientation(QtCore.Qt.Vertical)
        self.volume.setObjectName("volume")
        self.volume.setStyleSheet(
            """
            QSlider::groove:vertical {
                border: 1px solid #ccc;
                background: white;
                width: 10px;
                margin: 0 5px;
            }
        
            QSlider::handle:vertical {
                background: #333;
                border: 1px solid #ccc;
                width: 10px;
                height: 20px;
                margin: 0 -5px;
            }
            """
        )
        self.folder = QtWidgets.QPushButton(self.centralwidget)
        self.folder.setGeometry(QtCore.QRect(235, 6, 31, 21))
        self.folder.setObjectName("folder")
        self.photo_mp3 = QtWidgets.QLabel(self.centralwidget)
        self.photo_mp3.setGeometry(QtCore.QRect(60, 60, 141, 151))
        self.photo_mp3.setObjectName("photo_mp3")
        self.ddwrite_b = QtWidgets.QPushButton(self.centralwidget)
        self.ddwrite_b.setGeometry(QtCore.QRect(280, 290, 81, 31))
        self.ddwrite_b.setObjectName("ddwrite_b")
        self.ddwrite_b.clicked.connect(self.create_database)
        self.ddwrite_b.clicked.connect(self.open_notes_window)
        self.listWidget = QtWidgets.QListWidget(self.centralwidget)
        self.listWidget.setGeometry(QtCore.QRect(280, 10, 151, 281))
        self.listWidget.setObjectName("listWidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 230, 50, 20))
        self.label.setObjectName("label")
        self.label.setText('00:00')
        self.time2 = QtWidgets.QLabel(self.centralwidget)
        self.time2.setGeometry(QtCore.QRect(230, 230, 50, 20))
        self.time2.setObjectName("time2")
        self.time2.setText('00:00')
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 451, 18))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.video_widget = QVideoWidget()
        self.playlist_items = []
        self.current_song = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateTime)
        self.last_position = 0

        # Создаем экземпляр класса QMediaPlayer
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)

        self.folder.clicked.connect(self.addFiles)
        self.PlayPause.clicked.connect(self.play)
        self.right_sw.clicked.connect(self.playNext)
        self.horizontalSlider.sliderReleased.connect(self.setPosition)
        self.volume.valueChanged.connect(self.setVolume)
        self.left_sw.clicked.connect(self.playSNext)
        self.about_button = QtWidgets.QPushButton(self.centralwidget)
        self.about_button.setGeometry(QtCore.QRect(410, 290, 21, 20))
        self.about_button.setObjectName("about_button")
        self.about_button.clicked.connect(self.showAboutDialog)
        self.add_shortcuts()

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.PlayPause.setText(_translate("MainWindow", "▶️"))
        self.left_sw.setText(_translate("MainWindow", "⏪"))
        self.right_sw.setText(_translate("MainWindow", "⏩"))
        self.name_song.setText(_translate("MainWindow", " "))
        self.folder.setText(_translate("MainWindow", "📁"))
        self.photo_mp3.setText(_translate("MainWindow", "DDPlay"))
        self.label.setText(_translate("MainWindow", "00:00"))
        self.time2.setText(_translate("MainWindow", "00:00"))
        self.about_button.setText(_translate("MainWindow", "!"))
        self.ddwrite_b.setText(_translate("DDPlay", "DDWrite"))

    def addFiles(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_paths, _ = QFileDialog.getOpenFileNames(None, "Выберите MP3 файлы", "", "MP3 Files (*.mp3);;All Files (*)",
                                                     options=options)

        if file_paths:
            for file_path in file_paths:
                self.listWidget.addItem(os.path.basename(file_path))
                self.playlist_items.append(file_path)

    def play(self):
        if not self.playlist_items:
            return

        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.last_position = self.media_player.position()
            self.PlayPause.setText("▶️")
        else:
            file_path = self.playlist_items[self.current_song]
            media_content = QMediaContent(QUrl.fromLocalFile(file_path))
            self.media_player.setMedia(media_content)

            if self.last_position > 0:
                self.media_player.setPosition(self.last_position)

            self.media_player.play()
            self.PlayPause.setText("⏸️")
            self.name_song.setText(os.path.basename(file_path))
            self.load_album_cover(file_path)
        file_path = self.playlist_items[self.current_song]
        self.timer.start(1000)

    def play2(self):
        if not self.playlist_items:
            return

        file_path = self.playlist_items[self.current_song]
        media_content = QMediaContent(QUrl.fromLocalFile(file_path))
        self.media_player.setMedia(media_content)

        self.media_player.play()
        self.name_song.setText(os.path.basename(file_path))
        self.PlayPause.setText('⏸️')
        self.load_album_cover(file_path)
        file_path = self.playlist_items[self.current_song]

    def playNext(self):
        if not self.playlist_items:
            return

        self.current_song += 1
        if self.current_song >= len(self.playlist_items):
            self.current_song = 0
        self.play2()
        self.label.setText('00:00')
        self.time2.setText('00:00')
        self.horizontalSlider.setValue(0)

    def playSNext(self):
        if not self.playlist_items:
            return

        self.current_song -= 1
        if self.current_song >= len(self.playlist_items):
            self.current_song = 0
        self.label.setText('00:00')
        self.time2.setText('00:00')
        self.horizontalSlider.setValue(0)
        self.play2()

    def setVolume(self, value):
        volume = int(value)
        self.media_player.setVolume(volume)

    def showAboutDialog(self):
        about_dialog = AboutDialog()
        about_dialog.exec()

    def setPosition(self):
        position = self.horizontalSlider.value() / 100.0
        position_ms = int(position * self.media_player.duration())
        self.media_player.setPosition(position_ms)

    def create_database(self):
        db_connection = sqlite3.connect("notes.db")
        cursor = db_connection.cursor()

        # Создаем таблицу notes, если ее еще нет
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT
        )
        """)

        db_connection.commit()
        db_connection.close()

    def open_notes_window(self):
        notes_window = NotesWindow()
        notes_window.exec()

    def updateTime(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            total_time = self.media_player.duration()
            current_time = self.media_player.position()
            total_time_str = self.formatTime(total_time)
            current_time_str = self.formatTime(current_time)
            time_str = f"{current_time_str}"
            time_str2 = f'{total_time_str}'
            self.label.setText(time_str)
            self.time2.setText(time_str2)

            if total_time > 0:
                self.horizontalSlider.setValue(round(current_time / total_time * 100))
            else:
                # Если total_time равно 0, то установите показатели времени и ползунка в исходное состояние
                self.label.setText('00:00')
                self.time2.setText('00:00')
                self.horizontalSlider.setValue(0)

    def load_album_cover(self, file_path):
        audiofile = eyed3.load(file_path)
        if audiofile.tag:
            image = audiofile.tag.images.get('')
            if image:
                image_data = image.image_data
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                self.photo_mp3.setPixmap(pixmap)
            else:
                # Если обложки альбома нет, создайте изображение с градиентным фоном и рандомным расположением "DD"
                image_width = 141
                image_height = 151

                # Создайте пустое изображение с градиентным фоном
                image = Image.new('RGBA', (image_width, image_height))

                # Создайте градиентный фон (от фиолетового к синему)
                for y in range(image_height):
                    r = int(150 + y * 1.3)  # Красный цвет
                    g = int(0 + y * 1.3)  # Зеленый цвет
                    b = int(255 - y * 1.3)  # Синий цвет
                    for x in range(image_width):
                        image.putpixel((x, y), (r, g, b, 255))

                draw = ImageDraw.Draw(image)

                dd_text = "DD!"
                font = ImageFont.truetype("arial.ttf", 36)  # Установите шрифт и размер
                text_bbox = draw.textbbox((0, 0), dd_text, font=font)
                x = random.randint(0, image_width - text_bbox[2])
                y = random.randint(0, image_height - text_bbox[3])
                draw.text((x, y), dd_text, fill=(255, 255, 255), font=font)

                # Преобразуйте изображение Pillow в QPixmap и отобразите его
                pixmap = QPixmap.fromImage(
                    QImage(image.tobytes("raw", "RGBA"), image.width, image.height, QImage.Format_RGBA8888))
                self.photo_mp3.setPixmap(pixmap)
        else:
            # Если метаданные недоступны, установите пустую обложку
            self.photo_mp3.clear()

    def add_shortcuts(self):
        # Комбинация клавиш Ctrl+E для вызова функции addFiles
        shortcut_add_files = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_E), self.centralwidget)
        shortcut_add_files.activated.connect(self.addFiles)

        # Комбинация клавиш Ctrl+I для открытия окна About
        shortcut_about = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_I), self.centralwidget)
        shortcut_about.activated.connect(self.showAboutDialog)

        # Комбинация клавиш Ctrl+P для вызова функции PlayPause
        shortcut_play_pause = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_P), self.centralwidget)
        shortcut_play_pause.activated.connect(self.play)

        shortcut_write = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_W), self.centralwidget)
        shortcut_write.activated.connect(self.open_notes_window)

    def formatTime(self, milliseconds):
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes:02}:{seconds:02}"


# DDC Code

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = MP3Player()
    ui.setupUi(MainWindow)
    MainWindow.show()
    MainWindow.setObjectName("DDPlay")
    MainWindow.setWindowTitle("DDPlay")
    MainWindow.resize(451, 377)
    sys.exit(app.exec_())
