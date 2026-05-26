#--------------------------------------------------
# Facultad de Ingenieria, UNAM
# Materia: Fundamentos de Sistemas Embebidos
# Autor: Jesús Vázquez Romero
# Programa:Centro Multimedia
# License: MIT
#--------------------------------------------------



import pygame
import vlc
import os
import time
import subprocess
import pyudev
import threading
import sys

# --- Inicialización y Configuración Global ---
pygame.init()

# Configuración de la pantalla
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Centro Multimedia Raspberry Pi")

# Definición de colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
LIGHT_BLUE = (100, 100, 255)
DARK_BLUE = (30, 30, 150)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
YELLOW = (200, 200, 50)

# Definición de fuentes
font_large = pygame.font.Font(None, 74)
font_medium = pygame.font.Font(None, 50)
font_small = pygame.font.Font(None, 36)
font_tiny = pygame.font.Font(None, 24)

# Instancia global de VLC y variable para el proceso externo
player = vlc.MediaPlayer()
vlc_process = None

# --- Gestión de Estados de la Aplicación ---
STATE_MAIN_MENU = 0
STATE_WIFI_SETUP = 1
STATE_USB_SUBMENU = 2
STATE_USB_LOADING = 3
STATE_USB_MIXED_CHOICE = 4
STATE_PLAYING_MEDIA = 5
STATE_USB_VIDEO_SELECTION = 6
STATE_USB_NO_MEDIA = 7
STATE_WIFI_SUCCESS_MESSAGE = 8

# Estado inicial de la aplicación
current_state = STATE_MAIN_MENU
running = True

# --- Variables para la Detección y Contenido de USB ---
usb_thread = None
usb_event_queue = [] # Cola para eventos de USB
usb_data = {
    'mount_point': None,
    'photos': [],
    'music': [],
    'videos': []
}

# --- Variables para la Configuración de Wi-Fi ---
wifi_ssid_input = ""
wifi_password_input = ""
active_input_field = None # Campo de entrada activo ('ssid' o 'password')

# --- Carga y Escalado de Íconos ---
ICON_PATH = "icons/"
icons = {}
try:
    # Carga de iconos individuales
    icons['netflix'] = pygame.image.load(os.path.join(ICON_PATH, 'netflix.png')).convert_alpha()
    icons['disneyplus'] = pygame.image.load(os.path.join(ICON_PATH, 'disneyplus.png')).convert_alpha()
    icons['primevideo'] = pygame.image.load(os.path.join(ICON_PATH, 'primevideo.png')).convert_alpha()
    icons['spotify'] = pygame.image.load(os.path.join(ICON_PATH, 'spotify.png')).convert_alpha()
    icons['applemusic'] = pygame.image.load(os.path.join(ICON_PATH, 'applemusic.png')).convert_alpha()
    icons['usb'] = pygame.image.load(os.path.join(ICON_PATH, 'usb.png')).convert_alpha()
    icons['videos_logo'] = pygame.image.load(os.path.join(ICON_PATH, 'videos_logo.png')).convert_alpha()
    icons['imagenes_logo'] = pygame.image.load(os.path.join(ICON_PATH, 'imagenes_logo.png')).convert_alpha()
    icons['music_logo'] = pygame.image.load(os.path.join(ICON_PATH, 'music_logo.png')).convert_alpha()
    icons['back_arrow'] = pygame.image.load(os.path.join(ICON_PATH, 'back_arrow.png')).convert_alpha()
    icons['wifi_logo'] = pygame.image.load(os.path.join(ICON_PATH, 'wifi_logo.png')).convert_alpha()

    # Definición de tamaños de iconos
    icon_size_main = 100
    icon_size_submenu = 120
    icon_size_back_arrow = 60
    icon_size_wifi = 60

    # Escalado de iconos según su tipo
    for key in icons:
        if key == 'back_arrow':
            icons[key] = pygame.transform.scale(icons[key], (icon_size_back_arrow, icon_size_back_arrow))
        elif key == 'wifi_logo':
            icons[key] = pygame.transform.scale(icons[key], (icon_size_wifi, icon_size_wifi))
        elif key in ['videos_logo', 'imagenes_logo', 'music_logo']:
            icons[key] = pygame.transform.scale(icons[key], (icon_size_submenu, icon_size_submenu))
        else:
            icons[key] = pygame.transform.scale(icons[key], (icon_size_main, icon_size_main))

