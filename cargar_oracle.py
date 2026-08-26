#!/usr/bin/env python3
"""Carga mensual de archivos de ancho fijo a tablas temporales de Oracle."""

import argparse
import getpass
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "DATOS"
ESTRUCTURAS_DIR = BASE_DIR / "ESTRUCTURAS"
CONFIG_LOCAL = BASE_DIR / "configuracion.local.json"
MESES = ("ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC")


@dataclass(frozen=True)
class Carga:
    clave: str
    nombre: str
    usuario: str
    esquema: str
    prefijo_tabla: str
    estructura: str
    archivos: tuple[str, ...]


CARGAS = {
    "lic": Carga("lic", "Licencias", "CSNISPLICENCIA", "CSNISPLICENCIA", "Z_PYLOAD_LICENCIA", "CNI_LICENCIAS_JUL.txt", ("CNI_LICENCIAS.dat",)),
    "rmj": Carga("rmj", "Mandamientos judiciales", "CSNISPMANDAMIENTOS", "CSNISPMANDAMIENTOS", "Z_PYLOAD_MANDAMIENTOS", "CNI_MANDAMIENTOS.txt", ("CNI_Mandamientos.dat",)),
    "rnip": Carga("rnip", "Registro Nacional de Información Penitenciaria", "CSNISPRNIP", "CSNISPRNIP", "Z_PYLOAD_RNIP", "CNI_RNIP.txt", ("CNI_RNIP_01.dat",)),
    "rnpsp": Carga("rnpsp", "Registro Nacional de Personal de Seguridad Pública", "CSNISPRNPSP", "CSNISPRNPSP", "Z_PYLOAD_RNPSP", "CNI_RNPSP.txt", tuple(f"CNI_PERSONAL_{numero:02d}.dat" for numero in range(1, 33))),
    "vryr": Carga("vryr", "Vehículos robados y recuperados", "CSNISPVRYR", "CSNISPVRYR", "Z_PYLOAD_VRYR", "CNI_VRYR.txt", ("CNI_VRYR.dat",))
}


def periodo_anterior(fecha: date | None = None) -> tuple[int, int]:
    fecha = fecha or date.today()
    return (fecha.year - 1, 12) if fecha.month == 1 else (fecha.year, fecha.month - 1)


def sufijo_periodo(periodo: str | None = None) -> str:
    if periodo:
        if not re.fullmatch(r"\d{6}", periodo):
            raise ValueError("El periodo debe tener formato AAAAMM, por ejemplo 202607.")
        anio, mes = int(periodo[:4]), int(periodo[4:])
        if mes < 1 or mes > 12:
            raise ValueError("El mes del periodo debe estar entre 01 y 12.")
    else:
        anio, mes = periodo_anterior()
    return f"{MESES[mes - 1]}{anio}"


def resolver_ruta(ruta: str | Path, base: Path = BASE_DIR) -> Path:
    ruta = Path(ruta).expanduser()
    return ruta.resolve() if ruta.is_absolute() else (base / ruta).resolve()


def buscar_archivo(raiz: Path, nombre: str) -> Path:
    coincidencias = [ruta for ruta in raiz.rglob("*") if ruta.is_file() and ruta.name.casefold() == nombre.casefold()]
    if not coincidencias:
        raise FileNotFoundError(f"No se encontró {nombre} dentro de {raiz}")
    if len(coincidencias) > 1:
        rutas = "\n  - ".join(str(ruta) for ruta in coincidencias)
        raise RuntimeError(f"Se encontraron varias copias de {nombre}; deja solo la correspondiente al periodo:\n  - {rutas}")
    return coincidencias[0]


def leer_estructura(ruta: Path) -> list[tuple[str, int, int]]:
    columnas = []
    patron = re.compile(r"^\s*([A-Z0-9_]+)\s+POSITION\s+\((\d+):(\d+)\)", re.IGNORECASE)
    with ruta.open(encoding="latin-1") as archivo:
        for numero_linea, linea in enumerate(archivo, 1):
            coincidencia = patron.search(linea)
            if not coincidencia:
                raise ValueError(f"Estructura inválida en {ruta}, línea {numero_linea}: {linea.rstrip()}")
            nombre, inicio, fin = coincidencia.group(1), int(coincidencia.group(2)), int(coincidencia.group(3))
            if inicio < 1 or fin < inicio:
                raise ValueError(f"Posición inválida para {nombre} en {ruta}, línea {numero_linea}")
            columnas.append((nombre, inicio, fin))
    if not columnas:
        raise ValueError(f"La estructura está vacía: {ruta}")
    return columnas


def validar_identificador(valor: str) -> str:
    if not re.fullmatch(r"[A-Z][A-Z0-9_$#]*", valor, re.IGNORECASE):
        raise ValueError(f"Identificador Oracle inválido: {valor}")
    return valor


