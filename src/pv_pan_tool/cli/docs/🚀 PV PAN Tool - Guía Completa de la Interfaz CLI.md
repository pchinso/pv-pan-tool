# 🚀 PV PAN Tool - Guía Completa de la Interfaz CLI

## 📋 **Resumen**

La interfaz CLI (Command Line Interface) de PV PAN Tool está completamente implementada y funcional. Proporciona acceso completo a todas las funcionalidades de la herramienta desde la línea de comandos, incluyendo parseo de archivos .PAN, consultas de base de datos, comparaciones de módulos y exportación de datos.

## ✅ **Estado de Implementación**

### **🎯 Completado al 100%**
- ✅ **Arquitectura CLI completa** - Estructura modular y extensible
- ✅ **7 comandos principales** - parse, search, compare, stats, export, database, info
- ✅ **Configuración flexible** - Archivos JSON y variables de entorno
- ✅ **Salida rica y colorida** - Tablas, progress bars, paneles informativos
- ✅ **Validación robusta** - Parámetros, archivos, y datos de entrada
- ✅ **Manejo de errores** - Mensajes claros y recuperación elegante
- ✅ **Ayuda contextual** - Help detallado para cada comando
- ✅ **Tests completos** - Validación de funcionalidad

## 🏗️ **Estructura del Proyecto**

```
src/pv_pan_tool/
├── cli.py                    # Punto de entrada principal
├── cli/
│   ├── main.py              # CLI principal con grupo de comandos
│   ├── commands/            # Comandos individuales
│   │   ├── parse.py         # Parseo de archivos .PAN
│   │   ├── search.py        # Búsqueda en base de datos
│   │   ├── compare.py       # Comparación de módulos
│   │   ├── stats.py         # Estadísticas y análisis
│   │   ├── export.py        # Exportación de datos
│   │   └── database.py      # Gestión de base de datos
│   ├── utils/               # Utilidades
│   │   ├── config.py        # Gestión de configuración
│   │   └── formatters.py    # Formateo de salida
│   └── config/
│       └── default.json     # Configuración por defecto
├── models.py                # Modelos de datos Pydantic
├── parser.py                # Parser de archivos .PAN
└── database.py              # Gestión de base de datos SQLite
```

## 🚀 **Instalación y Configuración**

### **1. Instalar dependencias**
```bash
pip install rich click pydantic pandas sqlalchemy
```

### **2. Configurar directorio de archivos .PAN**
```bash
python -m src.pv_pan_tool.cli.main config set pan_directory "C:\Users\slpcs.ABG\OneDrive - Cox\PAN_catalog\01. Modulos"
```

### **3. Verificar instalación**
```bash
python -m src.pv_pan_tool.cli.main --help
```

## 📖 **Comandos Disponibles**

### **🔍 Comando Principal**
```bash
python -m src.pv_pan_tool.cli.main [COMMAND] [OPTIONS]
```

### **1. `parse` - Parsear archivos .PAN**
```bash
# Parsear todos los archivos del directorio configurado
python -m src.pv_pan_tool.cli.main parse

# Parsear archivos de un directorio específico
python -m src.pv_pan_tool.cli.main parse --input-dir "C:\path\to\pan\files"

# Parsear solo archivos nuevos/modificados
python -m src.pv_pan_tool.cli.main parse --new-only

# Parsear con límite para testing
python -m src.pv_pan_tool.cli.main parse --max-files 10 --verbose

# Dry run (mostrar qué se procesaría)
python -m src.pv_pan_tool.cli.main parse --dry-run

# Forzar re-parseo de todos los archivos
python -m src.pv_pan_tool.cli.main parse --force
```

### **2. `search` - Buscar módulos**
```bash
# Buscar por fabricante
python -m src.pv_pan_tool.cli.main search --manufacturer "Jinko"

# Buscar por rango de potencia
python -m src.pv_pan_tool.cli.main search --power-min 500 --power-max 600

# Buscar por eficiencia mínima
python -m src.pv_pan_tool.cli.main search --efficiency-min 22.0

# Búsqueda combinada con ordenamiento
python -m src.pv_pan_tool.cli.main search --manufacturer "Longi" --power-min 550 --sort-by efficiency_stc

# Guardar resultados en archivo
python -m src.pv_pan_tool.cli.main search --power-min 500 --output results.csv

# Formato JSON
python -m src.pv_pan_tool.cli.main search --manufacturer "Jinko" --format json
```

