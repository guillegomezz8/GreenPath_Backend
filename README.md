# 🌿 GreenPath — Plataforma de Gestión de Recogida de Aceites Usados

## 📘 Descripción General

**GreenPath** es una aplicación web desarrollada como Trabajo Fin de Grado, pensada para ayudar a las empresas dedicadas a la **recogida de aceites usados** a organizar su trabajo diario.  
Permite gestionar clientes, trabajadores y camiones, así como planificar rutas y analizar el rendimiento de la empresa.

El sistema está diseñado para que **cada empresa disponga de su propio entorno de trabajo**:  
- El **propietario** puede administrar su empresa, empleados y clientes.  
- Los **trabajadores** accederán a sus rutas y tareas asignadas (fase futura).  
- Los **clientes** podrán solicitar recogidas y consultar su histórico (fase futura).

Actualmente, la aplicación está centrada en la **fase de propietarios**, que constituye la base funcional del sistema.

---

## 🎯 Objetivos de la Fase Actual

- Gestionar de forma centralizada la información de clientes, trabajadores y camiones.  
- Optimizar la planificación de rutas y recogidas.  
- Registrar litros recogidos, ingresos y rendimiento operativo.  
- Proporcionar un panel de control intuitivo para el propietario.

---

## 🧩 Módulos del Sistema

### 👥 Clientes ✅ (completo)
Gestión completa de los clientes de la empresa recolectora.

**Funcionalidades:**
- Alta, edición y baja de clientes.  
- Datos de contacto, dirección, precios, frecuencia de recogida.  
- Histórico de recogidas asociadas (modelo preparado para futuras integraciones).  
- Visualización de estadísticas por cliente (litros, ingresos, visitas).  

**Implementación técnica:**
- Backend: modelo `Client`, serializador y `ClientViewSet` con permisos por empresa.  
- Frontend: vista `/clients` con tabla paginada, búsqueda y modales de creación/edición.  
- Integración completa con la API REST mediante **Axios**.

---

### 👷‍♂️ Trabajadores ✅ (completo)
Gestión del personal de la empresa y control de su actividad.

**Funcionalidades:**
- CRUD completo de trabajadores.  
- Datos personales y laborales.  
- Asociación con camiones y rutas.  
- Visualización de rendimiento (litros recogidos, rutas completadas, eficiencia).  

**Implementación técnica:**
- Backend: modelo `Worker`, `WorkerViewSet` y serializer extendido.  
- Frontend: `/workers` con pestañas **Información / Recogidas / Rendimiento**.  
- Incluye paginación, filtros por estado y métricas derivadas (litros/ruta, €/litro).  

---

### 🚛 Camiones ✅ (completo)
Gestión de la flota de vehículos de recogida.

**Funcionalidades:**
- Alta, edición y baja de camiones.  
- Datos técnicos: matrícula, marca, modelo, capacidad, combustible, año.  
- Estado (activo/inactivo).  
- Asignación directa a un conductor (trabajador).  

**Implementación técnica:**
- Backend: modelo `Truck` con `OneToOne` hacia `Worker`.  
- Frontend: `/trucks` con tabla, asignación rápida, filtros y badges de estado.  
- Integración total con el módulo de trabajadores.

---

### 🧭 Dashboard ⚙️ (pendiente)
Será el panel principal del propietario.

**Objetivo:**
Mostrar una visión general del negocio mediante indicadores clave (KPIs):
- Litros recogidos totales.  
- Ingresos generados.  
- Rutas realizadas y pendientes.  
- Estado de flota y trabajadores activos.  

**Implementación prevista:**
- Backend: endpoints `/stats/` con agregaciones sobre `Collection`, `Route`, `Truck`.  
- Frontend: tarjetas y gráficos con **Recharts** y componentes `Card` (Shadcn UI).

---

### 📍 Zonas de Recogida 🕓 (pendiente)
Definición de zonas geográficas para organizar la logística.

