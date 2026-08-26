from carga_comun import ConfigCarga, ejecutar_carga


if __name__ == "__main__":
    raise SystemExit(
        ejecutar_carga(
            ConfigCarga(
                nombre="RNPSP",
                esquema="CSNISPRNPSP",
                prefijo_tabla="Z_PYLOAD_RNPSP",
                estructura="ESTRUCTURAS/CNI_RNPSP.txt",
                carpeta_datos="DATOS/RNPSP",
                archivos=tuple(
                    f"CNI_PERSONAL_{numero:02d}.dat"
                    for numero in range(1, 33)
                )
            )
        )
    )