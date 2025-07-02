# 🎯 Funcionalidades de Filtrado para el Frontend

## 📋 Resumen Ejecutivo

Este documento detalla todas las funcionalidades de filtrado que debe implementar el frontend para cada tipo de producto turístico. El sistema soporta 4 tipos principales: **Actividades**, **Vuelos**, **Alojamientos** y **Transporte**.

## 🏗️ **ESTRUCTURA GENERAL DE FILTROS**

### **Filtros Comunes a Todos los Productos**
- ✅ **Tipo de producto** (selector)
- ✅ **Búsqueda por texto** (input de texto)
- ✅ **Rango de precios** (slider o inputs)
- ✅ **Ubicación** (selector de destinos)
- ✅ **Fechas** (date pickers)
- ✅ **Proveedor** (selector)
- ✅ **Solo disponibles** (checkbox)
- ✅ **Ordenamiento** (dropdown)

---

## 🎯 **FILTROS ESPECÍFICOS POR TIPO DE PRODUCTO**

### **1. 🏃‍♂️ ACTIVIDADES**

#### **Filtros Básicos**
- ✅ **Nivel de dificultad**
  - Muy Fácil
  - Fácil
  - Medio
  - Difícil
  - Muy Difícil
  - Extremo

- ✅ **Incluye guía**
  - Sí/No (checkbox)

- ✅ **Idioma**
  - Input de texto libre

- ✅ **Duración**
  - Rango de horas (0-24)
  - Slider o inputs numéricos

#### **Filtros de Fechas**
- ✅ **Fecha específica** (date picker)
- ✅ **Hora de inicio** (time picker)

#### **Filtros de Capacidad**
- ✅ **Espacios disponibles**
  - Rango mínimo/máximo
  - Slider o inputs numéricos

#### **Ejemplo de UI**
```json
{
  "filters": {
    "product_type": "activity",
    "search": "excursión montaña",
    "location_id": 1,
    "date_min": "2024-01-01",
    "difficulty_level": "Easy",
    "include_guide": true,
    "duration_min": 2,
    "duration_max": 6,
    "unit_price_max": 150
  }
}
```

---

### **2. ✈️ VUELOS**

#### **Filtros Básicos**
- ✅ **Aerolínea**
  - Input de texto libre
  - Autocompletado sugerido

- ✅ **Clase de vuelo**
  - Basic Economy
  - Economy
  - Premium Economy
  - Business Class
  - First Class

- ✅ **Duración del vuelo**
  - Rango de horas
  - Slider o inputs numéricos

- ✅ **Vuelos directos**
  - Sí/No (checkbox)

#### **Filtros de Fechas**
- ✅ **Fecha de salida** (date picker)
- ✅ **Fecha de llegada** (date picker)

#### **Filtros de Ubicación**
- ✅ **Aeropuerto de origen** (selector)
- ✅ **Aeropuerto de destino** (selector)

#### **Filtros de Capacidad**
- ✅ **Asientos disponibles**
  - Rango mínimo/máximo
  - Slider o inputs numéricos

#### **Ejemplo de UI**
```json
{
  "filters": {
    "product_type": "flight",
    "origin_id": 1,
    "destination_id": 5,
    "date_departure": "2024-06-01",
    "class_flight": "Economy",
    "direct_flight": true,
    "duration_flight_max": 8,
    "unit_price_max": 800
  }
}
```

---

### **3. 🏨 ALOJAMIENTOS**

#### **Filtros Básicos**
- ✅ **Tipo de alojamiento**
  - Hotel
  - Hostel
  - Apartamento
  - Casa
  - Cabaña
  - Resort
  - Bed & Breakfast
  - Villa
  - Camping

- ✅ **Tipo de habitación**
  - Individual
  - Doble
  - Triple
  - Cuádruple
  - Suite
  - Familiar
  - Dormitorio
  - Estudio

#### **Filtros de Fechas**
- ✅ **Fecha de check-in** (date picker)
- ✅ **Fecha de check-out** (date picker)
- ✅ **Estadía mínima** (número de noches)
- ✅ **Estadía máxima** (número de noches)

#### **Filtros de Capacidad**
- ✅ **Número de huéspedes**
  - Rango mínimo/máximo
  - Slider o inputs numéricos

#### **Filtros de Precio**
- ✅ **Precio por noche**
  - Rango mínimo/máximo
  - Slider o inputs numéricos

