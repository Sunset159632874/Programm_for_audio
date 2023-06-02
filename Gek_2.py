import os
import json
from pydub import AudioSegment
from pydub.silence import split_on_silence
from vosk import Model, KaldiRecognizer
from nltk.tokenize import word_tokenize
import vosk
import re
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from functools import partial
from PIL import Image, ImageTk
from tkinter.messagebox import showerror, showwarning, showinfo
from tkinter.scrolledtext import ScrolledText
import librosa
import soundfile as sf
import wave
import string
model_path = "vosk-model-small-ru-0.4"
vosk_model = vosk.Model(model_path)
def convert_audio(input_file, output_file, target_sample_rate):
    audio = AudioSegment.from_file(input_file)
    converted_audio = audio.set_frame_rate(target_sample_rate).set_channels(1)
    converted_audio.export(output_file, format='wav')

def split_audio(input_file, output_directory, fragment_duration):
    audio = AudioSegment.from_file(input_file)
    total_duration = len(audio)
    
    fragments = []
    start_time = 0
    
    while start_time + fragment_duration <= total_duration:
        end_time = start_time + fragment_duration
        fragment = audio[start_time:end_time]
        fragments.append(fragment)
        
        start_time = end_time
    
    return fragments

def remove_silence(audio):
    # Удаление пауз перед первым словом
    #non_silent_audio = audio.strip_silence(silence_len=100, silence_thresh=-40, padding=100)
    segments = split_on_silence(audio, min_silence_len=500, silence_thresh=-40)
    non_silent_audio = segments[0]
    for segment in segments[1:-1]:
        non_silent_audio += segment
   
    return non_silent_audio

def transcribe_fragment(audio_file, model_path):
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)

    with open(audio_file, 'rb') as f:
        audio_data = f.read()

    recognizer.AcceptWaveform(audio_data)

    result = json.loads(recognizer.Result())
    transcription = result['text']
    
    return transcription


def remove_silence_off():
    # Загрузка аудиофайла
    audio_path =filedialog.askopenfilename()
    audio, sample_rate = librosa.load(audio_path)

    # Вычисление энергии аудиофайла
    energy = librosa.feature.rms(y = audio)

    # Поиск первого и последнего ненулевого сэмпла
    non_silent_indices = librosa.effects.split(audio, top_db=20)
    start_sample = non_silent_indices[0, 0]
    end_sample = non_silent_indices[-1, 1]

    # Обрезка аудиофайла
    trimmed_audio = audio[start_sample:end_sample]
    output_path = filedialog.asksaveasfilename()
    # Сохранение обрезанного аудиофайла
    sf.write(output_path, trimmed_audio, sample_rate)

       # Вычисление длительности аудиофайла до и после обрезки
    duration_before = librosa.get_duration(y = audio, sr = sample_rate)
    duration_after = librosa.get_duration(y = trimmed_audio, sr = sample_rate)

    text_1.insert('end', '\nДлительность аудиофайла до обрезки: {:.2f} секунд'.format(duration_before))
    text_1.insert('end', '\nДлительность аудиофайла после обрезки: {:.2f} секунд'.format(duration_after))

def tran_audio():
    converted_audio = "D:/converted_audio.wav"
    input_audio =filedialog.askopenfilename()
    audio = AudioSegment.from_file(input_audio)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(converted_audio, format="wav")

    model_path = "D:/Studio/Gek_2/Gek_2/vosk-model-small-ru-0.4"

    # Загрузка модели
    model = Model(model_path)

    # Открытие аудиофайла
    audio_file = wave.open(converted_audio, "rb")

    # Создание распознавателя
    recognizer = KaldiRecognizer(model, audio_file.getframerate())

    # Чтение аудиофайла по блокам и распознавание речи
    while True:
        data = audio_file.readframes(4000)
        if len(data) == 0:
            break
        recognizer.AcceptWaveform(data)

    # Получение распознанного текста
    result = json.loads(recognizer.Result())

    # Вывод распознанного текста
    transcription = result["text"]
    text_1.insert('end', transcription)
    output_text = filedialog.asksaveasfilename()
    with open(output_text, "w", encoding="utf-8") as f:
        f.write(transcription)
    text_1.insert('end', "\nТранскрибирвоание сохранено в файл формата .txt")
# Закрытие аудиофайла
    audio_file.close()

# Удаление временного конвертированного аудиофайла
    os.remove(converted_audio)

