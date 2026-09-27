"""Генератор музыкальных треков.

Каждый запуск создаёт ОДИН уникальный MIDI-файл.
Пространство возможных треков — десятки тысяч комбинаций.
"""

import random
import sys
import time
from midiutil import MIDIFile


# --- ПРОСТРАНСТВО ГЕНЕРАЦИИ ---
# Считаем: 13 × 15 × 3 × 10 × 4 × 3 × 2 = 140 400 комбинаций

# 1. Тональности (13)
KEYS = [
    ("C", 0), ("C#", 1), ("D", 2), ("D#", 3), ("E", 4), ("F", 5),
    ("F#", 6), ("G", 7), ("G#", 8), ("A", 9), ("A#", 10), ("B", 11),
    ("Gm", 7),  # дополнительная минорная тональность
]

# 2. Прогрессии (15)
# Каждая — список (ступень в полутонах, тип аккорда)
PROGRESSIONS = {
    "Pop_I_V_vi_IV":   [(0, "M"), (7, "M"), (9, "m"), (5, "M")],
    "Pop_vi_IV_I_V":   [(9, "m"), (5, "M"), (0, "M"), (7, "M")],
    "Pop_I_IV_vi_V":   [(0, "M"), (5, "M"), (9, "m"), (7, "M")],
    "Andalusian":      [(0, "m"), (7, "M"), (5, "M"), (4, "M")],
    "Minor_i_VI_III_VII": [(0, "m"), (8, "M"), (3, "M"), (7, "M")],
    "Minor_i_VII_VI_V":  [(0, "m"), (10, "M"), (8, "M"), (7, "M")],
    "Ballad_I_V_vi_IV":  [(0, "M"), (7, "M"), (9, "m"), (5, "M")],
    "Ballad_vi_IV_I_V":  [(9, "m"), (5, "M"), (0, "M"), (7, "M")],
    "Jazz_ii_V_I":       [(2, "m"), (7, "M"), (0, "M"), (0, "M")],
    "Jazz_I_vi_ii_V":    [(0, "M"), (9, "m"), (2, "m"), (7, "M")],
    "Blues_I_IV_V":      [(0, "M"), (5, "M"), (7, "M"), (0, "M")],
    "Dorian_i_IV":       [(0, "m"), (5, "M"), (0, "m"), (10, "M")],
    "Mixolydian_I_VII":  [(0, "M"), (10, "M"), (0, "M"), (5, "M")],
    "Chromatic_Descent": [(0, "M"), (11, "dim"), (10, "M"), (9, "m")],
    "Epic_i_VI_III_VII": [(0, "m"), (8, "M"), (3, "M"), (10, "M")],
}

# 3. Темповые диапазоны (3)
TEMPO_RANGES = {
    "slow":   (60, 80),
    "medium": (80, 110),
    "fast":   (110, 140),
}

# 4. Инструменты (10)
INSTRUMENTS = [
    (0, "Acoustic Grand Piano"),
    (1, "Bright Acoustic Piano"),
    (4, "Electric Piano"),
    (24, "Acoustic Guitar (nylon)"),
    (25, "Acoustic Guitar (steel)"),
    (48, "String Ensemble 1"),
    (49, "String Ensemble 2"),
    (80, "Lead 1 (square)"),
    (81, "Lead 2 (sawtooth)"),
    (88, "Pad 1 (new age)"),
]

# 5. Варианты мелодии (4)
MELODY_STYLES = [
    "chord_tone",   # ноты из аккорда
    "arpeggio",     # разложенный аккорд
    "scale_run",    # гаммообразное движение
    "sparse",       # редкие ноты
]

# 6. Варианты баса (3)
BASS_STYLES = [
    "root",       # только корень
    "root_fifth", # корень + квинта
    "walking",    # движение по аккорду
]

# 7. Октава мелодии (2)
MELODY_OCTAVES = [12, 24]


# --- ЛОГИКА ГЕНЕРАЦИИ ---

CHORD_TYPES = {
    "M":   [0, 4, 7],
    "m":   [0, 3, 7],
    "7":   [0, 4, 7, 10],
    "maj7":[0, 4, 7, 11],
    "min7":[0, 3, 7, 10],
    "dim": [0, 3, 6],
}


def get_chord_notes(root: int, chord_type: str) -> list:
    """Возвращает MIDI-ноты аккорда."""
    return [root + i for i in CHORD_TYPES[chord_type]]


def build_track_data(seed: int = None) -> dict:
    """Собирает все случайные параметры для одного трека.

    Если seed задан — воспроизводимо.
    """
    if seed is not None:
        random.seed(seed)

    key_name, key_shift = random.choice(KEYS)
    prog_name, prog = random.choice(list(PROGRESSIONS.items()))
    tempo_range_name = random.choice(list(TEMPO_RANGES.keys()))
    tempo_min, tempo_max = TEMPO_RANGES[tempo_range_name]
    tempo = random.randint(tempo_min, tempo_max)
    instrument_id, instrument_name = random.choice(INSTRUMENTS)
    melody_style = random.choice(MELODY_STYLES)
    bass_style = random.choice(BASS_STYLES)
    melody_octave = random.choice(MELODY_OCTAVES)

    return {
        "seed": seed,
        "key_name": key_name,
        "key_shift": key_shift,
        "progression_name": prog_name,
        "progression": prog,
        "tempo": tempo,
        "tempo_range": tempo_range_name,
        "instrument_id": instrument_id,
        "instrument_name": instrument_name,
        "melody_style": melody_style,
        "bass_style": bass_style,
        "melody_octave": melody_octave,
    }


