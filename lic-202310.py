from carga_comun import ConfigCarga, ejecutar_carga


if __name__ == "__main__":
    raise SystemExit(
        ejecutar_carga(
            ConfigCarga(
                nombre="LICENCIAS",
                esquema="CSNISPLICENCIA",
                prefijo_tabla="Z_PYLOAD_LICENCIA",
                estructura="ESTRUCTURAS/CNI_LICENCIAS_JUL.txt",
                carpeta_datos="DATOS/LIC",
                archivos=(
                    "CNI_LICENCIAS.dat",
                )
            )
        )
    )