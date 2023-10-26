# %%
import numpy as np
import pandas as pd
import datetime
import dateutil.relativedelta as relativedelta
import os

if __name__ == '__main__':

    if os.getenv('USERNAME') == 'hugo.ubilla':
        if 'opticliente' in os.getcwd().split(os.path.sep):
            os.chdir(r'C:\Users\Hugo.ubilla\OneDrive - ARAUCO\Escritorio\opticliente\oc-modelo\tests\proys\base')

os.chdir(r'C:\Trabajo\203_Ale\heuristica_opticliente_3oct\tests\proys\base')
# %%
# Lectura de parametros
parametros = pd.read_csv("par.csv", sep = ";")
parametros = parametros.to_dict(orient='records')[0]

mes_inicio = parametros["mes_inicio"]
año_inicio = parametros["ano_inicio"]
horizonte_planificacion = parametros["horizonte_planificacion"]


# %%
#temporada: 1 es verano, 0 es invierno.
inv_verano = pd.read_excel('verano.xlsx', sheet_name='veranos', skiprows=1)
inv_verano = pd.melt(inv_verano, id_vars=['zona'], value_vars=inv_verano.columns[1:] , var_name='mes_no', value_name='temporada')

date_inicio = datetime.datetime(year=año_inicio, month=mes_inicio, day=10)
primer_periodo = str(date_inicio.year) + '-' + str(date_inicio.month).zfill(2)

periodos = []
for mes in range(horizonte_planificacion + 1):
    aux_per = date_inicio + relativedelta.relativedelta(months=mes)
    periodos.append(str(aux_per.year) + '-' + str(aux_per.month).zfill(2))

periodos = pd.DataFrame(periodos, columns=['mes_real'])
periodos['año'] = periodos['mes_real'].str[:4]
periodos['mes_no'] = periodos['mes_real'].str[5:7].astype(int)
periodos['mes_planificado'] = periodos.index + 1
periodos = pd.merge(periodos, inv_verano, how='left', on='mes_no')
periodos.head()

# %%
rango_mes_tipo = pd.read_excel('parametro_antiguedad.xlsx', sheet_name='rango_mes_tipo')
dict_tiporango = rango_mes_tipo.set_index(['mes_planificado', 'nombre_planta', 'producto'])['id_tipo_rango'].to_dict()

rangos_demanda = pd.read_excel('parametro_antiguedad.xlsx', sheet_name='parametro_antiguedad')

rangos_demanda_ext = pd.DataFrame(columns=['id_tipo_rango', 'rango', 'antiguedad'])
for ix in rangos_demanda.index:
    for ant in range(rangos_demanda.at[ix, 'inicio_rango'], rangos_demanda.at[ix, 'fin_rango'] + 1):
        aux = [[rangos_demanda.at[ix, 'id_tipo_rango'], rangos_demanda.at[ix, 'rango'], ant ]]
        aux = pd.DataFrame(aux, columns=['id_tipo_rango', 'rango', 'antiguedad'])
        rangos_demanda_ext = pd.concat([rangos_demanda_ext, aux], ignore_index=True)

rangos_demanda_ext['antiguedad'] = rangos_demanda_ext['antiguedad'].astype(np.int64).astype(str)

# %%
'''
1. calculo de stock inicial del mes
2. calculo de demanda del mes
3. algoritmo
4. calculo de stock inicial mes siguiente
'''

# %%
#Lectura de parametros planta
parametros_planta = pd.read_excel('plantas.xlsx', sheet_name='parametros_planta')
parametros_planta['stock_ideal_planta'] = (parametros_planta['ideal_dias_rollizos'] + parametros_planta['ideal_dias_astillas']) * parametros_planta['consumo_diario'] 
dict_plantas_stock_ideal = parametros_planta.set_index(['nombre_planta', 'producto'])['stock_ideal_planta'].to_dict()
dict_prioridad_abastecimiento = parametros_planta.set_index(['nombre_planta', 'producto'])['Prioridad_abastecimiento'].to_dict()

#Lectura consumo plantas
consumo_plantas = pd.read_excel('plantas.xlsx', sheet_name='consumo_plantas')
consumo_plantas = pd.melt(consumo_plantas, consumo_plantas.columns[:2], consumo_plantas.columns[2:], var_name='mes_planificado', value_name='volumen_consumo')
dict_plantas_consumo = consumo_plantas.set_index(['mes_planificado', 'nombre_planta', 'producto'])['volumen_consumo'].to_dict()

# %%
#Carga Ingresos: Compras y produccion
base_ingresos = pd.read_excel('ingresos.xlsx', sheet_name='ingresos')

#Temporada de ingresos
dict_temp_ingresos = pd.merge(base_ingresos, periodos, how='left', on='zona')
dict_temp_ingresos = dict_temp_ingresos[['id_ingreso', 'mes_planificado', 'temporada']]
dict_temp_ingresos = dict_temp_ingresos.set_index(['id_ingreso', 'mes_planificado'])['temporada'].to_dict()