def srav():
    output_text = filedialog.askopenfilename()
    comparison_text = filedialog.askopenfilename()
    with open(output_text, "r", encoding="utf-8") as f:
        saved_text = f.read()

    with open(comparison_text, "r", encoding="utf-8") as f:
        comparison_text = f.read()

    # Замена буквы "ё" на букву "е"
    saved_text = saved_text.replace("ё", "е")
    comparison_text = comparison_text.replace("ё", "е")

    # Нормализация текста для сравнения
    translator = str.maketrans("", "", string.punctuation)
    saved_text_normalized = saved_text.lower().translate(translator)
    comparison_text_normalized = comparison_text.lower().translate(translator)

    # Разделение текста на слова
    saved_words = saved_text_normalized.split()
    comparison_words = comparison_text_normalized.split()

    # Определение отличающихся слов
    differing_words = [word for word in saved_words if word not in comparison_words]

    if differing_words:
        text_1.insert('end',"Отличающиеся слова:")
        for word in differing_words:
            index = saved_words.index(word)
            corresponding_word = comparison_words[index] if index < len(comparison_words) else "-"
            text_1.insert('end',f"\nСлово: {word}, Оригинал: {corresponding_word}")
    else:
        text_1.insert('end',"Нет отличающихся слов.")


def transcribe_audio(audio_path, first_word, last_word):
    # Загрузка аудиофайла с помощью PyDub
    audio = AudioSegment.from_file(audio_path)

    # Удаление пауз перед первым словом и после последнего слова
    trimmed_audio = remove_silence(audio)

    # Конвертирование в формат WAV с параметрами, соответствующими требованиям Vosk
    trimmed_audio = trimmed_audio.set_frame_rate(16000).set_channels(1)

    # Сохранение временного WAV-файла для передачи в Vosk
    temp_wav_path = "temp.wav"
    trimmed_audio.export(temp_wav_path, format="wav")

    # Открываем временный WAV-файл
    wf = vosk.KaldiRecognizer(vosk_model, 16000)

    # Читаем данные из временного WAV-файла и передаем их в распознаватель речи
    with open(temp_wav_path, "rb") as wav_file:
        while True:
            data = wav_file.read(4000)
            if len(data) == 0:
                break
            wf.AcceptWaveform(data)

    # Получаем результаты распознавания
    result = json.loads(wf.FinalResult())
    text = result["text"]

    # Находим индекс первого и последнего слова в тексте
    first_word_index = text.find(first_word)
    last_word_index = text.rfind(last_word)

    # Проверяем, что оба слова найдены
    if first_word_index == -1 and last_word_index == -1:
        
        print('Фрагмент не найден')
        text = 0
        fragment = 0
        return text, fragment
    # Вычисляем длительность фрагмента на основе индексов первого и последнего слова
    first_word_time = trimmed_audio.duration_seconds * first_word_index / len(text)
    last_word_time = trimmed_audio.duration_seconds * last_word_index / len(text)
    fragment_start_time = int(first_word_time * 980)
    fragment_end_time = int(last_word_time * 1030)

    # Обрезаем аудиофайл до нужного фрагмента
    fragment = trimmed_audio[fragment_start_time:fragment_end_time]

    # Удаляем временный WAV-файл
    os.remove(temp_wav_path)
    # Возвращаем текстовый результат и фрагмент аудио
    
    return text, fragment

def extract_text_fragment(file_path, first_word, last_word):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Преобразование текста: удаление заглавных букв и знаков препинания
    content = content.lower()
    # Разделение содержимого файла на слова
    words = content.split()

    # Поиск индекса первого слова
    start_index = None
    for i, word in enumerate(words):
        if word.strip(".,!?") == first_word:
            start_index = i
            break

    # Поиск индекса последнего слова
    end_index = None
    for i in range(len(words) - 1, -1, -1):
        if words[i].strip(".,!?") == last_word:
            end_index = i
            break

    # Если найдены оба индекса
    if start_index is not None and end_index is not None:
        # Формирование фрагмента текста
        fragment = ' '.join(words[start_index:end_index+1])
        text_1.insert('end',f'\nНайденный фрагмент:{fragment}')
        return fragment
    else:
        print('Не найдено')


