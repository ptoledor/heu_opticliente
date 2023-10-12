# %%
import os, sys, time, glob

# %%
import logging
logger = logging.getLogger(__name__)

# %% [markdown]
# -------------------------------------------------------------------------------------------------
# # Debug
# -------------------------------------------------------------------------------------------------

# %%
if __name__ == '__main__':
    debug_path = None

    if os.getenv('USERNAME') == 'hugo.ubilla':
        if 'opticliente' in os.getcwd().split(os.path.sep):
            debug_path = r'C:\Users\Hugo.ubilla\OneDrive - ARAUCO\Escritorio\opticliente\oc-modelo\tests\proys\base'

    if debug_path is not None:
        sys.argv.append(debug_path)

# %% [markdown]
# -------------------------------------------------------------------------------------------------
# # Ejecutar
# -------------------------------------------------------------------------------------------------

# %%
def ejecutar(carpeta_proy:str = None):
    """
    Objetivo
    ----------
    Funcion que ejecuta el modelo opti-cliente

    Parametros
    ----------
    carpeta_proy : str
        Carpeta en donde se quiere ejecutar el modelo
    """

    returninfo = None
    returncode = -999
    returnerrormsg = None
    returnwarnings = []

    import oc_funciones as ocf

    verbose_base = ocf.printi_get_base()
    
    returncode = -1
    
    tini = time.time()
    nompro = None
    if carpeta_proy is None:
        carpeta_proy = os.getcwd()

    try:
        if not os.path.isdir(carpeta_proy):
            raise RuntimeError('No se encuentra la carpeta del proyecto')

        with ocf.cwd(carpeta_proy):
            ocf.init()

            # Inicializar
            ocf.printi(logger.info, 'Iniciando el modelo OptiCliente', post=1)

            ocf.printi(logger.info, 'Parametros:', post=1)
            ocf.printi(logger.info, '{}: {}'.format('Carpeta', carpeta_proy))

            # Elimino los resultados anteriores, si es que hay
            ocf.printi_reset(verbose_base=verbose_base)
            ocf.printi(logger.info, 'Limpiando...', pre=1, post=1)

            for archivo in glob.glob('result_*'):
                os.remove(archivo)

            # Ejecutar modelo gams
            ocf.printi_reset(verbose_base=verbose_base)
            ocf.printi(logger.info, 'Ejecutando modelo ...', pre=1, post=1)

            import stg_modelo
            del(sys.modules['stg_modelo'])

            # Marco fin exitoso
            returncode = 0

    except Exception as error:

        returncode = 1
        returninfo = sys.exc_info()
        #raise

    finally:
        tfin = time.time()

        tdif = tfin-tini
        tuni = 's'
        if tdif > 1.5*60:
            tdif = tdif / 60.0
            tuni = 'm'
        if tdif > 1.5*60:
            tdif = tdif / 60.0
            tuni = 'h'
        teta = '{:5.1f} [{:1s}]'.format(tfin-tini, tuni)

        tail = '     {}    (exitcode: {})'.format(teta, returncode)

        if returncode == 0:
            ocf.printi_reset(verbose_base=verbose_base)
            ocf.printi(logger.info, 'Fin exitoso del modelo OptiCliente){}'.format(tail))
        else:
            if returninfo is not None:
                ocf.printi_reset(verbose_base=verbose_base)
                ocf.printi(logger.error, '')
                for linea in ocf.format_traceback(returninfo):
                    ocf.printi(logger.error, linea)
                ocf.printi(logger.error, '')
            
            if returnerrormsg is None:
                returnerrormsg = 'Exit code: {}'.format(returncode)

            ocf.printi_reset(verbose_base=verbose_base)
            ocf.printi(logger.info, 'Error al ejecutar el modelo OptiCliente {}'.format(tail))

    return (returncode, returnerrormsg, returnwarnings)

# %% [markdown]
# -------------------------------------------------------------------------------------------------
# # Main
# -------------------------------------------------------------------------------------------------

# %%
if __name__ == '__main__':
    if len(sys.argv) == 2:
        returncode, returnerrormsg, returnwarnings = ejecutar(sys.argv[1])
        sys.exit(returncode)
    
    if os.path.split(sys.argv[0])[1].lower() == 'ipykernel_launcher.py':
        returncode, returnerrormsg, returnwarnings = ejecutar(sys.argv[-1])

# %%
