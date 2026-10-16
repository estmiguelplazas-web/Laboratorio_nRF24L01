
# Comunicación SPI con nRF24L01+ y Raspberry Pi Pico 2W

## Descripción

Este proyecto analiza la comunicación SPI entre una Raspberry Pi Pico 2W y un módulo inalámbrico nRF24L01+. Se utilizaron capturas del analizador lógico Saleae Logic 2 para identificar los comandos, los datos transmitidos y los tiempos de ejecución de diferentes operaciones.

## Objetivos

- Identificar las señales y la secuencia de comunicación SPI.
- Analizar los comandos y datos intercambiados con el módulo nRF24L01+.
- Comparar los tiempos teóricos y experimentales de transferencia.
- Examinar las señales capturadas mediante un analizador lógico.

## Hardware utilizado

- Raspberry Pi Pico 2W.
- Módulo inalámbrico nRF24L01+.
- Analizador lógico Saleae.
- Protoboard y cables de conexión.

## Software utilizado

- MicroPython.
- Saleae Logic 2.

## Pruebas realizadas

### 1. Lectura de registros

Se analizó la lectura de un registro mediante SPI, identificando el envío del comando y la recepción de los datos. El intervalo experimental fue de aproximadamente **17 µs**, frente a los **16 µs** teóricos para dos bytes a 1 MHz.

### 2. Escritura del registro RF_CH

Se identificó el comando `0x25`, correspondiente a la escritura del registro `RF_CH`, seguido del dato `0x60`. Este valor representa el canal 96, cuya frecuencia calculada es de 2496 MHz. Dicha frecuencia supera el límite superior de 2483,5 MHz de la banda ISM de 2,4 GHz, por lo que es necesario revisar la configuración del canal.

### 3. Carga del mensaje en el búfer de transmisión

Se analizó el comando `W_TX_PAYLOAD` (`0xA0`) para cargar el mensaje `ALEGRIA`, compuesto por siete caracteres ASCII. La operación comprende ocho bytes: uno de comando y siete de datos.

El tiempo teórico de transferencia fue de **64 µs**, mientras que el intervalo experimental fue de aproximadamente **74 µs**. Esta diferencia se relaciona con las pausas entre bytes durante la ejecución del programa.

## Resultados experimentales

| Operación | Bytes | Tiempo teórico | Tiempo experimental |
|---|---:|---:|---:|
| Lectura de registro | 2 | 16 µs | 17 µs |
| Escritura de RF_CH | 2 | 16 µs | 17 µs |
| Carga del mensaje | 8 | 64 µs | 74 µs |

Los tiempos teóricos se calcularon considerando una frecuencia SPI de 1 MHz y una transferencia continua. Los intervalos experimentales pueden incluir pausas entre bytes, por lo que no representan exclusivamente el tiempo activo del reloj.

## Conclusiones

Las capturas del analizador lógico permitieron identificar los comandos y datos transmitidos mediante SPI, así como comparar los tiempos teóricos y experimentales. Las diferencias observadas evidencian la influencia de las pausas entre bytes y de la temporización del programa. Asimismo, se identificó la necesidad de revisar el canal configurado en `RF_CH` antes de evaluar una transmisión inalámbrica dentro de la banda ISM de 2,4 GHz.

## Estructura del repositorio

```text
nRF24L01-SPI/
├── codigo/
├── capturas/
├── informe/
```

*Nota: las carpetas mostradas son una estructura sugerida y deben ajustarse a los archivos incluidos en el repositorio.*

## Autor

**Miguel Ángel Plazas Llanes**  
Ingeniería en Telecomunicaciones  
Universidad Militar Nueva Granada (UMNG)