#### **Filtros de Amenidades**
- ✅ **Amenidades** (checkboxes múltiples)
  - Piscina
  - WiFi
  - Gimnasio
  - Restaurante
  - Spa
  - Estacionamiento
  - Aire acondicionado
  - Balcón
  - Baño privado

#### **Ejemplo de UI**
```json
{
  "filters": {
    "product_type": "lodgment",
    "location_id": 3,
    "lodgment_type": "hotel",
    "date_checkin": "2024-07-01",
    "date_checkout": "2024-07-07",
    "guests_min": 2,
    "nights_min": 3,
    "amenities": ["pool", "wifi", "air_conditioning"],
    "price_per_night_max": 200,
    "room_type": "double"
  }
}
```

---

### **4. 🚌 TRANSPORTE**

#### **Filtros Básicos**
- ✅ **Tipo de transporte**
  - Bus
  - Van
  - Carro privado
  - Shuttle
  - Tren
  - Otro

#### **Filtros de Fechas**
- ✅ **Fecha de salida** (date picker)
- ✅ **Fecha de llegada** (date picker)

#### **Filtros de Ubicación**
- ✅ **Origen** (selector)
- ✅ **Destino** (selector)

#### **Filtros de Capacidad**
- ✅ **Capacidad mínima**
  - Input numérico

#### **Ejemplo de UI**
```json
{
  "filters": {
    "product_type": "transportation",
    "origin_id": 1,
    "destination_id": 2,
    "date_departure": "2024-05-15",
    "transport_type": "bus",
    "capacity_min": 4,
    "unit_price_max": 50
  }
}
```

---

## 🎨 **COMPONENTES DE UI RECOMENDADOS**

### **1. Selector de Tipo de Producto**
```typescript
interface ProductTypeSelector {
  options: [
    { value: "activity", label: "Actividades", icon: "🏃‍♂️" },
    { value: "flight", label: "Vuelos", icon: "✈️" },
    { value: "lodgment", label: "Alojamientos", icon: "🏨" },
    { value: "transportation", label: "Transporte", icon: "🚌" }
  ]
}
```

### **2. Filtros Dinámicos**
```typescript
interface DynamicFilters {
  // Los filtros cambian según el tipo de producto seleccionado
  activity: ActivityFilters;
  flight: FlightFilters;
  lodgment: LodgmentFilters;
  transportation: TransportationFilters;
}
```

### **3. Filtros Avanzados (Colapsables)**
```typescript
interface AdvancedFilters {
  isExpanded: boolean;
  filters: {
    supplier: SupplierSelector;
    rating: RatingFilter;
    promotions: PromotionFilter;
    featured: FeaturedFilter;
  }
}
```

---

## 🔄 **ESTADOS Y COMPORTAMIENTOS**

### **1. Filtros Dinámicos**
- Los filtros específicos aparecen/desaparecen según el tipo de producto
- Validaciones en tiempo real
- Mensajes de error contextuales

### **2. Persistencia de Filtros**
- Guardar filtros en URL (query parameters)
- Restaurar filtros al recargar página
- Historial de búsquedas

### **3. Loading States**
- Skeleton loaders durante la búsqueda
- Indicadores de progreso
- Estados de error

### **4. Resultados en Tiempo Real**
- Búsqueda automática al cambiar filtros
- Debounce para evitar muchas requests
- Paginación infinita o paginada

---

## 📱 **RESPONSIVE DESIGN**

### **Mobile (< 768px)**
- Filtros en drawer/modal
- Filtros apilados verticalmente
- Botones grandes para touch

### **Tablet (768px - 1024px)**
- Filtros en sidebar colapsable
- Grid de 2 columnas para filtros

### **Desktop (> 1024px)**
- Filtros en sidebar fijo
- Grid de 3-4 columnas para filtros
- Hover effects y tooltips

---

## 🎯 **FUNCIONALIDADES AVANZADAS**

### **1. Búsqueda Inteligente**
- Autocompletado de ubicaciones
- Sugerencias de búsqueda
- Búsqueda por voz (futuro)

### **2. Filtros Guardados**
- Guardar combinaciones de filtros
- Compartir filtros por URL
- Filtros favoritos

### **3. Comparación de Productos**
- Comparar hasta 3 productos
- Tabla de comparación
- Exportar comparación