def gg(audio_files):
    file1_path = ryb.get()
    print(audio_files)
    #file1_path = 'C:/Users/79196/OneDrive/Рабочий стол/1.txt'
    

    target_sample_rate = 16000  # Целевая частота дискретизации
    fragment_duration = int(times.get()) * 1000  # Длительность фрагмента в миллисекундах
    print(fragment_duration)
    tetris = filedialog.askdirectory()
    output_directory = tetris +'/output_directory'  # Директория для сохранения фрагментов
    match_fragments = tetris +'/match_fragments'
    textovye = tetris +'/Models'
    # Проверка и создание директории output_directory
    os.makedirs( output_directory, exist_ok=True)
    os.makedirs( match_fragments, exist_ok=True)
    os.makedirs( textovye, exist_ok=True)

    for audio_file in audio_files:
        converted_audio_file = os.path.join(output_directory, f'converted_{os.path.basename(audio_file)}')
        convert_audio(audio_file, converted_audio_file, target_sample_rate)

    if audio_files:
        # Поиск самого короткого файла
        shortest_file = min(audio_files, key=lambda x: os.path.getsize(x))
        print(f'Самый короткий аудиофайл: {shortest_file}')
        audio_files.pop(audio_files.index(shortest_file))
        # Разделение аудио на фрагменты
        fragments = split_audio(os.path.join(output_directory, f'converted_{os.path.basename(shortest_file)}'), output_directory, fragment_duration)

        for audio in audio_files:
        # Транскрибирование и определение первого и последнего слова для каждого фрагмента
            for i, fragment in enumerate(fragments):
                fragment_file = os.path.join(output_directory, f'fragment_{i}.wav')
                fragment.export(fragment_file, format='wav')

                transcription = transcribe_fragment(fragment_file, model_path)

                # Токенизация текста на слова с помощью NLTK
                tokens = word_tokenize(transcription)

                # Определение первого и последнего слова
                first_word = tokens[0] if tokens else None
                last_word = tokens[-1] if tokens else None
                text, audio_fragment = transcribe_audio(audio, first_word, last_word)
                
                fragment_path = os.path.join(match_fragments,f"audio_fragment{i}.wav")
                audio_fragment.export(fragment_path, format="wav")


                audio_duration = len(AudioSegment.from_file(audio)) / 1000  # Продолжительность аудио в секундах
                fragment_start_time = len(AudioSegment.from_file(fragment_path)) / 1000  # Время начала фрагмента в секундах
                fragment_end_time = fragment_start_time + len(audio_fragment) / 930  # Время окончания фрагмента в секундах
                if text == 0 and audio_fragment == 0 or (fragment_end_time-fragment_start_time)>15.0 or (fragment_end_time-fragment_start_time)<12.0:
                    os.remove(match_fragments + f"/audio_fragment{i}.wav")
                    print('Фрагмент не найден')
                    continue
        
                #print("Текст:", text)
            
                text_1.insert('end',f'\nФрагмент {i+1}:')
            

                text_1.insert('end',f'    \nТранскрипция: {transcription}')
                text_1.insert('end',f'    \nПервое слово: {first_word}')
                text_1.insert('end',f'    \nПоследнее слово: {last_word}')

            
                
                #print("Фрагмент аудио сохранен в", fragment_path)
                print(transcribe_fragment(fragment_path, model_path))

                popolam = extract_text_fragment(file1_path, first_word, last_word)
                file_path = os.path.join(textovye + f"/Ready_model{i}.txt")
                if popolam == None or fragment_end_time-fragment_start_time==0:
                    print('Фрагмент не найден')
                else:
                    with open(file_path, "w") as file:
                        file.write(popolam)
                    text_1.insert('end','\nФрагмент сохранен в файл формата .txt')
                    text_1.insert('end',f"\nВремя найденного фрагмента: {fragment_end_time-fragment_start_time} сек")
            os.remove(converted_audio_file)

audio_files = []
audio_files1 = []
def mass(okn):
    per0 = b00.get()
    per1 = b01.get()
    per2 = b02.get()

    if  per0 != '':
        audio_files.append(okn + f'/{per0}')
        audio_files1.append(per0)
        ryb1.set(audio_files1)
    if  per1 != '':
        audio_files.append(okn + f'/{per1}')
        audio_files1.append(per1)
        ryb1.set(audio_files1)
    if  per2 != '':
        audio_files.append (okn + f'/{per2}')
        audio_files1.append(per2)
        ryb1.set(audio_files1)

def ish_tekst():
    ish_text = filedialog.askopenfilename()
    ryb.set(ish_text)

def delete_text():
    text_1.delete("1.0", END)

def del_mas():
    audio_files.clear()
    audio_files1.clear()
    ryb1.set(audio_files1)





