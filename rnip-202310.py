from carga_comun import ConfigCarga, ejecutar_carga


if __name__ == "__main__":
    raise SystemExit(
        ejecutar_carga(
            ConfigCarga(
                nombre="RNIP",
                esquema="CSNISPRNIP",
                prefijo_tabla="Z_PYLOAD_RNIP",
                estructura="ESTRUCTURAS/CNI_RNIP.txt",
                carpeta_datos="DATOS/RNIP",
                archivos=(
                    "CNI_RNIP_01.dat",
                )
            )
        )
    )