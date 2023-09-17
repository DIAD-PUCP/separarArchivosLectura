import pandas as pd
import streamlit as st
from io import BytesIO
from zipfile import ZipFile

@st.cache_data
def read_ans_file(path,idlen=5,start=5,rsplen=76):
    df = pd.read_fwf(
        path,
        header=None,
        dtype=str,
        encoding='iso-8859-1'
    )
    df.columns = ['line']
    df['EXAMEN'] = df['line'].str[:idlen]
    maxline = df['line'].str.len().max()
    end = min(start+rsplen,maxline)
    df['RSP'] = df['line'].str[start:end]
    return df.set_index('EXAMEN')

@st.cache_data
def read_datos(path):
    df = pd.read_csv(
        path,
        dtype=str,
        encoding='iso-8859-1'
    ).fillna("")
    st.write(df)
    df = df.applymap(lambda x: x[2:-1] if x.startswith('="') and x.endswith('"') else x)
    versiones = {
        'ESTUDIOS GENERALES CIENCIAS': 'CIENCIAS',
        'ESTUDIOS GENERALES LETRAS': 'LETRAS',
        'ARQUITECTURA Y URBANISMO': 'ARQUITECTURA',
        'EDUCACION' : 'EDUCACION',
        'ARTE Y DISEÑO': 'LETRAS',
        'ARTES ESCÉNICAS': 'LETRAS',
        'GASTRONOMÍA; HOTELERÍA Y TURISMO': 'LETRAS',
    }
    df['VERSIÓN'] = df['UNIDAD'].apply(lambda x: versiones[x] if x in versiones else 'LETRAS')
    return df

@st.cache_data
def split(df,datos,campoID,campoSep,rsplen):
    grouped = df.join(datos.set_index(campoID)[campoSep]).groupby(campoSep)
    tempZip = BytesIO()
    with ZipFile(tempZip,'w') as zf:
        for name,group in grouped:
            with zf.open(f'{name}.txt','w') as buffer:
                group.reset_index()[['EXAMEN','RSP']].apply(
                    lambda x: ''.join(x) + " " *(rsplen - len(x['RSP'])) ,axis=1
                ).to_csv(
                    buffer,
                    index=False,
                    header=False,
                    lineterminator='\r\n'
                )
    return tempZip

def main():
    st.title('Separar archivos de Lectura')
    with st.sidebar:
        archivo = st.file_uploader('Archivo de lectura',help='El archivo de escaneo que se separará')
        idlen = st.number_input('Longitud del ID',help='Cuantos caracteres tiene el ID en el archivo',value=5,format='%d',min_value=1)
        idlen = int(idlen)
        start = st.number_input('Caracter de inicio de las respuestas',help='A partir de que caracter en el archivo empiezan las respuestas el primer caracter es 0',value=5,format='%d',min_value=1)
        rsplen = st.number_input('Cantidad máx de respuestas',help='Cuantos caracteres tiene como máximo las respuestas, los excesos se descartan',value=76,format='%d',min_value=1)
        datos = st.file_uploader('Archivo de datos',help='El archivo que contiene los datos')
        
    if archivo and datos:
        df = read_ans_file(archivo,idlen=idlen,start=start,rsplen=rsplen)
        dat = read_datos(datos)
        campoID = st.selectbox("ID",options=dat.columns,)
        campoSep = st.selectbox("Grupo",options=dat.columns)
        if campoID != campoSep:
            groups = dat[campoSep].unique()
            if groups.shape[0] != dat.shape[0]:
                st.write(groups)
                tempZip = split(df,dat,campoID,campoSep,rsplen)
                st.download_button("Descargar archivos",data=tempZip.getvalue(),file_name='Respuestas.zip',mime="application/zip")
                tempZip.close()
            
if __name__ == '__main__':
    main()