**Objetivo:**
Permitir que cada empresa cree sus zonas de recogida mediante polígonos geoespaciales.

**Implementación prevista:**
- Backend: modelo `CollectionZone` con campo `PolygonField` (PostGIS).  
- Frontend: mapa interactivo con **Leaflet** para dibujar zonas.  
- Asociación de clientes y rutas a zonas específicas.

---

### 🗺️ Rutas 🕓 (pendiente)
Planificación y optimización de las rutas de recogida.

**Objetivo:**
Optimizar recorridos diarios en función de los clientes y zonas.

**Funcionalidades previstas:**
- Creación manual o automática de rutas.  
- Asignación de conductor, camión y zona.  
- Estado: pendiente / en curso / completada.  
- Visualización del recorrido optimizado en mapa.  

**Implementación técnica prevista:**
- Backend: modelo `Route` vinculado a `Worker`, `Truck`, `CollectionZone`.  
- Endpoint `/routes/plan/` usando **OSRM** o **Google Directions API**.  
- Frontend: mapa con clientes y orden de paradas optimizado.

---

### 🧾 Recogidas 🕓 (pendiente)
Registro detallado de cada recogida realizada.

**Funcionalidades previstas:**
- Alta manual o automática de recogidas.  
- Datos: cliente, trabajador, litros, fecha y observaciones.  
- Control de estado: pendiente / realizada / cancelada.  

**Implementación técnica prevista:**
- Backend: modelo `Collection` vinculado a `Client`, `Worker`, `Route`.  
- Endpoints `/collections/` y `/collections/worker/:id`.  
- Frontend: vista con tabla y filtros por cliente, fecha y estado.

---

### 📊 Estadísticas 🕓 (pendiente)
Módulo analítico para visualizar métricas y evolución del negocio.

**Indicadores previstos:**
- Litros recogidos por periodo, trabajador o cliente.  
- Ingresos por mes o zona.  
- Costes y eficiencia de rutas.  

**Implementación técnica prevista:**
- Backend: agregaciones SQL o ORM.  
- Frontend: gráficas con **Recharts** y componentes de resumen (KPIs, comparativas).

---

## 🛠️ Tecnologías y Arquitectura

**Backend**
- Python 3 + Django REST Framework  
- PostgreSQL (con PostGIS para geodatos)  
- Autenticación JWT  
- Docker para entorno y despliegue  

**Frontend**
- React (Vite)  
- TailwindCSS + Shadcn/UI + Lucide React  
- Axios + React Router  
- Componentes reutilizables (`CustomTable`, `StatusBadge`, `Dialog`, etc.)

---

## 🚀 Planificación

| Fase | Módulos | Estado | Fecha Estimada |
|------|----------|--------|----------------|
| 1 | **Clientes**, **Trabajadores**, **Camiones** | ✅ Completados | Octubre 2025 |
| 2 | **Zonas de Recogida**, **Rutas** | ⚙️ En desarrollo | Noviembre 2025 |
| 3 | **Recogidas**, **Estadísticas** | 🕓 Pendientes | Diciembre 2025 |
| 4 | **Dashboard** | 🕓 Pendientes | Enero 2026 |
| 5 | **Aplicación para trabajadores y clientes** | ⏳ Fase futura | 2026 |

---

## 🧭 Fases Futuras

### 👷 Módulo de Trabajadores (App)
- Consultar rutas asignadas.  
- Marcar recogidas como realizadas.  
- Registrar incidencias o notas.  

### 👥 Módulo de Clientes (Portal)
- Solicitar nuevas recogidas.  
- Consultar histórico y litros entregados.  
- Descargar facturas y ver sus estadísticas.  

---

✍️ **Autor:** Guillermo Gómez Romero
🎓 **Trabajo Fin de Grado – Ingeniería Informática**  
🏫 **Universidad de Sevilla**