### **4. Notificaciones**
- Alertas de precio
- Nuevos productos disponibles
- Ofertas especiales

---

## 🔧 **INTEGRACIÓN CON API**

### **Endpoint Principal**
```http
GET /api/products/products/
```

### **Parámetros de Filtrado**
```typescript
interface FilterParams {
  // Filtros básicos
  product_type?: string;
  search?: string;
  supplier_id?: number;
  
  // Ubicación
  destination_id?: number;
  origin_id?: number;
  location_id?: number;
  
  // Fechas
  date_min?: string;
  date_max?: string;
  date_checkin?: string;
  date_checkout?: string;
  date_departure?: string;
  date_arrival?: string;
  
  // Precio
  unit_price_min?: number;
  unit_price_max?: number;
  price_per_night_min?: number;
  price_per_night_max?: number;
  
  // Disponibilidad
  available_only?: boolean;
  capacity_min?: number;
  capacity_max?: number;
  available_seats_min?: number;
  available_seats_max?: number;
  
  // Filtros específicos por tipo
  difficulty_level?: string;
  include_guide?: boolean;
  language?: string;
  duration_min?: number;
  duration_max?: number;
  
  airline?: string;
  class_flight?: string;
  duration_flight_min?: number;
  duration_flight_max?: number;
  direct_flight?: boolean;
  
  lodgment_type?: string;
  room_type?: string;
  guests_min?: number;
  guests_max?: number;
  nights_min?: number;
  nights_max?: number;
  amenities?: string[];
  
  transport_type?: string;
  
  // Ordenamiento
  ordering?: string;
}
```

### **Respuesta de la API**
```typescript
interface ProductsResponse {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}
```

---

## 🎨 **EJEMPLOS DE IMPLEMENTACIÓN**

### **React/TypeScript**
```typescript
// Hook personalizado para filtros
const useProductFilters = () => {
  const [filters, setFilters] = useState<FilterParams>({});
  const [results, setResults] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);

  const applyFilters = useCallback(async (newFilters: FilterParams) => {
    setLoading(true);
    try {
      const response = await api.getProducts(newFilters);
      setResults(response.items);
    } catch (error) {
      console.error('Error applying filters:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  return { filters, setFilters, results, loading, applyFilters };
};
```

### **Vue.js**
```vue
<template>
  <div class="product-filters">
    <!-- Selector de tipo -->
    <ProductTypeSelector v-model="filters.product_type" />
    
    <!-- Filtros dinámicos -->
    <ActivityFilters v-if="filters.product_type === 'activity'" v-model="filters" />
    <FlightFilters v-if="filters.product_type === 'flight'" v-model="filters" />
    <LodgmentFilters v-if="filters.product_type === 'lodgment'" v-model="filters" />
    <TransportationFilters v-if="filters.product_type === 'transportation'" v-model="filters" />
    
    <!-- Resultados -->
    <ProductList :products="results" :loading="loading" />
  </div>
</template>
```

---

## 📊 **MÉTRICAS Y ANALYTICS**

### **Eventos a Trackear**
- Cambio de filtros
- Búsquedas realizadas
- Productos vistos
- Conversiones (reservas)

### **KPIs Importantes**
- Tiempo de búsqueda
- Tasa de conversión por filtro
- Filtros más utilizados
- Abandono en búsqueda

---

## 🚀 **ROADMAP FUTURO**

### **Fase 1 (Implementación Básica)**
- ✅ Filtros básicos por tipo
- ✅ Búsqueda por texto
- ✅ Filtros de precio y fechas

### **Fase 2 (Mejoras UX)**
- 🔄 Filtros guardados
- 🔄 Búsqueda inteligente
- 🔄 Comparación de productos

### **Fase 3 (Funcionalidades Avanzadas)**
- 🔄 Búsqueda por voz
- 🔄 IA para recomendaciones
- 🔄 Filtros personalizados

---

## 📝 **CONCLUSIÓN**

El sistema de filtrado está **completamente implementado** en el backend y listo para ser consumido por el frontend. Las funcionalidades cubren todos los casos de uso necesarios para una plataforma turística moderna.

**Prioridades de implementación:**
1. **Alta**: Filtros básicos y específicos por tipo
2. **Media**: Búsqueda avanzada y filtros guardados
3. **Baja**: Funcionalidades avanzadas y AI

**Estado**: ✅ **LISTO PARA DESARROLLO FRONTEND** 