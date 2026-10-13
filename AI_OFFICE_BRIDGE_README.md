# AI Office Bridge

Interfaz grafica para automatizar el trabajo administrativo del abasto
con panaderia. Extrae datos de facturas con OCR, valida la informacion,
genera comprobantes de retencion, actualiza el libro de compras y
opcionalmente envia el comprobante por email.

## Caracteristicas principales

- **OCR con MiniMax Vision**: Extrae N factura, RIF, fechas, montos, items
- **Catalogo de proveedores**: 362 proveedores pre-cargados con autocompletar
- **Form validado**: Validacion en tiempo real, validaciones cruzadas (sub+IVA=total)
- **Generacion de comprobantes**: IVA e ISLR basados en templates reales del usuario
- **Email automatico**: SMTP con plantillas HTML y adjuntos
- **Catalogo interactivo**: Al seleccionar proveedor, autollena RIF, direccion, email
- **Watchdog GUI**: Auto-restart cada 3 minutos para evitar hooks rotos
- **Compatible con hardware antiguo**: Sandy Bridge 2011+, 4GB RAM

## Quick start

1. Doble-click en **"AI Office Bridge"** del escritorio
2. Click **"Configuracion"** para configurar email (opcional)
3. Click **"Abrir archivo"** y selecciona tu libro de compras (.xlsx)
4. Click **"Cargar Factura (OCR)"** y selecciona el PDF o imagen
5. MiniMax Vision extrae los datos automaticamente
6. **Verifica** los datos en el formulario (busca el proveedor en el catalogo)
7. Click **"Guardar + Comprobante + Email"**
8. Listo! Comprobante generado, libro actualizado, email enviado

## Requisitos

- Windows 10 o superior
- Python 3.10+ (incluido en el bundle, no requiere instalacion)
- API key de MiniMax (configurada en `~/.dictation_config.json`)
- Microfono (opcional, para dictado con Dicto)
- Conexion a internet (para OCR, email y catalogos)

## Estructura

```
voz-a-texto/
├── voice_dictation.py       # Dicto (dictado por voz)
├── overlay.py                # Overlay visual
├── configurador.py           # Panel de configuracion
├── watchdog_dictation.bat    # Auto-restart
├── gridcraft_ai.py           # CLI bridge (existente)
│
├── ai_office_bridge_gui.py  # GUI principal
├── ocr_engine.py             # MiniMax Vision + tesseract fallback
├── comprobante_generator.py  # Genera comprobantes y actualiza libro
├── catalogo_proveedores.py   # Carga el catalogo
├── email_sender.py           # SMTP para comprobantes
│
├── proveedores_catalogo.json # 362 proveedores
├── templates/                # (PRIVADO - archivos del usuario, no en repo)
│
├── python/                    # Python embebido con todas las deps
├── start_dictation_silent.vbs
├── start_vosk_silent.vbs
├── abrir_bridge_gui.bat      # Launcher principal
├── launcher.bat               # Usado por el acceso directo
└── watchdog_dictation.bat
```

## Configuracion

### API key MiniMax

Ya debe estar en `~/.dictation_config.json`:
```json
{
  "minimax_api_key": "sk-cp-..."
}
```

Si no esta, configura Dicto primero (o edita el archivo manualmente).

### Email SMTP (opcional)

En la GUI, click **"Configuracion"** → llenar:
- SMTP Server (ej: smtp.gmail.com)
- Puerto (ej: 587)
- Usuario (tu email)
- Password (app password, NO tu contrasena normal)
- CC (opcional)

Para Gmail, usa [App Passwords](https://support.google.com/accounts/answer/185833).

## Templates del usuario

**IMPORTANTE**: Los templates son archivos personales del usuario. NO se incluyen en el repo.

Coloca tus templates en `voz-a-texto/templates/`:
- `COMPROBANTE DE RETENCION IVA...xlsx` (comprobante IVA)
- `COMPROBANTE DE RETENCIONES DE ISLR...xlsx` (comprobante ISLR)
- `RESUMEN LIBRO DE COMPRAS...xlsx` (libro de compras)

Los templates se usan como base para crear los nuevos comprobantes.

## Catalogo de proveedores

El catalogo se extrae automaticamente de `PROVEEDORES 2021+.xlsx` (o similar).

Para regenerarlo:
```python
python extraer_proveedores.py
```

## Tips para OCR

- Imagenes **menores a 5MB** son ideales
- Resolucion: **1200x1600 px** es suficiente
- Formato: **JPG** (mejor que PNG para fotos)
- Si la factura es PDF con texto, **mejor usar el PDF** (mas rapido)
- Si la imagen es > 20MB, **rechazara con error claro** (no se cuelga)

## Tests

```bash
# Test de logica
python test_logica.py

# Test E2E
python test_e2e_completo.py

# Test de OCR con imagen sintetica
python test_ocr_simple.py
```

## Limitaciones conocidas

- Solo Windows (no Mac/Linux)
- Requiere internet para OCR y email (no offline)
- El catalogo de proveedores no tiene emails (la mayoria)
- El mapeo de celdas del template se hace en el codigo (no auto-detectado)
- 1 minuto de OCR maximo (timeout 30s + extraccion)

## Licencia

MIT - Ver LICENSE
