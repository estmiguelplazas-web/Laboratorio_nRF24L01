#main.py
from machine import Pin, SPI, I2C
import ssd1306, time
from nrf24 import NRF24

# ---------- Hardware ----------
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
spi = SPI(0, baudrate=1000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(19), miso=Pin(16))
nrf = NRF24(spi, csn=Pin(17, Pin.OUT), ce=Pin(20, Pin.OUT))

b_var = Pin(13, Pin.IN, Pin.PULL_UP)     # variar entre opciones
b_sel = Pin(12, Pin.IN, Pin.PULL_UP)     # seleccionar
led_r = Pin(11, Pin.OUT)                 # rojo: error / no se transmitio
led_a = Pin(10, Pin.OUT)                 # amarillo: configurando / esperando
led_v = Pin(9, Pin.OUT)                  # verde: enviado / recibido

# ---------- Valores definidos ----------
CANAL_MAX = 125                          # canales 0..125 -> 2400..2525 MHz
POT_TXT = ["-18 dBm", "-12 dBm", "-6 dBm", "0 dBm"]
VELOCIDADES = ["250K", "1M", "2M"]
VEL_TXT = ["250Kbps", "1Mbps", "2Mbps"]
ROLES = ["TX", "RX"]
ENVIOS = ["Unico", "Loop 1 msg", "Loop lista"]     # modo de envio
INTERVALOS = [100, 250, 500, 1000, 2000]           # ms entre envios del loop
IV_TXT = ["100 ms", "250 ms", "500 ms", "1 s", "2 s"]
MENSAJES = [b"ALEGRIA", b"MIGUELITO",
            b"ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            b"abcdefghijklmnopqrstuvwxyz",
            b"ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"]   # maximo 32 bytes

# configuracion actual ("can" es el numero de canal directamente: 0..125)
cfg = {"rol": 0, "can": 40, "pot": 3, "vel": 1, "msg": 0, "env": 0, "iv": 3}

# ---------- Utilidades ----------
def leds(r=0, a=0, v=0):
    led_r(r)
    led_a(a)
    led_v(v)

def leer_botones():
    """Devuelve 'var', 'var_largo', 'sel' o None."""
    if b_var.value() == 0:
        time.sleep_ms(30)
        t0 = time.ticks_ms()
        while b_var.value() == 0 and time.ticks_diff(time.ticks_ms(), t0) < 800:
            time.sleep_ms(10)
        largo = b_var.value() == 0
        while b_var.value() == 0:
            time.sleep_ms(10)
        return "var_largo" if largo else "var"
    if b_sel.value() == 0:
        time.sleep_ms(30)
        while b_sel.value() == 0:
            time.sleep_ms(10)
        return "sel"
    return None

def esperar_boton():
    ev = None
    while ev is None:
        ev = leer_botones()
        time.sleep_ms(10)
    return ev

def hay_boton():
    return b_var.value() == 0 or b_sel.value() == 0

def esperar_soltar():
    while hay_boton():
        time.sleep_ms(10)
    time.sleep_ms(30)

def aplicar():
    """Carga la configuracion elegida en el NRF24L01."""
    nrf.ce(0)
    nrf.set_channel(cfg["can"])
    nrf.set_power(cfg["pot"])
    nrf.set_datarate(VELOCIDADES[cfg["vel"]])
    if cfg["rol"] == 1:
        nrf.start_rx()

# ---------- Pantallas ----------
def verificar_nrf():
    if nrf.read_reg(0x03) != 0x03:       # SETUP_AW debe leerse como 0x03
        leds(r=1)
        oled.fill(0)
        oled.text("ERROR NRF24L01", 0, 20)
        oled.text("Revise cableado", 0, 32)
        oled.show()
        while True:
            time.sleep(1)

def inicio():
    leds(a=1)
    oled.fill(0)
    oled.text("Comunicacion", 0, 8)
    oled.text("digital", 0, 20)
    oled.text("inalambrica", 0, 32)
    oled.text("GFSK - UMNG", 0, 48)
    oled.show()
    time.sleep(2.5)
    verificar_nrf()
    canal = cfg["can"]
    oled.fill(0)
    oled.text("CONFIGURACION", 0, 0)
    oled.text("Canal: %d" % canal, 0, 14)
    oled.text("Freq: %d MHz" % (2400 + canal), 0, 26)
    oled.text("Vel: " + VEL_TXT[cfg["vel"]], 0, 38)
    oled.text("Pot: " + POT_TXT[cfg["pot"]], 0, 50)
    oled.show()
    time.sleep(3)

