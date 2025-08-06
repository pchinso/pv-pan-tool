# Arquitectura de la Interfaz CLI - PV PAN Tool

## 🎯 **Objetivo**
Crear una interfaz de línea de comandos completa y fácil de usar para la herramienta PV PAN Tool que permita a los usuarios realizar todas las operaciones principales sin necesidad de conocimientos de programación.

## 🏗️ **Estructura de Comandos**

### **Comando Principal: `pv-pan-tool`**

```bash
pv-pan-tool [COMMAND] [OPTIONS]
```

### **1. Comandos de Parseo**

#### `parse` - Parsear archivos .PAN
```bash
# Parsear todos los archivos en el directorio por defecto
pv-pan-tool parse

# Parsear archivos de un directorio específico
pv-pan-tool parse --input-dir "C:\path\to\pan\files"

# Parsear solo archivos nuevos/modificados
pv-pan-tool parse --new-only

# Parsear con límite de archivos (para testing)
pv-pan-tool parse --max-files 10

# Parsear y mostrar progreso detallado
pv-pan-tool parse --verbose

# Forzar re-parseo de todos los archivos
pv-pan-tool parse --force
```

### **2. Comandos de Consulta**

#### `search` - Buscar módulos
```bash
# Buscar por fabricante
pv-pan-tool search --manufacturer "Jinko"

# Buscar por modelo
pv-pan-tool search --model "JKM590N"

# Buscar por rango de potencia
pv-pan-tool search --power-min 500 --power-max 600

# Buscar por eficiencia mínima
pv-pan-tool search --efficiency-min 22.0

# Búsqueda combinada
pv-pan-tool search --manufacturer "Longi" --power-min 550 --efficiency-min 21.5
```

#### `list` - Listar elementos
```bash
# Listar todos los fabricantes
pv-pan-tool list manufacturers

# Listar modelos de un fabricante
pv-pan-tool list models --manufacturer "Jinko"

# Listar todos los módulos (con paginación)
pv-pan-tool list modules --page 1 --per-page 20

# Listar módulos con filtros
pv-pan-tool list modules --power-min 500 --sort-by power
```

### **3. Comandos de Comparación**

#### `compare` - Comparar módulos
```bash
# Comparar módulos específicos por ID
pv-pan-tool compare --ids 1,2,3

# Comparar módulos por criterios
pv-pan-tool compare --manufacturer "Jinko,Longi" --power-min 550

# Comparar top N módulos por potencia
pv-pan-tool compare --top-power 5

# Comparar top N módulos por eficiencia
pv-pan-tool compare --top-efficiency 5

# Comparar con formato de salida específico
pv-pan-tool compare --ids 1,2,3 --format table
pv-pan-tool compare --ids 1,2,3 --format json
```

### **4. Comandos de Estadísticas**

#### `stats` - Mostrar estadísticas
```bash
# Estadísticas generales
pv-pan-tool stats

# Estadísticas por fabricante
pv-pan-tool stats --by-manufacturer

# Estadísticas por tipo de celda
pv-pan-tool stats --by-cell-type

# Estadísticas de rangos de potencia
pv-pan-tool stats --power-ranges
```

### **5. Comandos de Exportación**

#### `export` - Exportar datos
```bash
# Exportar todos los módulos a CSV
pv-pan-tool export --format csv --output modules.csv

# Exportar con filtros
pv-pan-tool export --format csv --manufacturer "Jinko" --output jinko_modules.csv

# Exportar comparación específica
pv-pan-tool export --format csv --ids 1,2,3 --output comparison.csv

# Exportar a Excel
pv-pan-tool export --format xlsx --output modules.xlsx

# Exportar a JSON
pv-pan-tool export --format json --output modules.json
```

### **6. Comandos de Gestión**

#### `database` - Gestión de base de datos
```bash
# Mostrar información de la base de datos
pv-pan-tool database info

# Limpiar base de datos
pv-pan-tool database clear --confirm

# Respaldar base de datos
pv-pan-tool database backup --output backup.db

# Restaurar base de datos
pv-pan-tool database restore --input backup.db
```

#### `config` - Configuración
```bash
# Mostrar configuración actual
pv-pan-tool config show

# Establecer directorio por defecto de archivos .PAN
pv-pan-tool config set pan-directory "C:\path\to\pan\files"

# Establecer directorio de base de datos
pv-pan-tool config set database-path "C:\path\to\database"
```