def build_filename(params: dict) -> str:
    """Формирует читаемое имя файла из параметров."""
    return (
        f"track_{params['key_name']}_"
        f"{params['progression_name']}_"
        f"{params['tempo']}bpm_"
        f"{params['melody_style']}.mid"
    )


def generate_track(params: dict, min_duration_sec: float = 30.0):
    """Генерирует MIDI-трек по заданным параметрам.

    Возвращает имя файла.
    """
    tempo = params["tempo"]
    key_shift = params["key_shift"]
    progression = params["progression"]
    instrument_id = params["instrument_id"]
    melody_style = params["melody_style"]
    bass_style = params["bass_style"]
    melody_octave = params["melody_octave"]

    # Считаем нужное число тактов
    beat_duration = 60.0 / tempo
    bar_duration = 4 * beat_duration
    bars_needed = max(8, int(min_duration_sec / bar_duration) + 4)

    # Создаём MIDI
    midi = MIDIFile(1)
    track = 0
    channel = 0
    time = 0.0

    midi.addTrackName(track, time, "Generated")
    midi.addTempo(track, time, tempo)
    midi.addProgramChange(track, channel, int(time), instrument_id)

    # Транспонируем прогрессию
    chords = []
    for degree, ctype in progression:
        root = 60 + key_shift + degree
        chords.append((root, ctype))

    # Основной цикл по тактам
    for bar in range(bars_needed):
        root, ctype = chords[bar % len(chords)]
        chord_notes = get_chord_notes(root, ctype)
        chord_dur = 4.0

        # --- Аккорд ---
        for note in chord_notes:
            midi.addNote(track, channel, note, time, chord_dur, 80)

        # --- Бас ---
        if bass_style == "root":
            midi.addNote(track, channel, root - 12, time, chord_dur, 90)
        elif bass_style == "root_fifth":
            midi.addNote(track, channel, root - 12, time, chord_dur / 2, 90)
            midi.addNote(track, channel, root - 12 + 7, time + chord_dur / 2,
                         chord_dur / 2, 90)
        elif bass_style == "walking":
            for i, n in enumerate([root - 12, root - 12 + 4,
                                   root - 12 + 7, root - 12 + 12]):
                midi.addNote(track, channel, n, time + i, 1.0, 90)

        # --- Мелодия ---
        melody_base = melody_octave
        if melody_style == "chord_tone":
            for _ in range(2):
                note = random.choice(chord_notes) + melody_base
                offset = random.choice([0, 0.5, 1, 1.5, 2, 3])
                dur = random.choice([0.5, 1, 2])
                midi.addNote(track, channel, note, time + offset, dur, 70)
        elif melody_style == "arpeggio":
            for i, n in enumerate(chord_notes + chord_notes):
                midi.addNote(track, channel, n + melody_base,
                             time + i * 0.5, 0.5, 70)
        elif melody_style == "scale_run":
            scale = [0, 2, 4, 5, 7, 9, 11, 12]
            start = random.choice(scale)
            for i in range(8):
                note = root + scale[(start + i) % len(scale)] + melody_base
                midi.addNote(track, channel, note, time + i * 0.5, 0.5, 70)
        elif melody_style == "sparse":
            note = random.choice(chord_notes) + melody_base
            midi.addNote(track, channel, note, time + 1, 2, 70)

        time += chord_dur

    # Сохраняем
    filename = build_filename(params)
    with open(filename, "wb") as f:
        midi.writeFile(f)
    return filename


def main():
    """Точка входа: один трек за запуск."""
    # Опциональный seed из аргументов
    seed = None
    if len(sys.argv) > 1:
        try:
            seed = int(sys.argv[1])
        except ValueError:
            print(f"Аргумент должен быть числом, получено: {sys.argv[1]}")
            sys.exit(1)

    # Если seed не задан — используем текущее время
    if seed is None:
        seed = int(time.time() * 1000) % 10_000_000

    params = build_track_data(seed)
    filename = generate_track(params)

    print(f"✅ Сгенерирован: {filename}")
    print(f"   seed: {params['seed']}")
    print(f"   Тональность: {params['key_name']}")
    print(f"   Прогрессия: {params['progression_name']}")
    print(f"   Темп: {params['tempo']} BPM ({params['tempo_range']})")
    print(f"   Инструмент: {params['instrument_name']}")
    print(f"   Мелодия: {params['melody_style']}")
    print(f"   Бас: {params['bass_style']}")
    print(f"   Октава мелодии: +{params['melody_octave']}")


if __name__ == "__main__":
    main()