except pygame.error as e:
    print(f"Error al cargar un icono: {e}")
    print("Asegúrate de que los archivos de imagen estén en la carpeta 'icons/' y sean accesibles.")
    icons = None

# --- Funciones de Utilidad de la GUI ---
def draw_text(text, font, color, surface, x, y, align_center=True):
    """Renderiza texto en la superficie de Pygame."""
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    if align_center:
        textrect.center = (x, y)
    else:
        textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def create_button_with_icon(icon_name, rect, base_color, hover_color, text_label="", font=None, text_color=WHITE):
    """Crea un botón con un icono y etiqueta de texto."""
    mouse_pos = pygame.mouse.get_pos()
    clicked = pygame.mouse.get_pressed()[0]
    
    current_color = base_color
    if rect.collidepoint(mouse_pos):
        current_color = hover_color
        if clicked:
            return True
    
    pygame.draw.rect(screen, current_color, rect, border_radius=10)
    
    if icons and icon_name in icons:
        icon = icons[icon_name]
        icon_rect = icon.get_rect(center=rect.center)
        screen.blit(icon, icon_rect)
    else:
        # Si no hay icono, dibujar solo el texto
        if font:
            draw_text(text_label, font, text_color, screen, rect.centerx, rect.centery)
        else:
            draw_text(text_label, font_medium, text_color, screen, rect.centerx, rect.centery)

    return False

def create_button_text_only(text, rect, font, base_color, hover_color):
    """Crea un botón que solo contiene texto."""
    mouse_pos = pygame.mouse.get_pos()
    clicked = pygame.mouse.get_pressed()[0]
    
    current_color = base_color
    if rect.collidepoint(mouse_pos):
        current_color = hover_color
        if clicked:
            return True
    
    pygame.draw.rect(screen, current_color, rect, border_radius=10)
    draw_text(text, font, WHITE, screen, rect.centerx, rect.centery)
    return False

# --- Lógica de Negocio ---
def stop_current_playback():
    """Detiene cualquier reproducción de VLC activa."""
    if player.is_playing():
        player.stop()
    global vlc_process
    if vlc_process:
        vlc_process.terminate()
        vlc_process = None

def is_connected_to_internet():
    """Verifica la conexión a internet."""
    try:
        subprocess.check_output(['ping', '-c', '1', '8.8.8.8'], timeout=2)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False

def connect_to_wifi_logic(ssid, password):
    """Intenta conectar el dispositivo a una red Wi-Fi."""
    try:
        # Asegurar que NetworkManager esté activo
        subprocess.run(['sudo', 'systemctl', 'start', 'NetworkManager'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1) 

        subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password],
                        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Conectado exitosamente a la red Wi-Fi '{ssid}'.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al conectar: {e.stderr.decode().strip()}")
        return False
    except FileNotFoundError:
        print("Error: 'nmcli' o 'systemctl' no encontrado. Asegúrese de que NetworkManager esté instalado.")
        return False

# --- Funciones de Manejo de USB (en un hilo separado) ---
def get_mount_point(device_path):
    """Obtiene el punto de montaje de un dispositivo."""
    try:
        result = subprocess.run(["findmnt", "-unl", "-S", device_path], capture_output=True, text=True, check=True)
        return result.stdout.split(" ")[0].strip()
    except subprocess.CalledProcessError:
        return None

def auto_mount(device_path):
    """Monta automáticamente un dispositivo USB."""
    try:
        subprocess.run(["udisksctl", "mount", "-b", device_path], check=True)
        time.sleep(1)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Fallo al montar {device_path}: {e}")
        return False

