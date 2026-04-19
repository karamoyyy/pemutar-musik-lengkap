import flet as ft
import os
import json
import uuid
import shutil
import yt_dlp

# --- PENGATURAN FOLDER ---
MUSIC_FOLDER = 'static/music'
PLAYLIST_FILE = 'playlist.json'
os.makedirs(MUSIC_FOLDER, exist_ok=True)

# --- FUNGSI DATA ---
def read_playlist():
    if not os.path.exists(PLAYLIST_FILE): return []
    try:
        with open(PLAYLIST_FILE, 'r') as f: return json.load(f)
    except: return []

def save_playlist(playlist):
    with open(PLAYLIST_FILE, 'w') as f: json.dump(playlist, f, indent=4)

# --- APLIKASI UTAMA ---
def main(page: ft.Page):
    page.title = "Karamoyy. App"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Warna Tema
    PRIMARY = "#ff7eb3"
    SECONDARY = "#ff758c"
    
    # --- VARIABEL STATE ---
    playlist_data = read_playlist()
    current_playing_index = -1
    repeat_mode = 0 # 0: Berurutan, 1: Ulangi 1, 2: Ulangi Semua
    search_query = ""

    # --- KOMPONEN AUDIO ---
    audio = ft.Audio(autoplay=True)
    page.overlay.append(audio)

    # --- ELEMEN UI ---
    now_playing_text = ft.Text("Pilih lagu untuk diputar", size=14, color=ft.colors.GREY_600)
    song_count_text = ft.Text(f"({len(playlist_data)} Lagu)", size=16, color=PRIMARY, weight=ft.FontWeight.BOLD)
    loading_yt = ft.Text("Sedang mendownload... Mohon tunggu.", color=PRIMARY, visible=False, size=12)
    playlist_view = ft.ListView(expand=True, spacing=10, padding=10)
    yt_input = ft.TextField(hint_text="https://youtube.com/...", expand=True, border_radius=8, height=45)
    search_input = ft.TextField(hint_text="Ketik judul lagu yang disimpan...", border_radius=8, height=45)
    
    # Tombol Ulangi
    def toggle_repeat(e):
        nonlocal repeat_mode
        repeat_mode = (repeat_mode + 1) % 3
        if repeat_mode == 0:
            repeat_btn.text = "➡️ Putar Berurutan"
        elif repeat_mode == 1:
            repeat_btn.text = "🔂 Ulangi Lagu"
        elif repeat_mode == 2:
            repeat_btn.text = "🔁 Ulangi Semua Lagu"
        page.update()
        
    repeat_btn = ft.OutlinedButton("➡️ Putar Berurutan", style=ft.ButtonStyle(color=PRIMARY), on_click=toggle_repeat)

    # --- LOGIKA AUDIO SELESAI ---
    def audio_state_changed(e):
        nonlocal current_playing_index
        if e.data == "completed" and current_playing_index != -1:
            if repeat_mode == 1:
                play_song(current_playing_index)
            else:
                next_idx = current_playing_index + 1
                if next_idx < len(playlist_data):
                    play_song(next_idx)
                else:
                    if repeat_mode == 2:
                        play_song(0)
                    else:
                        now_playing_text.value = "Selesai memutar semua lagu"
                        current_playing_index = -1
                        update_playlist_ui()
                        page.update()

    audio.on_state_changed = audio_state_changed

    # --- LOGIKA PEMUTAR & PLAYLIST ---
    def play_song(index):
        nonlocal current_playing_index
        current_playing_index = index
        song = playlist_data[index]
        audio.src = song['path']
        now_playing_text.value = f"Sedang diputar: {song['title']}"
        update_playlist_ui()
        page.update()

    def delete_song(index):
        song = playlist_data[index]
        try:
            if os.path.exists(song['path']): os.remove(song['path'])
        except: pass
        playlist_data.pop(index)
        save_playlist(playlist_data)
        
        nonlocal current_playing_index
        if current_playing_index == index:
            audio.pause()
            now_playing_text.value = "Pilih lagu untuk diputar"
            current_playing_index = -1
        update_playlist_ui()
        page.update()

    def move_song(index, direction):
        if direction == 'up' and index > 0:
            playlist_data[index], playlist_data[index-1] = playlist_data[index-1], playlist_data[index]
        elif direction == 'down' and index < len(playlist_data) - 1:
            playlist_data[index], playlist_data[index+1] = playlist_data[index+1], playlist_data[index]
        save_playlist(playlist_data)
        update_playlist_ui()
        page.update()

    # Logika Rename (Menggunakan Dialog Flet)
    rename_tf = ft.TextField(label="Nama Lagu Baru")
    rename_index = -1

    def close_dlg(e): rename_dlg.open = False; page.update()
    
    def save_rename(e):
        if rename_tf.value.strip():
            playlist_data[rename_index]['title'] = rename_tf.value
            save_playlist(playlist_data)
            update_playlist_ui()
        close_dlg(e)

    rename_dlg = ft.AlertDialog(
        title=ft.Text("Ubah Nama Lagu"),
        content=rename_tf,
        actions=[
            ft.TextButton("Batal", on_click=close_dlg),
            ft.TextButton("Simpan", on_click=save_rename),
        ],
    )
    page.overlay.append(rename_dlg)

    def open_rename_dialog(index):
        nonlocal rename_index
        rename_index = index
        rename_tf.value = playlist_data[index]['title']
        rename_dlg.open = True
        page.update()

    # Memperbarui Tampilan Daftar Lagu
    def update_playlist_ui():
        song_count_text.value = f"({len(playlist_data)} Lagu)"
        playlist_view.controls.clear()
        
        for i, song in enumerate(playlist_data):
            # Fitur Pencarian
            if search_query.lower() not in song['title'].lower():
                continue

            is_playing = (i == current_playing_index)
            title_color = PRIMARY if is_playing else ft.colors.GREY_800
            
            # Kumpulan Tombol Baris
            btn_row = ft.Row(spacing=3)
            if i > 0: btn_row.controls.append(ft.IconButton(ft.icons.ARROW_UPWARD, icon_color="#a18cd1", icon_size=18, on_click=lambda e, idx=i: move_song(idx, 'up')))
            if i < len(playlist_data) - 1: btn_row.controls.append(ft.IconButton(ft.icons.ARROW_DOWNWARD, icon_color="#a18cd1", icon_size=18, on_click=lambda e, idx=i: move_song(idx, 'down')))
            btn_row.controls.append(ft.IconButton(ft.icons.EDIT, icon_color="#4facfe", icon_size=18, on_click=lambda e, idx=i: open_rename_dialog(idx)))
            btn_row.controls.append(ft.IconButton(ft.icons.DELETE, icon_color="#ff4b4b", icon_size=18, on_click=lambda e, idx=i: delete_song(idx)))

            row = ft.Container(
                content=ft.Row([
                    ft.Text(song['title'], weight=ft.FontWeight.BOLD, color=title_color, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                    btn_row,
                    ft.IconButton(icon=ft.icons.PLAY_CIRCLE_FILL, icon_color=PRIMARY, on_click=lambda e, idx=i: play_song(idx))
                ]),
                bgcolor=ft.colors.WHITE, padding=10, border_radius=8,
                shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.BLACK12)
            )
            playlist_view.controls.append(row)

    # --- LOGIKA YOUTUBE & UPLOAD LOKAL ---
    def add_youtube(e):
        url = yt_input.value
        if not url: return
        loading_yt.visible = True
        page.update()

        try:
            song_id = str(uuid.uuid4())
            save_path = os.path.join(MUSIC_FOLDER, f"{song_id}.%(ext)s")
            ydl_opts = {'format': 'bestaudio/best', 'outtmpl': save_path, 'noplaylist': True}
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Lagu YouTube')
                ext = info.get('ext', 'webm')
                
                new_song = {'id': song_id, 'title': title, 'path': f"static/music/{song_id}.{ext}"}
                playlist_data.append(new_song)
                save_playlist(playlist_data)
                
            yt_input.value = ""
            update_playlist_ui()
        except Exception as ex:
            now_playing_text.value = f"Error: {str(ex)}"
        finally:
            loading_yt.visible = False
            page.update()

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                song_id = str(uuid.uuid4())
                ext = os.path.splitext(f.name)[1]
                filename = f"{song_id}{ext}"
                dest_path = os.path.join(MUSIC_FOLDER, filename)
                
                shutil.copy(f.path, dest_path)
                
                new_song = {'id': song_id, 'title': f.name, 'path': f"static/music/{filename}"}
                playlist_data.append(new_song)
            save_playlist(playlist_data)
            update_playlist_ui()
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    def on_search(e):
        nonlocal search_query
        search_query = search_input.value
        update_playlist_ui()
        page.update()
        
    search_input.on_change = on_search

    # --- DESAIN UI UTAMA (GABUNGAN) ---
    def create_section(title, content):
        return ft.Container(
            content=ft.Column([ft.Text(title, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_800), content]),
            bgcolor=ft.colors.WHITE, padding=15, border_radius=12,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12)
        )

    # Social Navbar
    def social_link(text, url):
        return ft.TextButton(text, url=url, style=ft.ButtonStyle(color="#888888"))

    social_navbar = ft.Row([
        social_link("IG", "https://instagram.com/dndycihuyy_"),
        social_link("TikTok", "https://tiktok.com/@dannsoniced"),
        social_link("WA", "https://wa.me/6283875965216"),
        social_link("Gmail", "mailto:dandyahmad647@gmail.com"),
    ], alignment=ft.MainAxisAlignment.CENTER)

    # Kartu Putih Utama
    main_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Karamoyy.", size=28, weight=ft.FontWeight.BOLD, color=SECONDARY),
                song_count_text
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([now_playing_text], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([
                ft.IconButton(ft.icons.PLAY_ARROW, icon_color=PRIMARY, on_click=lambda e: audio.resume()),
                ft.IconButton(ft.icons.PAUSE, icon_color=PRIMARY, on_click=lambda e: audio.pause()),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([repeat_btn], alignment=ft.MainAxisAlignment.CENTER),
            
            create_section("Tambah dari YouTube Music:", ft.Column([
                ft.Row([yt_input, ft.ElevatedButton("Download", bgcolor=PRIMARY, color=ft.colors.WHITE, on_click=add_youtube)]),
                loading_yt
            ])),
            create_section("Upload From File:", ft.ElevatedButton("Pilih Lagu", icon=ft.icons.UPLOAD_FILE, bgcolor=SECONDARY, color=ft.colors.WHITE, width=float("inf"), on_click=lambda _: file_picker.pick_files())),
            create_section("Cari Lagu:", search_input),
            
            ft.Container(content=playlist_view, height=250), # Ketinggian box playlist
            ft.Divider(),
            social_navbar
        ]),
        width=500, bgcolor=ft.colors.WHITE.with_opacity(0.95), padding=30, border_radius=20,
        shadow=ft.BoxShadow(blur_radius=30, color=ft.colors.BLACK26)
    )

    # Latar Belakang Gradasi
    background = ft.Container(
        content=main_card,
        gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=["#a18cd1", "#fbc2eb"]),
        expand=True, alignment=ft.alignment.center, padding=20
    )

    page.add(background)
    update_playlist_ui()

# Jalankan Aplikasi! (assets_dir="." sangat penting agar Flet bisa membaca folder static)
ft.app(target=main, assets_dir=".")
