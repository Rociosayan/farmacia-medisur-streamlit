# Farmacia MediSur · demo Streamlit

Aplicación web de demostración basada en los notebooks de consola y Gradio de Farmacia MediSur. Reproduce los flujos principales con **datos inventados** y una base SQLite **en memoria por sesión**. Ningún dato se escribe en el servidor; se restablece al reiniciar la sesión.

## Inicio local

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Funciones

- Clientes: consulta, alta, edición, baja, búsqueda y exportación según rol.
- Ventas: catálogo, operación, detalle, pago y ticket en una transacción.
- Reportes de ventas por categoría.
- Diccionario de datos, reglas de calidad, matriz de permisos y bitácora.
- KPIs de calidad y plan de mejora de demostración.

Los roles seleccionables son parte de una **simulación didáctica**. No son autenticación. No introducir información real. Los datos del paquete SQLite original y los CSV no se incluyen en este repositorio.

## Fuentes

Los notebooks originales de Python/SQLite y Gradio, el esquema y el diccionario del caso se conservaron en las carpetas de origen de la propietaria. Esta versión usa Streamlit para hacer visible la aplicación en la web. El caso completo requiere autenticación y persistencia segura antes de usarse en un negocio real.