def get_media_files(mount_point):
    """Escanea el punto de montaje en busca de archivos multimedia."""
    photos = []
    music = []
    videos = []
    
    if not os.path.exists(mount_point):
        return photos, music, videos

    for root, _, files in os.walk(mount_point):
        for file in files:
            file_path = os.path.join(root, file)
            lower_file = file.lower()
            # Añadir archivos a las listas correspondientes
            if lower_file.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                photos.append(file_path)
            elif lower_file.endswith(('.mp3', '.wav', '.flac', '.ogg')):
                music.append(file_path)
            elif lower_file.endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm')):
                videos.append(file_path)
    return photos, music, videos

# --- Funciones de Reproducción (VLC externo) ---
def play_media_vlc_external(file_path, loop=False, slideshow_duration=0):
    """Inicia la reproducción de medios usando un proceso VLC externo."""
    stop_current_playback()

    vlc_cmd = ['vlc', '--fullscreen', '--no-video-title-show', '--no-osd']
    if loop:
        vlc_cmd.append('--loop')
    if slideshow_duration > 0:
        vlc_cmd.append(f'--image-duration={slideshow_duration}')
    
    vlc_cmd.append(file_path)
    
    print(f"Lanzando VLC externo: {vlc_cmd}")
    global vlc_process
    vlc_process = subprocess.Popen(vlc_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    global current_state
    current_state = STATE_PLAYING_MEDIA

def play_slideshow_vlc(photo_paths):
    """Inicia una presentación de diapositivas de fotos con VLC."""
    if not photo_paths:
        print("No se encontraron fotografías.")
        return
    
    playlist_file = "/tmp/usb_photos.m3u"
    with open(playlist_file, "w") as f:
        f.write("#EXTM3U\n")
        for p in photo_paths:
            f.write(p + "\n")

    play_media_vlc_external(playlist_file, loop=True, slideshow_duration=3)

def play_music_loop_vlc(music_paths):
    """Reproduce música en bucle con VLC."""
    if not music_paths:
        print("No se encontraron pistas de música.")
        return

    playlist_file = "/tmp/usb_music.m3u"
    with open(playlist_file, "w") as f:
        f.write("#EXTM3U\n")
        for m in music_paths:
            f.write(m + "\n")

    play_media_vlc_external(playlist_file, loop=True)

def play_video_selection_vlc(video_paths):
    """Prepara la selección de video del USB."""
    global current_state, usb_data
    usb_data['videos'] = video_paths
    current_state = STATE_USB_VIDEO_SELECTION

def play_video_slideshow_vlc(video_paths):
    """Reproduce videos en modo presentación con VLC."""
    if not video_paths:
        print("No se encontraron videos para la presentación.")
        return

    playlist_file = "/tmp/usb_videos.m3u"
    with open(playlist_file, "w") as f:
        f.write("#EXTM3U\n")
        for v in video_paths:
            f.write(v + "\n")

    play_media_vlc_external(playlist_file, loop=True)

def usb_monitor_thread_func():
    """Monitorea eventos de conexión/desconexión de USB en un hilo separado."""
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block', device_type='partition')

    print("Hilo de monitoreo USB iniciado.")
    
    # Comprobar USB ya conectados al inicio
    for device in context.list_devices(subsystem='block', device_type='partition'):
        if 'ID_BUS' in device and device['ID_BUS'] == 'usb':
            dev_path = device.device_node
            mount_point = get_mount_point(dev_path)
            if not mount_point:
                if auto_mount(dev_path):
                    mount_point = get_mount_point(dev_path)
            
            if mount_point:
                photos, music, videos = get_media_files(mount_point)
                usb_event_queue.append({
                    'type': 'usb_inserted',
                    'mount_point': mount_point,
                    'photos': photos,
                    'music': music,
                    'videos': videos
                })
                print(f"USB existente detectado y datos en cola: {mount_point}")
                break

    # Monitorear nuevos eventos de USB
    for action, device in monitor:
        if action == 'add' and device.get('ID_BUS') == 'usb' and device.device_type == 'partition':
            dev_path = device.device_node
            print(f"Nuevo USB insertado: {dev_path}")
            mount_point = get_mount_point(dev_path)
            if not mount_point:
                if auto_mount(dev_path):
                    mount_point = get_mount_point(dev_path)
            
            if mount_point:
                photos, music, videos = get_media_files(mount_point)
                usb_event_queue.append({
                    'type': 'usb_inserted',
                    'mount_point': mount_point,
                    'photos': photos,
                    'music': music,
                    'videos': videos
                })
                print(f"Nuevo USB montado y datos en cola: {mount_point}")
            else:
                print(f"No se pudo montar/obtener punto de montaje para {dev_path}")
        elif action == 'remove' and device.get('ID_BUS') == 'usb' and device.device_type == 'partition':
            print(f"USB removido: {device.device_node}")
            usb_event_queue.append({'type': 'usb_removed'})

# --- Pantallas de la GUI ---
def main_menu_screen():
    """Dibuja y maneja la pantalla del menú principal."""
    screen.fill(DARK_BLUE)
    draw_text("Centro Multimedia Pi", font_large, WHITE, screen, SCREEN_WIDTH // 2, 80)

    button_width = 250
    button_height = 120
    button_x_center = SCREEN_WIDTH // 2
    
    # Posiciones de los botones
    btn_netflix_rect = pygame.Rect(button_x_center - button_width - 50, 180, button_width, button_height)
    btn_prime_video_rect = pygame.Rect(button_x_center - button_width - 50, 320, button_width, button_height)
    btn_spotify_rect = pygame.Rect(button_x_center - button_width - 50, 460, button_width, button_height)

    btn_disney_rect = pygame.Rect(button_x_center + 50, 180, button_width, button_height)
    btn_apple_music_rect = pygame.Rect(button_x_center + 50, 320, button_width, button_height)
    btn_usb_rect = pygame.Rect(button_x_center + 50, 460, button_width, button_height)

    btn_exit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 600, 300, 70)

    # Botón de configuración Wi-Fi
    wifi_icon_size = icons['wifi_logo'].get_width()
    btn_wifi_rect = pygame.Rect(SCREEN_WIDTH - wifi_icon_size - 20, 20, wifi_icon_size, wifi_icon_size)
    if create_button_with_icon('wifi_logo', btn_wifi_rect, DARK_BLUE, GRAY):
        return STATE_WIFI_SETUP

    # Botones de aplicaciones de streaming
    if create_button_with_icon('netflix', btn_netflix_rect, GRAY, LIGHT_BLUE, "Netflix"):
        subprocess.Popen(['chromium-browser', '--kiosk', 'https://www.netflix.com'])
        return STATE_MAIN_MENU
    if create_button_with_icon('disneyplus', btn_disney_rect, GRAY, LIGHT_BLUE, "Disney+"):
        subprocess.Popen(['chromium-browser', '--kiosk', 'https://www.disneyplus.com'])
        return STATE_MAIN_MENU
    if create_button_with_icon('primevideo', btn_prime_video_rect, GRAY, LIGHT_BLUE, "Prime Video"):
        subprocess.Popen(['chromium-browser', '--kiosk', 'https://www.primevideo.com'])
        return STATE_MAIN_MENU
    if create_button_with_icon('spotify', btn_spotify_rect, GRAY, LIGHT_BLUE, "Spotify"):
        subprocess.Popen(['chromium-browser', '--kiosk', 'https://open.spotify.com'])
        return STATE_MAIN_MENU
    if create_button_with_icon('applemusic', btn_apple_music_rect, GRAY, LIGHT_BLUE, "Apple Music"):
        subprocess.Popen(['chromium-browser', '--kiosk', 'https://music.apple.com'])
        return STATE_MAIN_MENU
    
    # Botón de USB
    if create_button_with_icon('usb', btn_usb_rect, GRAY, LIGHT_BLUE, "Reproducir USB"):
        return STATE_USB_SUBMENU

    # Botón de salida
    if create_button_text_only("Salir", btn_exit_rect, font_medium, GRAY, RED):
        return -1

    return STATE_MAIN_MENU

def wifi_setup_screen():
    """Dibuja y maneja la pantalla de configuración de Wi-Fi."""
    global wifi_ssid_input, wifi_password_input, active_input_field
    screen.fill(DARK_BLUE)
    draw_text("Configuración Wi-Fi", font_large, WHITE, screen, SCREEN_WIDTH // 2, 80)
    draw_text("Ingrese datos de la red:", font_medium, WHITE, screen, SCREEN_WIDTH // 2, 160)

    ssid_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, 250, 600, 60)
    pass_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, 350, 600, 60)

    # Dibujar campos de entrada para SSID y Contraseña
    pygame.draw.rect(screen, WHITE, ssid_rect, border_radius=5)
    pygame.draw.rect(screen, (150,255,150) if active_input_field == 'ssid' else GRAY, ssid_rect, 3, border_radius=5)
    draw_text("SSID: " + wifi_ssid_input, font_medium, BLACK, screen, ssid_rect.centerx, ssid_rect.centery)

    pygame.draw.rect(screen, WHITE, pass_rect, border_radius=5)
    pygame.draw.rect(screen, (150,255,150) if active_input_field == 'password' else GRAY, pass_rect, 3, border_radius=5)
    draw_text("Contraseña: " + ("*" * len(wifi_password_input)), font_medium, BLACK, screen, pass_rect.centerx, pass_rect.centery)

    btn_connect = pygame.Rect(SCREEN_WIDTH // 2 - 200, 450, 400, 80)
    btn_back = pygame.Rect(SCREEN_WIDTH // 2 - 200, 550, 400, 80)

    # Botón para regresar al menú principal
    back_arrow_rect = pygame.Rect(20, 20, icons['back_arrow'].get_width(), icons['back_arrow'].get_height())
    if create_button_with_icon('back_arrow', back_arrow_rect, DARK_BLUE, GRAY):
        return STATE_MAIN_MENU

    # Botón para conectar a Wi-Fi
    if create_button_text_only("Conectar", btn_connect, font_medium, GREEN, (0, 200, 0)):
        if connect_to_wifi_logic(wifi_ssid_input, wifi_password_input):
            return STATE_WIFI_SUCCESS_MESSAGE
        else:
            print("Fallo la conexión Wi-Fi.")
            return STATE_WIFI_SETUP
    
    # Botón para volver al menú principal
    if create_button_text_only("Volver", btn_back, font_medium, GRAY, YELLOW):
        return STATE_MAIN_MENU

    return STATE_WIFI_SETUP

def wifi_success_message_screen():
    """Muestra un mensaje de conexión Wi-Fi exitosa."""
    screen.fill(GREEN)
    draw_text("¡Conexión Wi-Fi Exitosa!", font_large, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
    draw_text("Volviendo al menú principal...", font_medium, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
    
    pygame.display.flip()
    pygame.time.wait(2000)
    return STATE_MAIN_MENU

def usb_submenu_screen():
    """Dibuja y maneja la pantalla del submenú USB."""
    screen.fill(DARK_BLUE)
    draw_text("Seleccione tipo de medio USB", font_large, WHITE, screen, SCREEN_WIDTH // 2, 80)

    button_width = 300
    button_height = 150
    button_spacing = 40

    # Posicionamiento de los botones de tipo de medio
    total_width = 3 * button_width + 2 * button_spacing
    start_x = (SCREEN_WIDTH - total_width) // 2
    y_pos = SCREEN_HEIGHT // 2 - button_height // 2

    btn_videos_rect = pygame.Rect(start_x, y_pos, button_width, button_height)
    btn_imagenes_rect = pygame.Rect(start_x + button_width + button_spacing, y_pos, button_width, button_height)
    btn_music_rect = pygame.Rect(start_x + 2 * (button_width + button_spacing), y_pos, button_width, button_height)

    # Botón para regresar
    back_arrow_rect = pygame.Rect(20, 20, icons['back_arrow'].get_width(), icons['back_arrow'].get_height())
    if create_button_with_icon('back_arrow', back_arrow_rect, DARK_BLUE, GRAY):
        return STATE_MAIN_MENU

    # Botones de selección de tipo de medio
    if create_button_with_icon('videos_logo', btn_videos_rect, GRAY, LIGHT_BLUE, "Videos"):
        if usb_data['videos']:
            play_video_selection_vlc(usb_data['videos'])
            return STATE_USB_VIDEO_SELECTION
        else:
            return STATE_USB_LOADING
    
    if create_button_with_icon('imagenes_logo', btn_imagenes_rect, GRAY, LIGHT_BLUE, "Imágenes"):
        if usb_data['photos']:
            play_slideshow_vlc(usb_data['photos'])
            return STATE_PLAYING_MEDIA
        else:
            return STATE_USB_LOADING

    if create_button_with_icon('music_logo', btn_music_rect, GRAY, LIGHT_BLUE, "Música"):
        if usb_data['music']:
            play_music_loop_vlc(usb_data['music'])
            return STATE_PLAYING_MEDIA
        else:
            return STATE_USB_LOADING

    return STATE_USB_SUBMENU

def usb_loading_screen():
    """Muestra una pantalla de carga para el USB."""
    screen.fill(DARK_BLUE)
    draw_text("Cargando USB...", font_large, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
    draw_text("Por favor espere o inserte la memoria USB.", font_medium, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
    
    # Botón para regresar
    back_arrow_rect = pygame.Rect(20, 20, icons['back_arrow'].get_width(), icons['back_arrow'].get_height())
    if create_button_with_icon('back_arrow', back_arrow_rect, DARK_BLUE, GRAY):
        return STATE_USB_SUBMENU

    return STATE_USB_LOADING

def usb_no_media_screen():
    """Muestra un mensaje cuando el USB no contiene medios compatibles."""
    screen.fill(DARK_BLUE)
    draw_text("USB detectado, pero sin medios.", font_large, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
    draw_text("Inserte un USB con fotos, música o videos.", font_medium, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
    
    # Botón para regresar
    back_arrow_rect = pygame.Rect(20, 20, icons['back_arrow'].get_width(), icons['back_arrow'].get_height())
    if create_button_with_icon('back_arrow', back_arrow_rect, DARK_BLUE, GRAY):
        return STATE_USB_SUBMENU

    return STATE_USB_NO_MEDIA

def usb_mixed_choice_screen():
    """Permite al usuario elegir qué tipo de medio reproducir si el USB tiene varios."""
    screen.fill(DARK_BLUE)
    draw_text("Contenido mixto en USB", font_large, WHITE, screen, SCREEN_WIDTH // 2, 80)
    draw_text("¿Qué desea reproducir?", font_medium, WHITE, screen, SCREEN_WIDTH // 2, 160)

    # Botón para regresar
    back_arrow_rect = pygame.Rect(20, 20, icons['back_arrow'].get_width(), icons['back_arrow'].get_height())
    if create_button_with_icon('back_arrow', back_arrow_rect, DARK_BLUE, GRAY):
        return STATE_USB_SUBMENU

    y_offset = 250
    
    # Botones para seleccionar tipo de medio
    if usb_data['photos']:
        btn_photos = pygame.Rect(SCREEN_WIDTH // 2 - 200, y_offset, 400, 80)
        if create_button_text_only("Reproducir Fotos", btn_photos, font_medium, GRAY, LIGHT_BLUE):
            play_slideshow_vlc(usb_data['photos'])
            return STATE_PLAYING_MEDIA
        y_offset += 100
    
    if usb_data['music']:
        btn_music = pygame.Rect(SCREEN_WIDTH // 2 - 200, y_offset, 400, 80)
        if create_button_text_only("Reproducir Música", btn_music, font_medium, GRAY, LIGHT_BLUE):
            play_music_loop_vlc(usb_data['music'])
            return STATE_PLAYING_MEDIA
        y_offset += 100
    
    if usb_data['videos']:
        btn_videos = pygame.Rect(SCREEN_WIDTH // 2 - 200, y_offset, 400, 80)
        if create_button_text_only("Reproducir Videos", btn_videos, font_medium, GRAY, LIGHT_BLUE):
            play_video_selection_vlc(usb_data['videos'])
            return STATE_USB_VIDEO_SELECTION
        y_offset += 100

    return STATE_USB_MIXED_CHOICE

def usb_video_selection_screen():
    """Permite al usuario seleccionar un video específico del USB."""
    screen.fill(DARK_BLUE)
    draw_text("Seleccione un Video del USB", font_large, WHITE, screen, SCREEN_WIDTH // 2, 80)

    # Botón para regresar
    back_arrow_rect = pygame.Rect(20, 20, icons['back_arrow'].get_width(), icons['back_arrow'].get_height())
    if create_button_with_icon('back_arrow', back_arrow_rect, DARK_BLUE, GRAY):
        return STATE_USB_SUBMENU

    start_y = 180
    video_buttons = []
    for i, video_path in enumerate(usb_data['videos']):
        display_name = os.path.basename(video_path)
        btn_rect = pygame.Rect(50, start_y + i * 70, SCREEN_WIDTH - 100, 60)
        video_buttons.append((btn_rect, video_path))
        pygame.draw.rect(screen, GRAY, btn_rect, border_radius=5)
        draw_text(display_name, font_small, WHITE, screen, btn_rect.centerx, btn_rect.centery)

    # Botón para reproducir todos los videos en presentación
    btn_play_all = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT - 180, 500, 70)
    if create_button_text_only("Reproducir todos en presentación", btn_play_all, font_medium, GREEN, (0, 200, 0)):
        play_video_slideshow_vlc(usb_data['videos'])
        return STATE_PLAYING_MEDIA

    mouse_pos = pygame.mouse.get_pos()
    clicked = pygame.mouse.get_pressed()[0]
    if clicked:
        for btn_rect, video_path in video_buttons:
            if btn_rect.collidepoint(mouse_pos):
                play_media_vlc_external(video_path, loop=False)
                return STATE_PLAYING_MEDIA
    
    return STATE_USB_VIDEO_SELECTION

def playing_media_screen():
    """Muestra la pantalla mientras se reproduce el contenido multimedia."""
    screen.fill(BLACK)
    draw_text("Reproduciendo multimedia...", font_large, WHITE, screen, SCREEN_WIDTH // 2, 50)
    draw_text("Presiona ESC para detener y volver al menú.", font_small, WHITE, screen, SCREEN_WIDTH // 2, 120)

    global vlc_process
    # Regresar al menú principal si la reproducción externa de VLC ha terminado
    if vlc_process and vlc_process.poll() is not None:
        print("Reproducción externa de VLC terminada.")
        vlc_process = None
        return STATE_MAIN_MENU

    return STATE_PLAYING_MEDIA

# --- Bucle Principal de la Aplicación ---
def main_loop():
    """Bucle principal de la aplicación Pygame que gestiona los estados."""
    global current_state, running, active_input_field, wifi_ssid_input, wifi_password_input, vlc_process, usb_thread

    # Iniciar el hilo de monitoreo de USB una sola vez al inicio
    if usb_thread is None:
        usb_thread = threading.Thread(target=usb_monitor_thread_func, daemon=True)
        usb_thread.start()

    # Si no hay conexión a internet al inicio, redirigir a la configuración Wi-Fi
    if not is_connected_to_internet():
        current_state = STATE_WIFI_SETUP

    vlc_process = None # Asegura que no haya un proceso VLC activo al inicio

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Manejo de entrada de texto en la pantalla de configuración Wi-Fi
            if current_state == STATE_WIFI_SETUP:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    ssid_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, 250, 600, 60)
                    pass_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, 350, 600, 60)
                    if ssid_rect.collidepoint(event.pos):
                        active_input_field = 'ssid'
                    elif pass_rect.collidepoint(event.pos):
                        active_input_field = 'password'
                    else:
                        active_input_field = None

                if event.type == pygame.KEYDOWN and active_input_field:
                    if event.key == pygame.K_BACKSPACE:
                        if active_input_field == 'ssid':
                            wifi_ssid_input = wifi_ssid_input[:-1]
                        else:
                            wifi_password_input = wifi_password_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        active_input_field = None
                    else:
                        if active_input_field == 'ssid':
                            wifi_ssid_input += event.unicode
                        else:
                            wifi_password_input += event.unicode
            
            # Manejo de la tecla ESC para salir de estados o detener reproducción
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if current_state == STATE_PLAYING_MEDIA:
                        stop_current_playback()
                        current_state = STATE_MAIN_MENU
                    elif current_state in [STATE_USB_SUBMENU, STATE_USB_LOADING, STATE_USB_NO_MEDIA,
                                           STATE_USB_MIXED_CHOICE, STATE_USB_VIDEO_SELECTION,
                                           STATE_WIFI_SETUP, STATE_WIFI_SUCCESS_MESSAGE]:
                        current_state = STATE_MAIN_MENU
                    elif current_state != STATE_MAIN_MENU: # Cualquier otro estado vuelve al menú principal
                        current_state = STATE_MAIN_MENU

        # Procesar eventos de USB desde la cola del hilo
        while usb_event_queue:
            usb_event = usb_event_queue.pop(0)
            if usb_event['type'] == 'usb_inserted':
                usb_data['mount_point'] = usb_event['mount_point']
                usb_data['photos'] = usb_event['photos']
                usb_data['music'] = usb_event['music']
                usb_data['videos'] = usb_event['videos']
                
                print(f"Datos de USB actualizados: Fotos={len(usb_data['photos'])}, Música={len(usb_data['music'])}, Videos={len(usb_data['videos'])}")

            elif usb_event['type'] == 'usb_removed':
                stop_current_playback()
                usb_data['mount_point'] = None
                usb_data['photos'] = []
                usb_data['music'] = []
                usb_data['videos'] = []
                # Si se remueve el USB, regresar al menú principal si estaba en un estado relacionado
                if current_state in [STATE_USB_LOADING, STATE_USB_MIXED_CHOICE, STATE_USB_VIDEO_SELECTION, STATE_USB_NO_MEDIA, STATE_PLAYING_MEDIA, STATE_USB_SUBMENU]:
                    current_state = STATE_MAIN_MENU
                print("Memoria USB desconectada.")

        # Renderizar la pantalla actual según el estado de la aplicación
        if current_state == STATE_MAIN_MENU:
            current_state = main_menu_screen()
        elif current_state == STATE_WIFI_SETUP:
            current_state = wifi_setup_screen()
        elif current_state == STATE_WIFI_SUCCESS_MESSAGE:
            current_state = wifi_success_message_screen()
        elif current_state == STATE_USB_SUBMENU:
            current_state = usb_submenu_screen()
        elif current_state == STATE_USB_LOADING:
            current_state = usb_loading_screen()
        elif current_state == STATE_USB_NO_MEDIA:
            current_state = usb_no_media_screen()
        elif current_state == STATE_USB_MIXED_CHOICE:
            current_state = usb_mixed_choice_screen()
        elif current_state == STATE_USB_VIDEO_SELECTION:
            current_state = usb_video_selection_screen()
        elif current_state == STATE_PLAYING_MEDIA:
            current_state = playing_media_screen()
            
        if current_state == -1: # Estado de salida de la aplicación
            running = False

        pygame.display.flip()
        pygame.time.Clock().tick(30) # Limitar a 30 FPS

    # Limpieza al salir
    stop_current_playback()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main_loop()