### **3. `compare` - Comparar módulos**
```bash
# Comparar módulos específicos por ID
python -m src.pv_pan_tool.cli.main compare --ids 1,2,3

# Comparar top 5 por potencia
python -m src.pv_pan_tool.cli.main compare --top-power 5

# Comparar top 3 por eficiencia
python -m src.pv_pan_tool.cli.main compare --top-efficiency 3

# Comparar por fabricantes
python -m src.pv_pan_tool.cli.main compare --manufacturer "Jinko,Longi" --limit 3

# Comparar por rangos
python -m src.pv_pan_tool.cli.main compare --power-range 500-600 --efficiency-range 21-23

# Exportar comparación
python -m src.pv_pan_tool.cli.main compare --top-power 5 --format json --output comparison.json
```

### **4. `stats` - Estadísticas**
```bash
# Estadísticas generales
python -m src.pv_pan_tool.cli.main stats

# Estadísticas por fabricante
python -m src.pv_pan_tool.cli.main stats --by-manufacturer

# Estadísticas por tipo de celda
python -m src.pv_pan_tool.cli.main stats --by-cell-type

# Distribución de rangos de potencia
python -m src.pv_pan_tool.cli.main stats --power-ranges

# Top 5 fabricantes
python -m src.pv_pan_tool.cli.main stats --top-manufacturers 5

# Exportar estadísticas
python -m src.pv_pan_tool.cli.main stats --format json --output stats.json
```

### **5. `export` - Exportar datos**
```bash
# Exportar todos los módulos a CSV
python -m src.pv_pan_tool.cli.main export --format csv --output modules.csv

# Exportar con filtros
python -m src.pv_pan_tool.cli.main export --format xlsx --manufacturer "Jinko" --output jinko.xlsx

# Exportar módulos de alta potencia
python -m src.pv_pan_tool.cli.main export --format json --power-min 550 --output high_power.json

# Incluir metadatos y datos raw
python -m src.pv_pan_tool.cli.main export --format csv --include-metadata --include-raw --output complete.csv

# Exportar con ordenamiento
python -m src.pv_pan_tool.cli.main export --format csv --sort-by efficiency_stc --sort-order desc --output sorted.csv
```

### **6. `database` - Gestión de base de datos**
```bash
# Información de la base de datos
python -m src.pv_pan_tool.cli.main database info

# Crear backup
python -m src.pv_pan_tool.cli.main database backup --output backup.db

# Crear backup comprimido
python -m src.pv_pan_tool.cli.main database backup --compress

# Restaurar desde backup
python -m src.pv_pan_tool.cli.main database restore --input backup.db

# Limpiar base de datos
python -m src.pv_pan_tool.cli.main database clear --confirm

# Optimizar base de datos
python -m src.pv_pan_tool.cli.main database optimize

# Verificar integridad
python -m src.pv_pan_tool.cli.main database check
```

### **7. `info` - Información del sistema**
```bash
# Información general del sistema
python -m src.pv_pan_tool.cli.main info

# Información detallada (verbose)
python -m src.pv_pan_tool.cli.main info --verbose
```

## ⚙️ **Configuración**

### **Archivo de configuración por defecto**
Ubicación: `src/pv_pan_tool/cli/config/default.json`

```json
{
    "pan_directory": "C:\\Users\\slpcs.ABG\\OneDrive - Cox\\PAN_catalog\\01. Modulos",
    "database_path": "data/database/pv_modules.db",
    "output_directory": "output",
    "max_files_per_batch": 100,
    "default_export_format": "csv",
    "verbose_output": false,
    "auto_backup": true,
    "backup_directory": "backups"
}
```

### **Variables de entorno**
```bash
# Configurar via variables de entorno (prefijo PV_PAN_TOOL_)
export PV_PAN_TOOL_PAN_DIRECTORY="C:\path\to\pan\files"
export PV_PAN_TOOL_DATABASE_PATH="custom/database/path.db"
export PV_PAN_TOOL_VERBOSE_OUTPUT="true"
```

### **Configuración de usuario**
```bash
# Configuración se guarda en: ~/.config/pv-pan-tool/config.json
python -m src.pv_pan_tool.cli.main config set pan_directory "C:\new\path"
python -m src.pv_pan_tool.cli.main config set database_path "custom.db"
python -m src.pv_pan_tool.cli.main config show
```

## 🎨 **Características de la Interfaz**

### **✨ Salida Rica y Colorida**
- **Tablas profesionales** con Rich para comparaciones y listados
- **Progress bars** para operaciones largas (parseo, exportación)
- **Paneles informativos** para resultados y estadísticas
- **Colores** para destacar información importante (errores, éxitos, advertencias)

### **🔍 Validación Robusta**
- **Validación de archivos** y directorios de entrada
- **Validación de parámetros** numéricos y rangos
- **Mensajes de error claros** con sugerencias de corrección
- **Confirmaciones** para operaciones destructivas