def crear_sql_tabla(carga: Carga, tabla: str, columnas: list[tuple[str, int, int]]) -> str:
    esquema = validar_identificador(carga.esquema)
    tabla = validar_identificador(tabla)
    definiciones = []
    for nombre, inicio, fin in columnas:
        longitud = min(fin - inicio + 1, 4000)
        definiciones.append(f"{validar_identificador(nombre)} VARCHAR2({longitud})")
    definiciones.append("TEXTFILENAME VARCHAR2(200)")
    return f"CREATE TABLE {esquema}.{tabla} ({', '.join(definiciones)})"


def obtener_driver():
    try:
        import oracledb
        return oracledb
    except ImportError:
        try:
            import cx_Oracle
            return cx_Oracle
        except ImportError as exc:
            raise RuntimeError("Falta el controlador de Oracle. Ejecuta: python -m pip install -r requirements.txt") from exc


def leer_configuracion_local() -> dict:
    if not CONFIG_LOCAL.is_file():
        return {}
    try:
        with CONFIG_LOCAL.open(encoding="utf-8") as archivo:
            configuracion = json.load(archivo)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"No se pudo leer {CONFIG_LOCAL}: {exc}") from exc
    if not isinstance(configuracion, dict):
        raise RuntimeError(f"La configuración de {CONFIG_LOCAL} debe ser un objeto JSON.")
    return configuracion


def completar_configuracion_local(carga: Carga) -> dict:
    configuracion = leer_configuracion_local()
    host = os.getenv("ORACLE_HOST") or configuracion.get("host")
    servicio = os.getenv("ORACLE_SERVICE") or configuracion.get("service")
    usuario = os.getenv(f"ORACLE_USER_{carga.clave.upper()}") or os.getenv("ORACLE_USER") or configuracion.get("user") or "SYS"
    password = os.getenv(f"ORACLE_PASSWORD_{carga.clave.upper()}") or os.getenv("ORACLE_PASSWORD") or configuracion.get("password")
    puerto = int(os.getenv("ORACLE_PORT") or configuracion.get("port") or 1521)
    faltantes = not host or not servicio or not password
    if faltantes and not sys.stdin.isatty():
        raise RuntimeError("Falta la configuración Oracle. Ejecuta una vez desde una consola interactiva o define ORACLE_HOST, ORACLE_SERVICE y ORACLE_PASSWORD.")
    if not host:
        host = input("Servidor o dirección IP de Oracle: ").strip()
    if not servicio:
        servicio = input("Nombre del servicio Oracle: ").strip()
    if not password:
        password = getpass.getpass(f"Contraseña de Oracle para {usuario}: ")
    if not host or not servicio or not password:
        raise RuntimeError("El servidor, el servicio y la contraseña Oracle son obligatorios.")
    if not faltantes:
        return {"host": str(host), "port": puerto, "service": str(servicio), "user": str(usuario), "password": str(password)}
    configuracion.update({"host": str(host), "port": puerto, "service": str(servicio), "user": str(usuario), "password": str(password)})
    try:
        with CONFIG_LOCAL.open("w", encoding="utf-8") as archivo:
            json.dump(configuracion, archivo, indent=2)
            archivo.write("\n")
        try:
            CONFIG_LOCAL.chmod(0o600)
        except OSError:
            pass
    except OSError as exc:
        raise RuntimeError(f"No se pudo guardar la configuración local en {CONFIG_LOCAL}: {exc}") from exc
    print(f"Configuración guardada únicamente en esta computadora: {CONFIG_LOCAL}")
    return configuracion


def crear_conexion(carga: Carga):
    oracle = obtener_driver()
    configuracion = completar_configuracion_local(carga)
    dsn = oracle.makedsn(configuracion["host"], configuracion["port"], service_name=configuracion["service"])
    parametros = {"user": configuracion["user"], "password": configuracion["password"], "dsn": dsn}
    if configuracion["user"].upper() == "SYS":
        parametros["mode"] = getattr(oracle, "AUTH_MODE_SYSDBA", getattr(oracle, "SYSDBA", None))
    return oracle.connect(**parametros)


def preparar_tabla(conexion, carga: Carga, tabla: str, columnas: list[tuple[str, int, int]]) -> None:
    oracle = obtener_driver()
    cursor = conexion.cursor()
    try:
        try:
            cursor.execute(crear_sql_tabla(carga, tabla, columnas))
            print(f"  Tabla creada: {carga.esquema}.{tabla}")
        except oracle.DatabaseError as exc:
            codigo = getattr(exc.args[0], "code", None)
            if codigo != 955:
                raise
        cursor.execute(f"TRUNCATE TABLE {validar_identificador(carga.esquema)}.{validar_identificador(tabla)}")
    finally:
        cursor.close()


