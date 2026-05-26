#!/bin/bash

#--------------------------------------------------
# Facultad de Ingenieria, UNAM
# Materia: Fundamentos de Sistemas Embebidos
# Autor: Jesús Vázquez Romero
# Programa: instalador de herramientas para Centro Multimedia
# License: MIT
#--------------------------------------------------

# --- Variable para rastrear errores ---
ERRORS_FOUND=0

# --- Funciones de ayuda para el registro de mensajes ---
log_info() {
    echo "[INFO] $1"
}

log_warning() {
    echo "[ADVERTENCIA] $1"
}

log_error() {
    echo "[ERROR] $1"
    ERRORS_FOUND=1
}

# --- Función para ejecutar comandos y verificar su éxito ---
run_command() {
    local command_description="$1"
    shift
    local command_to_run="$@"
    
    log_info "Ejecutando: $command_description"
    
    # Redirigir stdout y stderr a /dev/null para ocultar la salida, 
    # pero seguir capturando el código de salida
    if ! $command_to_run &>/dev/null; then
        log_error "Fallo al: $command_description"
        return 1
    fi
    return 0
}

# --- Mensaje de bienvenida y verificación de permisos ---
log_info "-----------------------------------------------------"
log_info "  Iniciando la instalación de dependencias del Centro Multimedia."
log_info "-----------------------------------------------------"

if [ "$EUID" -ne 0 ]; then
    log_error "Por favor, ejecuta este script con sudo: sudo ./install_dependencies.sh"
    exit 1 # Salir si no se tienen permisos de sudo
fi

# --- Paso 1: Actualizar la lista de paquetes ---
run_command "Actualizar la lista de paquetes (sudo apt update)" sudo apt update

# --- Paso 2: Actualizar los paquetes instalados ---
run_command "Actualizar los paquetes instalados (sudo apt upgrade)" sudo apt upgrade -y

# --- Paso 3: Instalar componentes gráficos esenciales y gestor de pantalla ---
run_command "Instalar xserver-xorg, xinit, openbox, x11-xserver-utils, lxterminal, lightdm" \
    sudo apt install -y xserver-xorg xinit openbox x11-xserver-utils lxterminal lightdm

# --- Paso 4: Instalar librerías GTK (para Pygame y otros elementos de GUI) ---
run_command "Instalar libgtk-3-0 y libcanberra-gtk-module" \
    sudo apt install -y libgtk-3-0 libcanberra-gtk-module

# --- Paso 5: Instalar VLC Media Player ---
run_command "Instalar VLC media player" sudo apt install -y vlc

# --- Paso 6: Instalar NetworkManager y sus herramientas (para configuración Wi-Fi) ---
run_command "Instalar NetworkManager y network-manager-gnome (para nmcli y gestión de Wi-Fi)" \
    sudo apt install -y network-manager network-manager-gnome

# --- Paso 7: Instalar udisks2 y util-linux (para gestión de USB y findmnt) ---
run_command "Instalar udisks2 (montaje de USB) y util-linux (que proporciona findmnt)" \
    sudo apt install -y udisks2 util-linux

# --- Paso 8: Instalar Chromium Browser y Widevine DRM (para plataformas de streaming) ---
run_command "Instalar chromium-browser y Widevine DRM (libwidevinecdm0)" \
    sudo apt install -y chromium-browser libwidevinecdm0

# --- Paso 9: Instalar Python 3 PIP y herramientas de desarrollo ---
run_command "Instalar python3-pip y python3-dev (para la gestión de paquetes de Python y compilación)" \
    sudo apt install -y python3-pip python3-dev

# --- Paso 10: Instalar dependencias adicionales de Pygame y librerías gráficas/multimedia ---
run_command "Instalar dependencias adicionales para Pygame y librerías multimedia (SDL, Mesa GLX)" \
    sudo apt install -y python3-pygame libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 libgl1-mesa-glx

# --- Paso 11: Instalar librerías de Python usando pip (asegura compatibilidad y versiones recientes) ---
log_info "Instalando librerías de Python con pip3..."
run_command "Instalar pygame vía pip3" pip3 install pygame
run_command "Instalar python-vlc vía pip3" pip3 install python-vlc
run_command "Instalar pyudev vía pip3" pip3 install pyudev

# --- Mensaje de finalización y resumen de errores ---
log_info "-----------------------------------------------------"
if [ "$ERRORS_FOUND" -eq 0 ]; then
    log_info " ¡Todas las dependencias necesarias han sido instaladas con éxito!"
    else
    log_warning " La instalación ha finalizado, pero se encontraron algunos errores."
    log_warning " Por favor, revisa los mensajes de '[ERROR]' anteriores para identificar qué falló."
    log_warning " Algunas funcionalidades del Centro Multimedia podrían no funcionar correctamente."
fi
log_info "-----------------------------------------------------"