## 🎨 **Características de la Interfaz**

### **1. Salida Rica y Colorida**
- Uso de la librería `rich` para tablas, progress bars y colores
- Formato de tablas profesional para comparaciones
- Progress bars para operaciones largas (parseo)
- Colores para destacar información importante

### **2. Validación de Entrada**
- Validación de rutas de archivos y directorios
- Validación de rangos numéricos
- Mensajes de error claros y útiles
- Sugerencias de comandos similares

### **3. Configuración Flexible**
- Archivo de configuración JSON para settings por defecto
- Variables de entorno para paths importantes
- Configuración por usuario y por proyecto

### **4. Ayuda Contextual**
- Help detallado para cada comando
- Ejemplos de uso en la ayuda
- Autocompletado de comandos (bash/zsh)

## 📁 **Estructura de Archivos CLI**

```
src/pv_pan_tool/
├── cli/
│   ├── __init__.py
│   ├── main.py          # Punto de entrada principal
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── parse.py     # Comandos de parseo
│   │   ├── search.py    # Comandos de búsqueda
│   │   ├── compare.py   # Comandos de comparación
│   │   ├── export.py    # Comandos de exportación
│   │   ├── stats.py     # Comandos de estadísticas
│   │   └── database.py  # Comandos de gestión DB
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py    # Gestión de configuración
│   │   ├── formatters.py # Formateo de salida
│   │   ├── validators.py # Validación de entrada
│   │   └── helpers.py   # Funciones auxiliares
│   └── config/
│       └── default.json # Configuración por defecto
```

## 🔧 **Tecnologías y Librerías**

### **Core CLI**
- **Click**: Framework principal para CLI
- **Rich**: Salida rica con colores y tablas
- **Typer**: Alternativa moderna a Click (opcional)

### **Configuración**
- **JSON**: Archivos de configuración
- **os.environ**: Variables de entorno
- **pathlib**: Manejo de rutas

### **Validación**
- **Pydantic**: Validación de datos de entrada
- **Click validators**: Validación de parámetros CLI

## 🚀 **Flujo de Trabajo Típico**

### **1. Primera vez (Setup)**
```bash
# Configurar directorio de archivos .PAN
pv-pan-tool config set pan-directory "C:\Users\user\OneDrive\PAN_catalog\01. Modulos"

# Parsear todos los archivos
pv-pan-tool parse --verbose

# Ver estadísticas
pv-pan-tool stats
```

### **2. Uso diario**
```bash
# Parsear solo archivos nuevos
pv-pan-tool parse --new-only

# Buscar módulos específicos
pv-pan-tool search --manufacturer "Jinko" --power-min 550

# Comparar módulos encontrados
pv-pan-tool compare --top-power 5

# Exportar resultados
pv-pan-tool export --format csv --power-min 550 --output high_power_modules.csv
```

### **3. Análisis avanzado**
```bash
# Estadísticas por fabricante
pv-pan-tool stats --by-manufacturer

# Comparación detallada
pv-pan-tool compare --manufacturer "Jinko,Longi,Trina" --format table

# Exportar análisis completo
pv-pan-tool export --format xlsx --output complete_analysis.xlsx
```

## 📋 **Prioridades de Implementación**

### **Fase 1 - Comandos Básicos**
1. `parse` - Parseo básico de archivos
2. `search` - Búsqueda simple
3. `list` - Listado de elementos
4. `stats` - Estadísticas básicas

### **Fase 2 - Funcionalidades Avanzadas**
1. `compare` - Comparación de módulos
2. `export` - Exportación a diferentes formatos
3. `config` - Gestión de configuración

### **Fase 3 - Gestión y Optimización**
1. `database` - Gestión de base de datos
2. Optimización de rendimiento
3. Autocompletado y mejoras UX

## 🎯 **Objetivos de Usabilidad**

1. **Simplicidad**: Comandos intuitivos y fáciles de recordar
2. **Flexibilidad**: Múltiples formas de lograr el mismo resultado
3. **Feedback**: Información clara sobre el progreso y resultados
4. **Robustez**: Manejo elegante de errores y casos edge
5. **Documentación**: Help contextual y ejemplos claros