def filas_menu():
    return ["Rol: " + ROLES[cfg["rol"]],
            "Canal: %d" % cfg["can"],
            "Pot: " + POT_TXT[cfg["pot"]],
            "Vel: " + VEL_TXT[cfg["vel"]],
            "Msg: %d/%d" % (cfg["msg"] + 1, len(MENSAJES)),
            "Envio: " + ENVIOS[cfg["env"]],
            "Intervalo: " + IV_TXT[cfg["iv"]],
            "Iniciar"]

def dibujar_menu(sel):
    filas = filas_menu()
    ini = max(0, sel - 5)                # ventana de 6 filas con desplazamiento
    oled.fill(0)
    oled.text("MENU", 0, 0)
    oled.text("%d/%d" % (sel + 1, len(filas)), 96, 0)
    for k in range(6):
        i = ini + k
        if i >= len(filas):
            break
        oled.text((">" if i == sel else " ") + filas[i], 0, 9 + 9 * k)
    oled.show()

def elegir(titulo, opciones, idx):
    """opciones: lista de (linea1, linea2). GP13 cambia, GP12 acepta."""
    while True:
        oled.fill(0)
        oled.text(titulo, 0, 0)
        l1, l2 = opciones[idx]
        oled.text(l1, 0, 20)
        oled.text(l2, 0, 32)
        oled.text("13: cambiar", 0, 46)
        oled.text("12: aceptar", 0, 55)
        oled.show()
        ev = esperar_boton()
        if ev in ("var", "var_largo"):
            idx = (idx + 1) % len(opciones)
        elif ev == "sel":
            return idx

def elegir_canal(ch):
    """Canal 0..125. GP13 corto: +1, GP13 largo: +10, GP12: aceptar."""
    while True:
        oled.fill(0)
        oled.text("CANAL", 0, 0)
        oled.text("Canal: %d" % ch, 0, 16)
        oled.text("Freq: %d MHz" % (2400 + ch), 0, 28)
        oled.text("13:+1 largo:+10", 0, 44)
        oled.text("12: aceptar", 0, 55)
        oled.show()
        ev = esperar_boton()
        if ev == "var":
            ch = (ch + 1) % (CANAL_MAX + 1)
        elif ev == "var_largo":
            ch = (ch + 10) % (CANAL_MAX + 1)
        elif ev == "sel":
            return ch

def menu():
    leds(a=1)                            # amarillo: configurando
    sel = 0
    n = len(filas_menu())
    while True:
        dibujar_menu(sel)
        ev = esperar_boton()
        if ev in ("var", "var_largo"):
            sel = (sel + 1) % n
        elif ev == "sel":
            if sel == 0:
                cfg["rol"] = elegir("ROL", [("TRANSMISOR", ""), ("RECEPTOR", "")], cfg["rol"])
            elif sel == 1:
                cfg["can"] = elegir_canal(cfg["can"])
            elif sel == 2:
                cfg["pot"] = elegir("POTENCIA TX", [(p, "") for p in POT_TXT], cfg["pot"])
            elif sel == 3:
                cfg["vel"] = elegir("VELOCIDAD", [(v, "") for v in VEL_TXT], cfg["vel"])
            elif sel == 4:
                cfg["msg"] = elegir("MENSAJE",
                    [(m.decode()[:16], m.decode()[16:32]) for m in MENSAJES], cfg["msg"])
            elif sel == 5:
                cfg["env"] = elegir("MODO DE ENVIO", [(e, "") for e in ENVIOS], cfg["env"])
            elif sel == 6:
                cfg["iv"] = elegir("INTERVALO LOOP", [(t, "") for t in IV_TXT], cfg["iv"])
            else:
                return

