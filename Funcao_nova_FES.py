from __future__ import annotations
import os
import pathlib
import numpy
import pyfes
import netCDF4 as nc
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

#Função para prever a maré astronômica a partir do FES
def FES(lat, lon, data_inicial, data_final):

    """
    Calcula a previsão de maré astronômica para uma localização e data específicas usando o algoritmo do FES

    Args:
        lat (float): latitude do ponto de interesse
        lon (float): longitude do ponto de interesse
        data_inicial (string): data de início da previsão no formato 'YYYY-MM-DD'
        datat_final (string): data final da previsão no formato 'YYYY-MM-DD'

    Returns:
        pandas.Dataframe: DataFrame contendo a previsão para o local e período selecionados.
    """

    os.environ['DATASET_DIR'] = str(Path("/home/rafael/Downloads"))
    #os.environ['DATASET_DIR'] = str(pathlib.Path().absolute().parent / 'tests' / 'python' / 'dataset')

    # Create a Path object
    #os.environ['DATASET_DIR']  = Path("/home/rafael/Downloads")
    handlers = pyfes.load_config(pathlib.Path().absolute() / 'FES2022'/'constantes.yaml')

    #Cada variável recebendo seu valor, sendo "x" o número de dias entre as datas inicial e final
    data_inicial = pd.to_datetime(data_inicial) 
    data_final = pd.to_datetime(data_final) 
    x=(data_final - data_inicial).days
    data_inicial.replace(hour=0, minute=0, second=0)

    #Algoritmo do FES com algumas adaptações
    date = numpy.datetime64(data_inicial, 's')

    dates = numpy.arange(date, date + numpy.timedelta64(x, 'D'),
                        numpy.timedelta64(1, 'h'))
    lons = numpy.full(dates.shape, lon)
    lats = numpy.full(dates.shape, lat)

    tide, lp, _ = pyfes.evaluate_tide(handlers['tide'],
                                    dates,
                                    lons,
                                    lats,
                                    num_threads=1)
    load, load_lp, _ = pyfes.evaluate_tide(handlers['radial'],
                                        dates,
                                        lons,
                                        lats,
                                        num_threads=1)
    cnes_julian_days = (dates - numpy.datetime64('1950-01-01T00:00:00')
                    ).astype('M8[s]').astype(float) / 86400
    hours = cnes_julian_days % 1 * 24
    
    #Criação do dataframe com o resultado do FES
    df = pd.DataFrame({
    'JulDay': cnes_julian_days,
    'Hour': hours,
    'Latitude': lats,
    'Longitude': lons,
    'Short_tide': tide,
    'LP_tide': lp,
    'Pure_Tide': tide + lp,
    'Geo_Tide': tide + lp + load,
    'Rad_Tide': load
})

    #Três casas decimais é o suficiente (depois os dias julianos serão tranformados em inteiros)
    df.iloc[:, 1:] = df.iloc[:, 1:].round(3)

    #Calculando a data no formato "YYYY-MM-DD" a partir dos dias julianos através da função "julian to date"
    #O marco inicial é 1 de Janeiro de 1950, data guardada em "julian_start". Então, "dia_juliano" recebe um número que representa quantos dias passaram
    #desde o marco inicial, daí "timedelta(days=dia_juliano)" cria um intervalo de tempo correspondente a esse número de dias e ao somar com "julian_start",
    #o resultado é a data.
    julian_start = datetime(1950, 1, 1)
    def julian_to_date(dia_juliano):

        """
        Transforma o dia juliano na data correspoondente no formato "YYYY-MM-DD"

        Args:
            dia_juliano (float): Número de dias desde 1 de Janeiro de 1950

        Returns:
            datetime: Objeto datemtime correspondente à data convertida
        """
        return julian_start + timedelta(days=dia_juliano)

    #Aplicação da função julian_to_date 
    df['Datas'] = df['JulDay'].apply(julian_to_date)
    #Passando o dia juliano para int (não é necessário dia juliano com casas decimais)
    df["JulDay"] = df["JulDay"].astype(int) 
    #Centralizando os valores da tabela
    pd.set_option('display.colheader_justify', 'center')

    #Colocando as colunas em ordem 
    df = df[['JulDay', 'Datas', 'Latitude', 'Longitude', 'Short_tide',
            'LP_tide', 'Pure_Tide', 'Geo_Tide', 'Rad_Tide']]
    #Aqui deixaria as datas indexadas
    #df.set_index('Datas', inplace=True)

    return df

#Chamando a função com os parâmetros desejados
resultado= FES(59.195, -7.688, '1983-01-01', '1983-01-02')
print(resultado)