### **📊 Formatos de Salida**
- **Tabla** - Formato visual para terminal
- **JSON** - Para integración con otras herramientas
- **CSV** - Para análisis en Excel/hojas de cálculo
- **Excel** - Con múltiples hojas y formato profesional

## 🔄 **Flujo de Trabajo Típico**

### **1. Primera configuración**
```bash
# 1. Configurar directorio de archivos .PAN
python -m src.pv_pan_tool.cli.main config set pan_directory "C:\Users\slpcs.ABG\OneDrive - Cox\PAN_catalog\01. Modulos"

# 2. Parsear todos los archivos (primera vez)
python -m src.pv_pan_tool.cli.main parse --verbose

# 3. Ver estadísticas generales
python -m src.pv_pan_tool.cli.main stats
```

### **2. Uso diario**
```bash
# 1. Parsear solo archivos nuevos
python -m src.pv_pan_tool.cli.main parse --new-only

# 2. Buscar módulos específicos
python -m src.pv_pan_tool.cli.main search --manufacturer "Jinko" --power-min 550

# 3. Comparar módulos encontrados
python -m src.pv_pan_tool.cli.main compare --top-power 5

# 4. Exportar resultados
python -m src.pv_pan_tool.cli.main export --format csv --power-min 550 --output high_power.csv
```

### **3. Análisis avanzado**
```bash
# 1. Estadísticas por fabricante
python -m src.pv_pan_tool.cli.main stats --by-manufacturer --top-manufacturers 10

# 2. Comparación detallada por tecnología
python -m src.pv_pan_tool.cli.main compare --cell-type monocrystalline --top-efficiency 5

# 3. Exportar análisis completo
python -m src.pv_pan_tool.cli.main export --format xlsx --include-metadata --output analysis.xlsx
```

## 🛠️ **Mantenimiento**

### **Backup y restauración**
```bash
# Backup automático con timestamp
python -m src.pv_pan_tool.cli.main database backup --compress

# Restaurar desde backup específico
python -m src.pv_pan_tool.cli.main database restore --input backups/backup_20250106.db.gz
```

### **Optimización**
```bash
# Optimizar rendimiento de la base de datos
python -m src.pv_pan_tool.cli.main database optimize

# Verificar integridad
python -m src.pv_pan_tool.cli.main database check --verbose
```

## 🚨 **Solución de Problemas**

### **Problemas comunes**

1. **"No module named 'rich'"**
   ```bash
   pip install rich click pydantic
   ```

2. **"Database file does not exist"**
   ```bash
   # Verificar configuración
   python -m src.pv_pan_tool.cli.main info
   
   # Parsear archivos para crear DB
   python -m src.pv_pan_tool.cli.main parse
   ```

3. **"No .PAN files found"**
   ```bash
   # Verificar directorio configurado
   python -m src.pv_pan_tool.cli.main config show
   
   # Configurar directorio correcto
   python -m src.pv_pan_tool.cli.main config set pan_directory "C:\correct\path"
   ```

### **Modo verbose**
Para debugging detallado, usar `--verbose` en cualquier comando:
```bash
python -m src.pv_pan_tool.cli.main parse --verbose
python -m src.pv_pan_tool.cli.main search --manufacturer "Jinko" --verbose
```

## 🎯 **Próximos Pasos Recomendados**

### **1. Instalación como paquete**
```bash
# Instalar en modo desarrollo
pip install -e .

# Después podrás usar directamente:
pv-pan-tool --help
pv-pan-tool parse
pv-pan-tool search --manufacturer "Jinko"
```

### **2. Procesamiento completo**
```bash
# Procesar todos los 1,163 archivos .PAN
python -m src.pv_pan_tool.cli.main parse --verbose

# Generar estadísticas completas
python -m src.pv_pan_tool.cli.main stats --by-manufacturer --power-ranges --efficiency-ranges
```

### **3. Automatización**
```bash
# Script para actualización diaria
#!/bin/bash
python -m src.pv_pan_tool.cli.main parse --new-only
python -m src.pv_pan_tool.cli.main database backup
python -m src.pv_pan_tool.cli.main stats > daily_stats.txt
```

## 📞 **Soporte**

Para obtener ayuda con cualquier comando:
```bash
python -m src.pv_pan_tool.cli.main --help
python -m src.pv_pan_tool.cli.main [COMMAND] --help
```

La CLI está completamente implementada y lista para uso en producción. Todas las funcionalidades están probadas y validadas.

---

**🎉 ¡La interfaz CLI de PV PAN Tool está completa y lista para usar!**