def pantalla_run(titulo, texto, extra, estado):
    canal = cfg["can"]
    oled.fill(0)
    oled.text("%s Canal:%d" % (titulo, canal), 0, 0)
    oled.text("%dMHz %s" % (2400 + canal, VEL_TXT[cfg["vel"]]), 0, 9)
    oled.text("Pot: " + POT_TXT[cfg["pot"]], 0, 18)
    oled.text(texto[:16], 0, 30)
    oled.text(texto[16:32], 0, 39)
    oled.text(extra[:16], 0, 48)
    oled.text(estado[:16], 0, 56)
    oled.show()

# ---------- Modo transmisor ----------
def enviar_uno(msg, cont):
    """Envia un mensaje, actualiza contadores y LEDs. Devuelve True si hubo ACK."""
    leds(a=1)
    ok = nrf.send(msg)
    print("TX:", msg, "OK" if ok else "SIN ACK")
    if ok:
        cont["ok"] += 1
        leds(v=1)
    else:
        cont["err"] += 1
        leds(r=1)
    return ok

def loop_tx(cont):
    """Envia en bucle hasta que se presione cualquier boton."""
    espera = INTERVALOS[cfg["iv"]]
    i = cfg["msg"]
    n = 0
    while True:
        msg = MENSAJES[i] if cfg["env"] == 2 else MENSAJES[cfg["msg"]]
        n += 1
        ok = enviar_uno(msg, cont)
        pantalla_run("TX", msg.decode(), "OK:%d Err:%d" % (cont["ok"], cont["err"]),
                     "Loop #%d" % n)
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < espera:
            if hay_boton():              # cualquier boton detiene el loop
                esperar_soltar()
                leds(a=1)
                return
            time.sleep_ms(5)
        if cfg["env"] == 2:
            i = (i + 1) % len(MENSAJES)

def correr_tx():
    aplicar()
    cont = {"ok": 0, "err": 0}
    estado = "12:Enviar" if cfg["env"] == 0 else "12:Iniciar loop"
    leds(a=1)
    while True:
        msg = MENSAJES[cfg["msg"]]
        pantalla_run("TX", msg.decode(), "OK:%d Err:%d" % (cont["ok"], cont["err"]), estado)
        ev = esperar_boton()
        if ev == "var":                              # siguiente mensaje
            cfg["msg"] = (cfg["msg"] + 1) % len(MENSAJES)
            estado = "Msg %d/%d" % (cfg["msg"] + 1, len(MENSAJES))
        elif ev == "var_largo":                      # volver al menu
            return
        elif ev == "sel":
            if cfg["env"] == 0:                      # envio unico
                pantalla_run("TX", msg.decode(),
                             "OK:%d Err:%d" % (cont["ok"], cont["err"]), "Enviando...")
                ok = enviar_uno(msg, cont)
                estado = "Enviado" if ok else "ERROR sin ACK"
                pantalla_run("TX", msg.decode(),
                             "OK:%d Err:%d" % (cont["ok"], cont["err"]), estado)
                time.sleep_ms(800)
                leds(a=1)
            else:                                    # loop
                loop_tx(cont)
                estado = "Loop detenido"

# ---------- Modo receptor ----------
def correr_rx():
    aplicar()
    n = 0
    texto = ""
    estado = "Esperando..."
    t_led = 0
    leds(a=1)
    pantalla_run("RX", texto, "Recibidos: %d" % n, estado)
    while True:
        if nrf.available():
            data = nrf.recv().rstrip(b'\x00')
            texto = data.decode('utf-8', 'ignore')
            n += 1
            print("RX:", texto)
            leds(v=1)
            t_led = time.ticks_add(time.ticks_ms(), 600)
            estado = "Recibido"
            pantalla_run("RX", texto, "Recibidos: %d" % n, estado)
        if t_led and time.ticks_diff(time.ticks_ms(), t_led) >= 0:
            leds(a=1)
            t_led = 0
        ev = leer_botones()
        if ev == "var_largo":                        # volver al menu
            return
        if ev == "sel":                              # reiniciar contador
            n = 0
            texto = ""
            estado = "Esperando..."
            pantalla_run("RX", texto, "Recibidos: %d" % n, estado)
        time.sleep_ms(10)

# ---------- Programa principal ----------
inicio()
while True:
    menu()
    if cfg["rol"] == 0:
        correr_tx()
    else:
        correr_rx()