root = Tk()     # создаем корневой объект - окно
root.title("AudioFile changing")     # устанавливаем заголовок окна
root.geometry("1300x800")    # устанавливаем размеры окна
ttk.Style().theme_use("classic")
style = ttk.Style()
# Устанавливаем стиль для кнопки, используя параметр "TButton"
style.configure("TButton", justify="center")
root["bg"] = "gray22"
logo_image = PhotoImage(file='C:/Users/79196/OneDrive/Рабочий стол/image.png')
photo=ttk.Label(root, image=logo_image)
photo.place(x=10, y=20, width=100, height=100)
Zagolovok = ttk.Label(root, text="AudioFile changing",font="Arial 45",background = "gray22").place(x=120, y=40, width=1000, height=100)

file = filedialog.askdirectory()
papka= []
for root1, dirs, files in os.walk(file):
    for filename in dirs:
        if os.path.exists(filename):
            continue
        papka.append(filename)
object_var = StringVar()
combobox = ttk.Combobox(textvariable=object_var, values = papka)
combobox.place(x=10, y=150, height=50, width = 100)

s0=ttk.Label(text = 'Блок 1')
s0.place(x=126, y=150, height=50, width = 250)
s1=ttk.Label(text = 'Блок 2')
s1.place(x=392, y=150, height=50, width = 250)
s2=ttk.Label(text = 'Блок 3')
s2.place(x=658, y=150, height=50, width = 250)
s3= ttk.Label(text = 'Введите время в сек')
s3.place(x=924, y=150, height=50, width = 250)

b00 = StringVar()
b01 = StringVar()
b02 = StringVar()


def okny():

    okn = file + f'/{object_var.get()}'
    for root1, dirs, files in os.walk(okn):
        for filename in files:
            if filename in b11 or filename in b12 or filename in b13:
                continue
            if filename == f'2023-04-10_{object_var.get()}_1.wav':
                b11.append(filename)
                
            elif filename == f'2023-04-10_{object_var.get()}_2.wav':
                b12.append(filename)
            elif filename == f'2023-04-10_{object_var.get()}_3.wav':
                b13.append(filename)
    #b00 = StringVar()
    b0=ttk.Combobox(textvariable=b00, values = b11)
    b0.place(x=126, y=210, height=50, width = 250)

    #b01 = StringVar()
    b1=ttk.Combobox(textvariable=b01, values = b12)
    b1.place(x=392, y=210, height=50, width = 250)

    #b02 = StringVar()
    b2=ttk.Combobox(textvariable=b02, values = b13)
    b2.place(x=658, y=210, height=50, width = 250)
    btn_choose = ttk.Button(text="Выбрать \nфайл", command=partial(mass,okn)).place(x=10, y=270, height=55, width = 100)
b11 = []
b12 = []
b13 = []
pap = ttk.Button(text="Выбрать \n папку", command=okny) # создаем кнопку из пакета ttk
pap.place(x=10, y=210, height=55, width = 100)


times = ttk.Entry()
times.place(x=924, y=210, height=50, width = 250)
okna = ttk.Button(text="Найти\n модель", command=partial(gg,audio_files)) # создаем кнопку из пакета ttk
okna.place(x=10, y=330, height=55, width = 100)

ryb = StringVar()
lbl_text_file = ttk.Label(textvariable = ryb)
#lbl_text_file.place(x=1000, y=500, width=256, height=50)
text_file = ttk.Button(text = 'Выбор \nтекста', command = ish_tekst).place(x=1190, y=150, height=55, width = 100)

text_1 = Text(root, height=5, width=20)
text_1.place(x=250, y=480, height=290, width = 800)
scrollbar = Scrollbar(root)
text_1.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=text_1.yview)
scrollbar.place(x=1050, y=479.7, height=290, width = 15)

ryb1 = StringVar()
delpo = ttk.Label(textvariable = ryb1).place(x=450, y=295, width=400, height=40)
delpo1 = ttk.Button(text= 'Очистить данные',command = del_mas).place(x=550, y=340, width=200, height=40)

ishod_dan = ttk.Label(text = 'Исходные данные').place(x=550, y=270, width=200, height=20)

button = ttk.Button(text="Очистить", command=delete_text)
button.place(x=1075, y=720, height=50, width = 100)

Finish = ttk.Label(root, text="Результат:",font="Arial 30",background = "gray22").place(x=250, y=380, width=400, height=100)

paus = ttk.Button(text="Удалить\n паузы", command=remove_silence_off).place(x=10, y=390, height=55, width = 100)

transkrib = ttk.Button(text="Транскрибировать\n аудиофайл", command=tran_audio).place(x=1080, y=270, height=55, width = 200) 

sravnen =  ttk.Button(text="Сравнить \nc оригиналом", command=srav).place(x=1080, y=335, height=55, width = 200)


root.mainloop()