#Carga Ingreso: Volumen mensual
vol_ingresos = pd.read_excel('ingresos_volumen.xlsx', sheet_name='ingresovolumen', skiprows=1)
vol_ingresos = pd.melt(vol_ingresos, vol_ingresos.columns[:1], vol_ingresos.columns[1:], var_name='mes_planificado', value_name='volumen')
vol_ingresos = pd.merge(base_ingresos, vol_ingresos, on='id_ingreso', how='left')
# vol_ingresos.to_csv('ingresos_volumen.csv', sep=';', decimal=',', index=False)

# %%
### Carga de Almacenes ###
base_almacenes = pd.read_excel('almacenes.xlsx', sheet_name='almacenes')
no_almacenes = len(base_almacenes)

alm_mes_temp = base_almacenes[['id_almacen', 'nombre_planta', 'producto', 'zona', 'carpeta']].copy().drop_duplicates(ignore_index=True)
alm_mes_temp = pd.merge(alm_mes_temp, periodos, how='left', on='zona')
alm_mes_temp['bloqueo'] = False
alm_mes_temp.loc[(alm_mes_temp['carpeta'] == 'tierra') & (alm_mes_temp['temporada'] == 0), 'bloqueo'] = True
dict_temp_almacen = alm_mes_temp.set_index(['id_almacen', 'mes_planificado'])['temporada'].to_dict()

#Stock almacen EN MES 0
stock_almacen = pd.read_excel('almacenes_stock2.xlsx', sheet_name='stock')
stock_almacen = stock_almacen[['id_almacen', 'ant_meses', 'cierre_stock']]
stock_almacen.columns = ['id_almacen', 'antiguedad', 'stock_inicial']

stock_almacen = pd.merge(base_almacenes, stock_almacen, how='left', on='id_almacen')
stock_almacen['antiguedad'] = stock_almacen['antiguedad'].astype(np.int64).astype(str)
stock_almacen.insert(loc=len(stock_almacen.columns)-1, column='mes_planificado', value=1)


dict_alm_acanche = stock_almacen[['id_almacen', 'id_almacen_acanche']].drop_duplicates().set_index('id_almacen')['id_almacen_acanche'].to_dict()
dict_alm_carpeta = stock_almacen[['id_almacen', 'carpeta']].drop_duplicates().set_index('id_almacen')['carpeta'].to_dict()

#Prioridad de almacenes
alma_prio = stock_almacen.copy()
alma_prio = alma_prio[['id_almacen', 'prioridad']].drop_duplicates(ignore_index=True)
alma_prio.columns = ['id', 'prioridad']


# %%
periodos
rango_mes_tipo
dict_tiporango
rangos_demanda
rangos_demanda_ext

dict_plantas_stock_ideal
dict_plantas_consumo

dict_temp_almacen
dict_temp_ingresos
dict_alm_acanche

stock_almacen
vol_ingresos


# %%
#Captura de todos los nodos
nodos_planta = pd.DataFrame(parametros_planta['nombre_planta'].unique(), columns=['id'])
nodos_planta['tipo_id'] = 'planta'

nodos_almacen = pd.DataFrame(stock_almacen['id_almacen'].unique(), columns=['id'])
nodos_almacen['tipo_id'] = 'almacen'

all_nodos = pd.concat([nodos_planta, nodos_almacen], ignore_index=True)

filtrado_almacen = base_almacenes[['id_almacen', 'nombre_planta', 'producto']].copy()

# %%
#Construccion de tabla de stock inicial
aux1 = parametros_planta[['nombre_planta', 'producto', 'stock_inicial']].copy().rename(columns={'stock_inicial':'volumen'})
aux1['mes'] = 1
aux1['antiguedad'] = '0'
aux1['tipo_id'] = 'planta'
aux1 = aux1[['mes', 'tipo_id', 'nombre_planta', 'producto', 'antiguedad', 'volumen']]
aux1.columns = ['mes', 'tipo_id', 'id', 'producto', 'antiguedad', 'volumen']

aux2 = stock_almacen[['mes_planificado', 'id_almacen', 'producto', 'antiguedad', 'stock_inicial']].copy()
aux2.columns = ['mes', 'id', 'producto', 'antiguedad', 'volumen']
aux2['tipo_id'] = 'almacen'

tabla_stock_original = pd.concat([aux1, aux2], ignore_index=True)
tabla_stock_original['mes'] = tabla_stock_original['mes'].astype(np.int64)
tabla_stock_original['volumen'] = tabla_stock_original['volumen'].fillna(0)
tabla_stock_original

# %%

col_tabla_movimiento = ['mes', 'origen', 'destino', 'producto', 'antiguedad', 'volumen']
tabla_movimiento = pd.DataFrame(columns=col_tabla_movimiento)

balance_producto = pd.DataFrame()
tabla_demanda_original = pd.DataFrame()
tabla_demanda_mod1 = pd.DataFrame()
tabla_demanda_mod2 = pd.DataFrame()
tabla_stock = pd.DataFrame()

def agregar_movimiento(mes, origen, destino, producto, antiguedad, volumen):
    fila = [mes, origen, destino, producto, antiguedad, volumen]
    fila = pd.DataFrame([fila], columns=tabla_movimiento.columns)
    return pd.concat([tabla_movimiento, fila], ignore_index=True)