def convertir_fila(linea: str, columnas: list[tuple[str, int, int]], nombre_archivo: str) -> tuple[str, ...]:
    linea = linea.rstrip("\r\n")
    valores = [linea[inicio - 1:fin].strip() for _, inicio, fin in columnas]
    valores.append(nombre_archivo)
    return tuple(valores)


def cargar_archivos(conexion, carga: Carga, tabla: str, columnas: list[tuple[str, int, int]], archivos: list[Path], batch_size: int) -> int:
    total = 0
    cantidad_valores = len(columnas) + 1
    marcadores = ", ".join(f":{numero}" for numero in range(1, cantidad_valores + 1))
    sql = f"INSERT INTO {validar_identificador(carga.esquema)}.{validar_identificador(tabla)} VALUES ({marcadores})"
    cursor = conexion.cursor()
    try:
        for ruta in archivos:
            procesadas = 0
            lote = []
            print(f"  Procesando: {ruta}")
            with ruta.open(encoding="latin-1") as archivo:
                for linea in archivo:
                    lote.append(convertir_fila(linea, columnas, ruta.name))
                    if len(lote) >= batch_size:
                        cursor.executemany(sql, lote)
                        conexion.commit()
                        procesadas += len(lote)
                        lote.clear()
                if lote:
                    cursor.executemany(sql, lote)
                    conexion.commit()
                    procesadas += len(lote)
            total += procesadas
            print(f"  Filas cargadas: {procesadas:,}")
    finally:
        cursor.close()
    return total


def prevalidar(cargas: list[Carga], datos_dir: Path, sufijo: str):
    if not datos_dir.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de datos: {datos_dir}")
    resultado = {}
    for carga in cargas:
        estructura = ESTRUCTURAS_DIR / carga.estructura
        if not estructura.is_file():
            raise FileNotFoundError(f"No existe la estructura: {estructura}")
        columnas = leer_estructura(estructura)
        archivos = [buscar_archivo(datos_dir, nombre) for nombre in carga.archivos]
        tabla = f"{carga.prefijo_tabla}_{sufijo}"
        crear_sql_tabla(carga, tabla, columnas)
        resultado[carga.clave] = (tabla, columnas, archivos)
    return resultado


def argumentos(argv=None):
    parser = argparse.ArgumentParser(description="Carga archivos mensuales a Oracle; de forma predeterminada usa el mes anterior.")
    parser.add_argument("--carga", action="append", choices=tuple(CARGAS), help="Carga específica; se puede repetir. Sin esta opción ejecuta las cinco.")
    parser.add_argument("--datos", default=str(DATOS_DIR), help="Carpeta raíz que contiene los .dat; puede tener subcarpetas.")
    parser.add_argument("--periodo", help="Periodo opcional AAAAMM. Si se omite, se usa el mes anterior.")
    parser.add_argument("--batch-size", type=int, default=100, help="Filas por lote (predeterminado: 100).")
    parser.add_argument("--validar", action="store_true", help="Valida archivos, estructuras y nombres sin conectarse ni modificar Oracle.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = argumentos(argv)
    try:
        if args.batch_size < 1:
            raise ValueError("--batch-size debe ser mayor que cero.")
        sufijo = sufijo_periodo(args.periodo)
        datos_dir = resolver_ruta(args.datos)
        claves = args.carga or list(CARGAS)
        cargas = [CARGAS[clave] for clave in claves]
        print(f"Periodo de carga: {sufijo}")
        print(f"Carpeta de datos: {datos_dir}")
        preparados = prevalidar(cargas, datos_dir, sufijo)
        for carga in cargas:
            tabla, columnas, archivos = preparados[carga.clave]
            print(f"{carga.nombre}: {carga.esquema}.{tabla} | {len(columnas)} columnas | {len(archivos)} archivo(s)")
        if args.validar:
            print("Validación terminada. No se realizó ningún cambio en Oracle.")
            return 0

        print("Validando conexiones Oracle antes de modificar tablas...")
        conexion = crear_conexion(cargas[0])
        conexion.close()
        print("  Conexión correcta: SYS como SYSDBA")

        totales = {}
        for carga in cargas:
            tabla, columnas, archivos = preparados[carga.clave]
            print(f"Iniciando {carga.nombre}...")
            conexion = crear_conexion(carga)
            try:
                preparar_tabla(conexion, carga, tabla, columnas)
                totales[carga.clave] = cargar_archivos(conexion, carga, tabla, columnas, archivos, args.batch_size)
            finally:
                conexion.close()
        print("Carga terminada correctamente.")
        for carga in cargas:
            print(f"  {carga.clave.upper()}: {totales[carga.clave]:,} filas")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR durante la carga: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
