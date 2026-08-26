# Cargas Oracle

Carga los archivos mensuales de LIC, RMJ, RNIP, RNPSP y VRYR en las tablas temporales de Oracle.

## Uso mensual

1. Copia todos los archivos `.dat` del periodo dentro de `DATOS`. Pueden estar directamente ahí o en cualquier subcarpeta.
2. En Windows ejecuta `ejecutar_cargas.bat`. En Linux ejecuta `./ejecutar_cargas.sh`.

No es necesario editar rutas, nombres de tablas ni fechas. El programa usa automáticamente el mes calendario anterior. Por ejemplo, si se ejecuta durante agosto de 2026, crea o reutiliza tablas terminadas en `JUL2026`.

Antes de truncar o insertar, el programa comprueba que estén los 36 archivos requeridos, que las cinco estructuras sean válidas y que funcionen las cinco conexiones Oracle. Si algo falta, termina sin modificar tablas.

La primera ejecución crea un entorno virtual, instala el controlador `oracledb` y pide una sola vez el servidor, el servicio y la contraseña de Oracle. Los guarda únicamente en `configuracion.local.json` de esa computadora; este archivo está excluido de Git. Las ejecuciones siguientes ya no piden ningún dato. La computadora debe tener Python 3 y acceso por la red institucional al listener de Oracle.

## Configuración

- Puerto: `1521`
- Usuario de base de datos: `SYS`, con conexión `SYSDBA`
- Host, servicio y contraseña: se solicitan una vez y se guardan sólo en la configuración local excluida de Git
- Datos: carpeta `DATOS`, relativa al repositorio
- Estructuras: carpeta `ESTRUCTURAS`, relativa al repositorio

La configuración puede sobrescribirse sin tocar código mediante las variables `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_SERVICE`, `ORACLE_USER` y `ORACLE_PASSWORD`. También se acepta una contraseña o usuario específico, por ejemplo `ORACLE_PASSWORD_RNIP` u `ORACLE_USER_RNIP`.

## Validar sin modificar Oracle

```powershell
python cargar_oracle.py --validar
```

## Reprocesar un periodo o una sola carga

Estas opciones son únicamente para casos extraordinarios; la ejecución mensual normal no las necesita.

```powershell
python cargar_oracle.py --periodo 202607
python cargar_oracle.py --carga rnip
python cargar_oracle.py --carga lic --carga rmj
```

Los cinco archivos antiguos con fecha `202310` se conservaron como accesos compatibles. Ahora llaman al cargador nuevo, usan rutas relativas y calculan el mes anterior automáticamente.