for planta in parametros_planta['nombre_planta'].unique():
    for producto in parametros_planta[parametros_planta['nombre_planta'] == planta]['producto'].unique():
        for mes in range(1, horizonte_planificacion+1):
            print(' ')
            print(mes, planta, producto)

            nodos_activos = filtrado_almacen[(filtrado_almacen['nombre_planta'] == planta) & (filtrado_almacen['producto'] == producto)].copy()
            nodos_activos = list(nodos_activos['id_almacen'])
            nodos_activos.append(planta)

            if mes == 1:
                #Filtrar planta-producto-mes
                tabla_stock_mes = tabla_stock_original[(tabla_stock_original['mes'] == mes) & (tabla_stock_original['id'].isin(nodos_activos)) & (tabla_stock_original['producto'] == producto)]
                tabla_stock = pd.concat([tabla_stock, tabla_stock_mes], ignore_index=True)

            else:
                tabla_stock_mes = tabla_stock[(tabla_stock['mes'] == mes) & (tabla_stock['id'].isin(nodos_activos)) & (tabla_stock['producto'] == producto)]
            
            nodos_activos = pd.DataFrame(nodos_activos, columns=['id'])
            nodos_activos['tipo_id'] = 'almacen'
            nodos_activos.loc[nodos_activos['id'] == planta, 'tipo_id'] = 'planta'

            tipo_rango = dict_tiporango[(mes, planta, producto)]
            rde = rangos_demanda_ext.copy()
            rde = rde.loc[rde['id_tipo_rango'] == tipo_rango].drop(columns=['id_tipo_rango'])


            #Demanda del mes
            stock_inicial_planta = tabla_stock_mes[(tabla_stock_mes['id'] == planta)].reset_index(drop=True)
            if len(stock_inicial_planta) == 0:
                stock_inicial_planta = 0
            elif len(stock_inicial_planta) > 1:
                raise ValueError('El stock inicial de la planta debiera ser unico')
            else:
                stock_inicial_planta = stock_inicial_planta.at[0, 'volumen']
            
            stock_ideal_planta = dict_plantas_stock_ideal[(planta, producto)]
            consumo_planta = dict_plantas_consumo[(mes, planta, producto)] 

            demanda = stock_ideal_planta + consumo_planta - stock_inicial_planta
            dpla = [mes, planta, producto, stock_ideal_planta, consumo_planta, stock_inicial_planta, demanda]
            dpla = pd.DataFrame([dpla], columns=['mes_planificado', 'nombre_planta', 'producto', 'stock_ideal', 'consumo', 'stock_inicio_mes', 'demanda'])
            dpla = pd.merge(dpla, rangos_demanda[rangos_demanda['id_tipo_rango'] == tipo_rango], how='cross')
            dpla['demanda_rango'] = dpla['demanda'] * dpla['porcentaje']
            tabla_demanda_original = pd.concat([tabla_demanda_original, dpla], ignore_index=True)


            #Almacenes disponibles
            alm_disponible = alm_mes_temp.copy()
            alm_disponible = alm_disponible[(alm_disponible['mes_planificado'] == mes)
                                            & (alm_disponible['nombre_planta'] == planta)
                                            & (alm_disponible['producto'] == producto)
                                            & (alm_disponible['bloqueo'] == False)]
            alm_disponible = list(alm_disponible['id_almacen'].unique())

            #Almacenes con rango 
            alma = tabla_stock_mes[tabla_stock_mes['tipo_id'] == 'almacen'].copy()
            alma = alma[(alma['id'].isin(alm_disponible))]
            alma = pd.merge(alma, rde, how='left', on=['antiguedad'])

            if len(alma[alma['rango'].isnull()]) > 0:
                print('ERROR: las siguientes antiguedades no tienen un rango en el "tipo_rango" ')
                print(alma[alma['rango'].isnull()]['antiguedad'].unique())

            #ingdir: ingresos directos
            ingdir = vol_ingresos.copy()
            ingdir = ingdir.loc[(ingdir['nombre_planta'] == planta) 
                            & (ingdir['producto'] == producto) 
                            & (ingdir['mes_planificado'] == mes)
                            & (ingdir['tipo_ingreso'] == 'directo_planta')]
            
            #inglib: ingresos libres
            inglib = vol_ingresos.copy()
            inglib = inglib.loc[(inglib['nombre_planta'] == planta) 
                & (inglib['producto'] == producto) 
                & (inglib['mes_planificado'] == mes)
                & (inglib['tipo_ingreso'] == 'libre')]

            #ingalm: ingreso directo a almacen
            ingalm = vol_ingresos.copy()
            ingalm = ingalm.loc[(ingalm['nombre_planta'] == planta) 
                & (ingalm['producto'] == producto) 
                & (ingalm['mes_planificado'] == mes)
                & (ingalm['tipo_ingreso'] == 'directo_almacen')]            
          

            print('Algo 1: Modificacion de demandas. Desde lo mas antiguo a lo mas nuevo')
            #Si la planta no tiene demanda en el mes actual, se continua el ciclo.
            dpla = dpla.sort_values(by='inicio_rango', ascending=False)
            
            alma_aux = alma.groupby(['rango'], as_index=False).agg(volumen=('volumen', 'sum'))
            alma_aux = alma_aux.sort_values(by='rango', ascending=False).reset_index(drop=True)
            dpla = pd.merge(dpla, alma_aux, how='left', on=['rango'])
            dpla['volumen'] = dpla['volumen'].fillna(0)

            #Algoritmo Ale
            for ix in dpla.index[:-1]:
                if dpla.at[ix, 'volumen'] < dpla.at[ix, 'demanda_rango']:
                    dpla.at[ix + 1, 'demanda_rango'] +=  dpla.at[ix, 'demanda_rango'] - dpla.at[ix, 'volumen']
                    dpla.at[ix, 'demanda_rango'] = dpla.at[ix, 'volumen']
            dpla = dpla.drop(columns=['volumen']).sort_values(by=['mes_planificado', 'inicio_rango'])

            tabla_demanda_mod1 = pd.concat([tabla_demanda_mod1, dpla], ignore_index=True)





            print('Algo 2: Modificacion de demandas. El ingreso directo debe estar complemente incluido en la demanda del primer rango')
            dpla = dpla.sort_values(by='inicio_rango', ascending=True).reset_index(drop=True)
            vol_demanda = dpla['demanda_rango'].sum()
            
            #Se filtran los ingresos de planta directo.
            vol_fresco = 0
            aux_ingdir = ingdir.groupby(['nombre_planta', 'producto', 'mes_planificado'], as_index=False).agg({'volumen':'sum'})
            if len(aux_ingdir) > 0:
                #Indicadores
                vol_fresco = aux_ingdir.at[0, 'volumen']
                vol_stock = vol_fresco - vol_demanda
                if vol_stock < 0:
                    vol_stock = 0.0

                # print(f'vol_demanda: {vol_demanda}, vol_ingreso_directo: {vol_fresco}, vol_stock: {vol_stock}')

                #Algoritmo Ale
                if vol_fresco > dpla.at[0, 'demanda_rango']:
                    dpla.at[1, 'demanda_rango'] = dpla.at[1, 'demanda_rango'] + dpla.at[0, 'demanda_rango'] - vol_fresco
                    dpla.at[0, 'demanda_rango'] = vol_fresco

                    for ix in dpla.index[1:-1]:
                        if dpla.at[ix, 'demanda_rango'] < 0:
                            dpla.at[ix+1, 'demanda_rango'] = dpla.at[ix+1, 'demanda_rango'] + dpla.at[ix, 'demanda_rango']
                            dpla.at[ix, 'demanda_rango'] = 0
                
                    if dpla.at[len(dpla)-1, 'demanda_rango'] < 0:
                        dpla.at[len(dpla)-1, 'demanda_rango'] = 0
               
                # display(dpla)
            demanda_modificada = dpla['demanda_rango'].sum()
            tabla_demanda_mod2 = pd.concat([tabla_demanda_mod2, dpla], ignore_index=True)




            print('Algo 3: Venta de ingresos directos')
            #Ingresos_directos -> planta
            for ix in ingdir.index:
                tabla_movimiento = agregar_movimiento(mes=mes,
                                                      origen=ingdir.at[ix, 'id_ingreso'],
                                                      destino=planta,
                                                      producto=producto,
                                                      antiguedad=0,
                                                      volumen=ingdir.at[ix,'volumen'])

            demanda_faltante = dpla.at[0, 'demanda_rango'] - vol_fresco





            # Lo que voy a hacer ahora es una supermala practica y me averguenza profundamente.
            # Sin embargo, si funciona, quien podria ser capaz de decir algo al respecto?.
            # Inicio de la mala practica

            if dict_prioridad_abastecimiento[(planta,producto)] == 'Almacenes':            

                print('Algo 5: Se completa demanda faltante en primer rango (0-3) desde almacenes')
                #Almacen -> Plata | Almacen -> Almacen
                #agregar prioridad a alma.
                alma = pd.merge(alma, alma_prio, how='left', on='id')
                alma = alma.sort_values(by=['prioridad', 'antiguedad'], ascending=[True, False])
                #Solo se itera sobre el primer rango.
                aux_rangos = rangos_demanda[rangos_demanda['id_tipo_rango'] == tipo_rango].reset_index(drop=True)
                aux_rangos = np.arange(aux_rangos.at[0, 'fin_rango'], aux_rangos.at[0, 'inicio_rango']-1, -1)
                aux_rangos


                for r in aux_rangos:
                    for ix in alma.index:
                        tempo_almacen_actual = dict_temp_almacen[(alma.at[ix, 'id'], mes)]
                        tempo_almacen_siguiente = dict_temp_almacen[(alma.at[ix, 'id'], mes+1)]

                        if dict_alm_carpeta[alma.at[ix,'id']] == 'tierra' and tempo_almacen_actual == 1 and tempo_almacen_siguiente == 0:
                            almacen_destino = dict_alm_acanche[alma.at[ix,'id']]
                        else:
                            almacen_destino = alma.at[ix,'id']
            

                        if alma.at[ix,'antiguedad'] == str(r):
                            if demanda_faltante >= alma.at[ix, 'volumen']:
                                #Movimiento Almacen-Planta
                                tabla_movimiento = agregar_movimiento(mes=mes,
                                                                    origen=alma.at[ix,'id'],
                                                                    destino=planta,
                                                                    producto=producto,
                                                                    antiguedad=alma.at[ix,'antiguedad'],
                                                                    volumen=alma.at[ix, 'volumen'])
                                demanda_faltante = demanda_faltante - alma.at[ix, 'volumen']

                            elif demanda_faltante > 0 and alma.at[ix, 'volumen'] > demanda_faltante:
                                #Movimiento Almacen-Planta
                                tabla_movimiento = agregar_movimiento(mes=mes,
                                                                    origen=alma.at[ix,'id'],
                                                                    destino=planta,
                                                                    producto=producto,
                                                                    antiguedad=alma.at[ix,'antiguedad'],
                                                                    volumen=demanda_faltante)
                                #Movimiento Almacen->Almacen-Acanche
                                tabla_movimiento = agregar_movimiento(mes=mes,
                                                                    origen=alma.at[ix,'id'],
                                                                    destino=almacen_destino,
                                                                    producto=producto,
                                                                    antiguedad=alma.at[ix,'antiguedad'],
                                                                    volumen=alma.at[ix, 'volumen'] - demanda_faltante)
                                demanda_faltante = 0
                            
                            elif demanda_faltante == 0:
                                #Movimiento Almacen->Almacen-Acanche
                                tabla_movimiento = agregar_movimiento(mes=mes,
                                                                    origen=alma.at[ix,'id'],
                                                                    destino=almacen_destino,
                                                                    producto=producto,
                                                                    antiguedad=alma.at[ix,'antiguedad'],
                                                                    volumen=alma.at[ix, 'volumen'])
                                



                print('Algo 4: Venta de ingresos libres')
                #De ingresos libres -> planta y almacen.
                for ix in inglib.index:
                    #Identificacion de almacen de destino
                    tempo_ingreso_actual = dict_temp_ingresos[(inglib.at[ix, 'id_ingreso'], mes)]
                    tempo_ingreso_siguiente = dict_temp_ingresos[(inglib.at[ix, 'id_ingreso'], mes+1)]

                    if tempo_ingreso_actual == 1 and tempo_ingreso_siguiente == 0:
                        almacen_ingreso = inglib.at[ix, 'almacen_verano']
                        almacen_ingreso = dict_alm_acanche[almacen_ingreso]
                    elif tempo_ingreso_actual == 1:
                        almacen_ingreso = inglib.at[ix, 'almacen_verano']
                    elif tempo_ingreso_actual == 0:
                        almacen_ingreso = inglib.at[ix, 'almacen_invierno']
                    else:
                        raise NotImplementedError('A4-1. Existe un caso no considerado en el ciclo')


                    if demanda_faltante >= inglib.at[ix, 'volumen']:
                        tabla_movimiento = agregar_movimiento(mes=mes,
                                                            origen=inglib.at[ix, 'id_ingreso'],
                                                            destino=planta,
                                                            producto=producto,
                                                            antiguedad=0,
                                                            volumen=inglib.at[ix, 'volumen'])
                        demanda_faltante = demanda_faltante - inglib.at[ix, 'volumen']

                    elif demanda_faltante > 0 and inglib.at[ix, 'volumen'] > demanda_faltante:
                        tabla_movimiento = agregar_movimiento(mes=mes,
                                                            origen=inglib.at[ix, 'id_ingreso'],
                                                            destino=planta,
                                                            producto=producto,
                                                            antiguedad=0,
                                                            volumen=demanda_faltante)                    

                        tabla_movimiento = agregar_movimiento(mes=mes,
                                                            origen=inglib.at[ix, 'id_ingreso'],
                                                            destino=almacen_ingreso,
                                                            producto=producto,
                                                            antiguedad=0,
                                                            volumen=inglib.at[ix, 'volumen'] - demanda_faltante)
                        
                        demanda_faltante = 0

                    elif demanda_faltante == 0:
                        tabla_movimiento = agregar_movimiento(mes=mes,
                                                            origen=inglib.at[ix, 'id_ingreso'],
                                                            destino=almacen_ingreso,
                                                            producto=producto,
                                                            antiguedad=0,
                                                            volumen=inglib.at[ix, 'volumen'])
                    
                    else:
                        raise NotImplementedError('A4-2. Existe un caso no considerado en el ciclo')

            
            elif dict_prioridad_abastecimiento[(planta,producto)] == 'Ingresos':

                print('Algo 4: Venta de ingresos libres')
                #De ingresos libres -> planta y almacen.
                for ix in inglib.index:
                    #Identificacion de almacen de destino
                    tempo_ingreso_actual = dict_temp_ingresos[(inglib.at[ix, 'id_ingreso'], mes)]
                    tempo_ingreso_siguiente = dict_temp_ingresos[(inglib.at[ix, 'id_ingreso'], mes+1)]

                    if tempo_ingreso_actual == 1 and tempo_ingreso_siguiente == 0:
                        almacen_ingreso = inglib.at[ix, 'almacen_verano']
                        almacen_ingreso = dict_alm_acanche[almacen_ingreso]
                    elif tempo_ingreso_actual == 1:
                        almacen_ingreso = inglib.at[ix, 'almacen_verano']
                    elif tempo_ingreso_actual == 0:
                        almacen_ingreso = inglib.at[ix, 'almacen_invierno']
                    else:
                        raise NotImplementedError('A4-1. Existe un caso no considerado en el ciclo')


                    if demanda_faltante >= inglib.at[ix, 'volumen']:
                        tabla_movimiento = agregar_movimiento(mes=mes,
                                                            origen=inglib.at[ix, 'id_ingreso'],
                                                            destino=planta,
                                                            producto=producto,
                                                            antiguedad=0,
                                                            volumen=inglib.at[ix, 'volumen'])
                        demanda_faltante = demanda_faltante - inglib.at[ix, 'volumen']

                    elif demanda_faltante > 0 and inglib.at[ix, 'volumen'] > demanda_faltante:
                        tabla_movimiento = agregar_movimiento(mes=mes,
                                                            origen=inglib.at[ix, 'id_ingreso'],
                                                            destino=planta,
                                                            producto=producto,
                                                            antiguedad=0,
                                                            volumen=demanda_faltante)                    

                        tabla_movimiento = agregar_movimiento(mes=mes,
                                                            origen=inglib.at[ix, 'id_ingreso'],
                                                            destino=almacen_ingreso,
                                                            producto=producto,
                                                            antiguedad=0,
                                                            volumen=inglib.at[ix, 'volumen'] - demanda_faltante)
                        
                        demanda_faltante = 0

                    elif demanda_faltante == 0:
                        tabla_movimiento = agregar_movimiento(mes=mes,
                                                            origen=inglib.at[ix, 'id_ingreso'],
                                                            destino=almacen_ingreso,
                                                            producto=producto,
                                                            antiguedad=0,
                                                            volumen=inglib.at[ix, 'volumen'])
                    
                    else:
                        raise NotImplementedError('A4-2. Existe un caso no considerado en el ciclo')

            



                print('Algo 5: Se completa demanda faltante en primer rango (0-3) desde almacenes')
                #Almacen -> Plata | Almacen -> Almacen
                #agregar prioridad a alma.
                alma = pd.merge(alma, alma_prio, how='left', on='id')
                alma = alma.sort_values(by=['prioridad', 'antiguedad'], ascending=[True, False])
                #Solo se itera sobre el primer rango.
                aux_rangos = rangos_demanda[rangos_demanda['id_tipo_rango'] == tipo_rango].reset_index(drop=True)
                aux_rangos = np.arange(aux_rangos.at[0, 'fin_rango'], aux_rangos.at[0, 'inicio_rango']-1, -1)
                aux_rangos


                for r in aux_rangos:
                    for ix in alma.index:
                        tempo_almacen_actual = dict_temp_almacen[(alma.at[ix, 'id'], mes)]
                        tempo_almacen_siguiente = dict_temp_almacen[(alma.at[ix, 'id'], mes+1)]

                        if dict_alm_carpeta[alma.at[ix,'id']] == 'tierra' and tempo_almacen_actual == 1 and tempo_almacen_siguiente == 0:
                            almacen_destino = dict_alm_acanche[alma.at[ix,'id']]
                        else:
                            almacen_destino = alma.at[ix,'id']
            

                        if alma.at[ix,'antiguedad'] == str(r):
                            if demanda_faltante >= alma.at[ix, 'volumen']:
                                #Movimiento Almacen-Planta
                                tabla_movimiento = agregar_movimiento(mes=mes,
                                                                    origen=alma.at[ix,'id'],
                                                                    destino=planta,
                                                                    producto=producto,
                                                                    antiguedad=alma.at[ix,'antiguedad'],
                                                                    volumen=alma.at[ix, 'volumen'])
                                demanda_faltante = demanda_faltante - alma.at[ix, 'volumen']

                            elif demanda_faltante > 0 and alma.at[ix, 'volumen'] > demanda_faltante:
                                #Movimiento Almacen-Planta
                                tabla_movimiento = agregar_movimiento(mes=mes,
                                                                    origen=alma.at[ix,'id'],
                                                                    destino=planta,
                                                                    producto=producto,
                                                                    antiguedad=alma.at[ix,'antiguedad'],
                                                                    volumen=demanda_faltante)
                                #Movimiento Almacen->Almacen-Acanche
                                tabla_movimiento = agregar_movimiento(mes=mes,
                                                                    origen=alma.at[ix,'id'],
                                                                    destino=almacen_destino,
                                                                    producto=producto,
                                                                    antiguedad=alma.at[ix,'antiguedad'],
                                                                    volumen=alma.at[ix, 'volumen'] - demanda_faltante)
                                demanda_faltante = 0
                            
                            elif demanda_faltante == 0:
                                #Movimiento Almacen->Almacen-Acanche
                                tabla_movimiento = agregar_movimiento(mes=mes,
                                                                    origen=alma.at[ix,'id'],
                                                                    destino=almacen_destino,
                                                                    producto=producto,
                                                                    antiguedad=alma.at[ix,'antiguedad'],
                                                                    volumen=alma.at[ix, 'volumen'])       
            
            else:
                raise ValueError('metodo_priorizado debe tomar uno de los siguientes valores [Ingresos, Almacenes]')
            #Fin de la mala practica
            

                
            print('Algo 6: Se completa la demanda faltante para el resto de los rangos (4-6 en adelante)')
            aux_rangos = rangos_demanda[rangos_demanda['id_tipo_rango'] == tipo_rango].reset_index(drop=True)
            for ix in aux_rangos.index[1:]:
                rango_actual = aux_rangos.at[ix, 'rango']
                demanda_faltante += dpla.set_index('rango').at[rango_actual, 'demanda_rango']
                # print(f'Inicio ciclo: rango {rango_actual}, demanda faltante {demanda_faltante}')
                it_rangos = np.arange(aux_rangos.at[ix, 'fin_rango'], aux_rangos.at[ix, 'inicio_rango']-1, -1)
            
                for r in it_rangos:
                    for ix in alma.index:
                        tempo_almacen_actual = dict_temp_almacen[(alma.at[ix, 'id'], mes)]
                        tempo_almacen_siguiente = dict_temp_almacen[(alma.at[ix, 'id'], mes+1)]
                        if dict_alm_carpeta[alma.at[ix,'id']] == 'tierra' and tempo_almacen_actual == 1 and tempo_almacen_siguiente == 0:
                            almacen_destino = dict_alm_acanche[alma.at[ix,'id']]
                        else:
                            # print('Se mantiene almacen', mes, almacen_destino)
                            almacen_destino = alma.at[ix,'id']
                        
            
                        if alma.at[ix,'antiguedad'] == str(r):
                            if demanda_faltante >= alma.at[ix, 'volumen']:
                                #Movimiento Almacen-Planta
                                tabla_movimiento = agregar_movimiento(mes=mes,
                                                                    origen=alma.at[ix,'id'],
                                                                    destino=planta,
                                                                    producto=producto,
                                                                    antiguedad=alma.at[ix,'antiguedad'],
                                                                    volumen=alma.at[ix, 'volumen'])
                                demanda_faltante = demanda_faltante - alma.at[ix, 'volumen']

                            elif demanda_faltante > 0 and alma.at[ix, 'volumen'] > demanda_faltante:
                                #Movimiento Almacen-Planta
                                tabla_movimiento = agregar_movimiento(mes=mes,
                                                                    origen=alma.at[ix,'id'],
                                                                    destino=planta,
                                                                    producto=producto,
                                                                    antiguedad=alma.at[ix,'antiguedad'],
                                                                    volumen=demanda_faltante)
                                #Movimiento Almacen->Almacen-Acanche
                                tabla_movimiento = agregar_movimiento(mes=mes,
                                                                    origen=alma.at[ix,'id'],
                                                                    destino=almacen_destino,
                                                                    producto=producto,
                                                                    antiguedad=alma.at[ix,'antiguedad'],
                                                                    volumen=alma.at[ix, 'volumen'] - demanda_faltante)
                                demanda_faltante = 0
                            
                            elif demanda_faltante == 0:
                                #Movimiento Almacen->Almacen-Acanche
                                tabla_movimiento = agregar_movimiento(mes=mes,
                                                                    origen=alma.at[ix,'id'],
                                                                    destino=almacen_destino,
                                                                    producto=producto,
                                                                    antiguedad=alma.at[ix,'antiguedad'],
                                                                    volumen=alma.at[ix, 'volumen'])
                            





            print('Algo 7: Ingresos "directo a almacen"')
            #De ingresos libres -> planta y almacen.
            for ix in ingalm.index:
                #Identificacion de almacen de destino
                tempo_ingreso_actual = dict_temp_ingresos[(ingalm.at[ix, 'id_ingreso'], mes)]
                tempo_ingreso_siguiente = dict_temp_ingresos[(ingalm.at[ix, 'id_ingreso'], mes+1)]

                if tempo_ingreso_actual == 1 and tempo_ingreso_siguiente == 0:
                    almacen_ingreso = ingalm.at[ix, 'almacen_verano']
                    almacen_ingreso = dict_alm_acanche[almacen_ingreso]
                elif tempo_ingreso_actual == 1:
                    almacen_ingreso = ingalm.at[ix, 'almacen_verano']
                elif tempo_ingreso_actual == 0:
                    almacen_ingreso = ingalm.at[ix, 'almacen_invierno']
                else:
                    raise NotImplementedError('A4-1. Existe un caso no considerado en el ciclo')


                tabla_movimiento = agregar_movimiento(mes=mes,
                                                        origen=ingalm.at[ix, 'id_ingreso'],
                                                        destino=almacen_ingreso,
                                                        producto=producto,
                                                        antiguedad=0,
                                                        volumen=ingalm.at[ix, 'volumen'])



            print('Algo 8: Descontar entradas de plantas (por concepto de demanda)')
            tabla_movimiento = agregar_movimiento(mes=mes,
                                    origen=planta,
                                    destino='consumo_planta',
                                    producto=producto,
                                    antiguedad=0,
                                    volumen=dict_plantas_consumo[(mes, planta, producto)])


            print('Toques finales...')
            #Resumen entradas y salidas
            tabla_movimiento['antiguedad'] = tabla_movimiento['antiguedad'].astype(str) 
            tabla_movimiento_mes = tabla_movimiento[tabla_movimiento['mes'] == mes].copy()
            entradas_producto = tabla_movimiento_mes.groupby(['mes', 'destino', 'producto', 'antiguedad'], as_index=False).agg(entrada_volumen=('volumen','sum'))
            entradas_producto = entradas_producto.rename(columns={'destino':'id'})
            salidas_producto = tabla_movimiento_mes.groupby(['mes', 'origen', 'producto', 'antiguedad'], as_index=False).agg(salida_volumen=('volumen','sum'))
            salidas_producto = salidas_producto.rename(columns={'origen':'id'})

            #Creando matriz de balance
            balance_producto_mes = pd.DataFrame([[mes, producto]], columns=['mes', 'producto'])
            antiguedades = pd.DataFrame(range(0,14), columns=['antiguedad'])
            antiguedades['antiguedad'] = antiguedades['antiguedad'].astype(str)
            balance_producto_mes = pd.merge(balance_producto_mes, antiguedades, how='cross')
            balance_producto_mes['mes'] = balance_producto_mes['mes'].astype(np.int64)
            
            #Se agregan nodos activos
            balance_producto_mes = pd.merge(balance_producto_mes, nodos_activos, how='cross')
    
            balance_producto_mes = pd.merge(balance_producto_mes, tabla_stock_mes.rename(columns={'volumen':'stock_mes'}), how='left', on=['mes', 'id', 'tipo_id', 'producto', 'antiguedad'])
            balance_producto_mes['stock_mes'] = balance_producto_mes['stock_mes'].fillna(0)

            #Se agrega salidas y entradas de producto
            balance_producto_mes = pd.merge(balance_producto_mes, salidas_producto, how='left')
            balance_producto_mes['salida_volumen'] = balance_producto_mes['salida_volumen'].fillna(0)
            balance_producto_mes = pd.merge(balance_producto_mes, entradas_producto, how='left')
            balance_producto_mes['entrada_volumen'] = balance_producto_mes['entrada_volumen'].fillna(0)
            balance_producto_mes['stock_final'] = balance_producto_mes['stock_mes'] + balance_producto_mes['entrada_volumen'] - balance_producto_mes['salida_volumen']
            
            #Se agrega balance a tabla maestra
            balance_producto = pd.concat([balance_producto, balance_producto_mes], ignore_index=True)
            print(mes, planta, producto, len(balance_producto_mes), len(balance_producto_mes.drop_duplicates()))
            #Se genera tabla de stock incial para mes siguiente
            aux = balance_producto_mes.copy()
            aux = aux.drop(columns=['stock_mes', 'salida_volumen', 'entrada_volumen'])
            aux['antiguedad'] = aux['antiguedad'].astype(np.int64) + 1
            aux.loc[aux['antiguedad'] > 13, 'antiguedad'] = 13
            aux.loc[aux['tipo_id'] == 'planta', 'antiguedad'] = 0
            aux['antiguedad'] = aux['antiguedad'].astype(str)
            aux['mes'] = aux['mes'] + 1
            aux = aux.rename(columns={'stock_final':'volumen'})
            aux = aux.groupby(['mes', 'producto', 'antiguedad', 'id', 'tipo_id'], as_index=False).agg({'volumen':'sum'})
            aux = aux.loc[~((aux['tipo_id'] == 'planta') & (aux['id'] != planta))]  

            tabla_stock = pd.concat([tabla_stock, aux], ignore_index=True)



