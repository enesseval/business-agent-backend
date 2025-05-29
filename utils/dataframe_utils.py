import pandas as pd

def analyze_dataframe(df: pd.DataFrame):
    result = {}

    result['satir_sayisi'] = len(df)
    result['sutun_sayisi'] = len(df.columns)

    dtypes = df.dtypes
    result['veri_tipleri'] = [
        {
            "name":"Sayisal",
            "count":sum(dtypes.apply(lambda x: pd.api.types.is_numeric_dtype(x)))
         
         },
         {
            "name":"Kategorik",
            "count":sum(dtypes.apply(lambda x: pd.api.types.is_categorical_dtype(x) or pd.api.types.is_object_dtype(x)))
         
         },
         {
            "name":"Tarih",
            "count":sum(dtypes.apply(lambda x: pd.api.types.is_datetime64_any_dtype(x)))
         
         },
         {
            "name":"Metin",
            "count":sum(dtypes.apply(lambda x: x == 'string'))
         
         }
    ]

    result['eksik_degerler'] = int(df.isnull().sum().sum())
    result['yinelenen_satirlar'] = int(df.duplicated().sum())

    total_cells = df.shape[0] * df.shape[1]
    non_null_cells = df.count().sum()
    result['tamlik'] = round(non_null_cells / total_cells * 100, 2)

    eksik_orani = result['eksik_degerler'] / total_cells
    yinelenen_orani = result['yinelenen_satirlar'] / df.shape[0]
    result['kalite_puani'] = round((1 - (eksik_orani + yinelenen_orani)) * 100, 2)

    return result