# %%
tabla_demanda_mod1 = tabla_demanda_mod1.rename(columns={'demanda_rango':'dr_mod1'})
demanda_mod1 = tabla_demanda_mod1.groupby(['mes_planificado', 'nombre_planta', 'producto'], as_index=False).agg(aux_mod1=('dr_mod1', 'sum'))
tabla_demanda_mod2 = tabla_demanda_mod2.rename(columns={'demanda_rango':'dr_mod2'})
demanda_mod2 = tabla_demanda_mod2.groupby(['mes_planificado', 'nombre_planta', 'producto'], as_index=False).agg(aux_mod2=('dr_mod2', 'sum'))

compilado_demanda = tabla_demanda_original.copy()
compilado_demanda = pd.merge(compilado_demanda , tabla_demanda_mod1, how='left')
compilado_demanda = pd.merge(compilado_demanda , tabla_demanda_mod2, how='left')
compilado_demanda = pd.merge(compilado_demanda , demanda_mod1, how='left')
compilado_demanda = pd.merge(compilado_demanda , demanda_mod2, how='left')

compilado_demanda.insert(loc=compilado_demanda.columns.get_loc('demanda')+1, column='dmod1', value=compilado_demanda['aux_mod1'])
compilado_demanda.insert(loc=compilado_demanda.columns.get_loc('demanda')+2, column='dmod2', value=compilado_demanda['aux_mod2']) 
compilado_demanda = compilado_demanda.drop(columns=['aux_mod1', 'aux_mod2'])

# %%
nombre_archivo = 'optic-' + str(datetime.datetime.now())[:17].replace('-','').replace(' ', '-').replace(':', '')
datetime.datetime.now()
writer = pd.ExcelWriter(nombre_archivo + '.xlsx')
compilado_demanda.to_excel(writer, sheet_name='tabla_demanda', index=False)
tabla_stock.to_excel(writer, sheet_name='tabla_stock', index=False)
balance_producto.to_excel(writer, sheet_name='tabla_balance', index=False)
tabla_movimiento.to_excel(writer, sheet_name='moviminetos', index=False)
writer.close()
